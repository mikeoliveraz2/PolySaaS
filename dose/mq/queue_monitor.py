"""
MQ Queue Monitor - Background service that monitors message queues
and routes messages through the MQ controllers
"""
import logging
import threading
import time
from django.db import connection
from dose.models.mq_config import MQConfig
from dose.utils import get_current_tenant
from dose.mq.mq_request_controller import MQRequestController
from dose.mq.mq_response_controller import MQResponseController

logger = logging.getLogger(__name__)


class MQQueueMonitor:
    """
    Monitors message queues and processes incoming messages.
    Runs as a background thread/service.
    """

    def __init__(self):
        self.running = False
        self.threads = {}
        self.adapters = {}
        logger.info("MQQueueMonitor initialized")

    def start(self):
        """Start monitoring all active MQ configurations."""
        if self.running:
            logger.warning("MQQueueMonitor is already running")
            return

        self.running = True
        logger.info("Starting MQQueueMonitor...")

        # Load all active MQ configurations
        try:
            # Reset to public schema to query MQConfig
            connection.cursor().execute("SET search_path TO public;")
            active_configs = MQConfig.objects.filter(is_active=True)
            logger.info(f"Found {active_configs.count()} active MQ configurations")

            for mq_config in active_configs:
                self._start_monitor_for_config(mq_config)

        except Exception as e:
            logger.error(f"Error starting MQQueueMonitor: {e}")
            self.running = False

    def stop(self):
        """Stop monitoring all queues."""
        logger.info("Stopping MQQueueMonitor...")
        self.running = False

        # Stop all adapter connections
        for adapter in self.adapters.values():
            try:
                adapter.close()
            except Exception as e:
                logger.error(f"Error closing adapter: {e}")

        # Wait for threads to finish
        for thread in self.threads.values():
            thread.join(timeout=5)

        self.threads.clear()
        self.adapters.clear()
        logger.info("MQQueueMonitor stopped")

    def _start_monitor_for_config(self, mq_config):
        """Start monitoring a specific MQ configuration."""
        config_id = str(mq_config.id)

        try:
            # Create adapter based on provider
            if mq_config.provider == 'rabbitmq':
                from dose.mq.adapters.rabbitmq_adapter import RabbitMQAdapter
                adapter = RabbitMQAdapter(mq_config)
            elif mq_config.provider == 'google_pubsub':
                from dose.mq.adapters.pubsub_adapter import PubSubAdapter
                adapter = PubSubAdapter(mq_config)
            else:
                logger.warning(f"Unsupported provider: {mq_config.provider}")
                return

            self.adapters[config_id] = adapter

            # Start monitoring thread
            thread = threading.Thread(
                target=self._monitor_queue,
                args=(mq_config, adapter),
                daemon=True,
                name=f"MQMonitor-{mq_config.name}"
            )
            thread.start()
            self.threads[config_id] = thread
            logger.info(f"Started monitoring for {mq_config.name} ({mq_config.provider})")

        except Exception as e:
            logger.error(f"Error starting monitor for {mq_config.name}: {e}")

    def _monitor_queue(self, mq_config, adapter):
        """Monitor a queue and process messages."""
        logger.info(f"Monitoring queue: {mq_config.name} ({mq_config.provider})")

        while self.running:
            try:
                # Set tenant schema for this request
                if mq_config.tenant and mq_config.tenant.schema_name:
                    connection.cursor().execute(f"SET search_path TO {mq_config.tenant.schema_name},public;")

                # Consume message from queue
                message = adapter.consume(timeout=5)  # 5 second timeout

                if message:
                    logger.info(f"Received message from {mq_config.name}: {message.get('routing_key') or message.get('topic')}")

                    # Process message through MQRequestController
                    routing_key = message.get('routing_key') or message.get('topic', '')
                    message_data = message.get('data') or message.get('body', {})

                    result = MQRequestController.process_mq_message(
                        message_data=message_data,
                        routing_key=routing_key,
                        topic=routing_key,
                        mq_config=mq_config,
                        tenant=mq_config.tenant
                    )

                    logger.info(f"Message processed: {result.get('success', False)}")

                    # If response processing is needed, process through MQResponseController
                    if result.get('success') and mq_config.response_queue_enabled:
                        requestpath = result.get('requestpath', f"/mq/{routing_key}")
                        response_result = MQResponseController.process_mq_response(
                            response_data=result,
                            requestpath=requestpath,
                            mq_config=mq_config,
                            tenant=mq_config.tenant
                        )
                        logger.info(f"Response processed: {response_result.get('success', False)}")

                else:
                    # No message, continue polling
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in monitor thread for {mq_config.name}: {e}")
                time.sleep(5)  # Wait before retrying

    def reload_configs(self):
        """Reload MQ configurations (useful for dynamic updates)."""
        logger.info("Reloading MQ configurations...")

        # Stop existing monitors
        for config_id in list(self.threads.keys()):
            if config_id in self.adapters:
                try:
                    self.adapters[config_id].close()
                except:
                    pass
            if config_id in self.threads:
                self.threads[config_id].join(timeout=2)

        self.threads.clear()
        self.adapters.clear()

        # Restart with new configs
        if self.running:
            self.start()


# Global monitor instance
_monitor_instance = None


def get_mq_monitor():
    """Get or create the global MQ monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = MQQueueMonitor()
    return _monitor_instance


def start_mq_monitor():
    """Start the MQ monitor (called from Django management command or startup)."""
    monitor = get_mq_monitor()
    monitor.start()
    return monitor


def stop_mq_monitor():
    """Stop the MQ monitor."""
    global _monitor_instance
    if _monitor_instance:
        _monitor_instance.stop()

