// ChatKeeper Plugin Webapp Entry Point

import React from 'react';
import {render} from 'react-dom';
import ChatKeeperDashboard from './components/ChatKeeperDashboard';
import './styles.css';

const PluginId = 'com.polysaas.chatkeeper';

class Plugin {
    initialize(registry, store) {
        // Register the ChatKeeper icon in the channel header
        registry.registerChannelHeaderButtonAction(
            // Icon
            <i className="icon fa fa-archive" aria-hidden="true" />,
            // Action when clicked
            (channel) => {
                this.showDashboard(channel.id);
            },
            // Tooltip
            'ChatKeeper - Conversation Analytics & Backup'
        );

        // Register slash command handler
        registry.registerSlashCommandWillBePostedHook(this.slashCommandHandler.bind(this));

        // Register main dashboard route
        registry.registerCustomRoute('/chatkeeper', ChatKeeperDashboard);

        console.log('[ChatKeeper] Plugin initialized');
    }

    slashCommandHandler(message, args) {
        if (message.startsWith('/chatkeeper')) {
            const parts = message.split(' ');
            const command = parts[1];

            switch (command) {
                case 'export':
                    return this.handleExportCommand(parts, args);
                case 'backup':
                    return this.handleBackupCommand(args);
                case 'stats':
                    return this.handleStatsCommand(args);
                case 'search':
                    return this.handleSearchCommand(parts, args);
                case 'tag':
                    return this.handleTagCommand(parts, args);
                default:
                    return {
                        message: 'Available commands: export, backup, stats, search, tag',
                        args
                    };
            }
        }
        return {message, args};
    }

    handleExportCommand(parts, args) {
        const format = parts[2] || 'json';
        const channelId = args.channel_id;
        
        // Trigger export via API
        this.triggerExport(channelId, format);
        
        return {
            message: `Exporting conversation as ${format}...`,
            args
        };
    }

    handleBackupCommand(args) {
        this.triggerBackup();
        return {
            message: 'Starting cloud backup...',
            args
        };
    }

    handleStatsCommand(args) {
        this.showDashboard(args.channel_id);
        return {
            message: '',
            args
        };
    }

    handleSearchCommand(parts, args) {
        const query = parts.slice(2).join(' ');
        if (!query) {
            return {
                message: 'Usage: /chatkeeper search <query>',
                args
            };
        }
        
        this.showSearchResults(query, args.channel_id);
        
        return {
            message: `Searching for "${query}"...`,
            args
        };
    }

    handleTagCommand(parts, args) {
        const tag = parts[2];
        if (!tag) {
            return {
                message: 'Usage: /chatkeeper tag <category>',
                args
            };
        }
        
        this.addTag(args.channel_id, tag);
        
        return {
            message: `Tagged channel with: ${tag}`,
            args
        };
    }

    showDashboard(channelId = '') {
        const basePath = window.basename || '';
        const url = `${basePath}/plugins/${PluginId}/dashboard`;
        window.open(url, '_blank');
    }

    async triggerExport(channelId, format) {
        try {
            const response = await fetch(`/plugins/${PluginId}/api/v1/export`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    channel_id: channelId,
                    format: format,
                    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
                    end_date: new Date().toISOString()
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = response.headers.get('content-disposition')?.split('filename=')[1] || `export.${format}`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('[ChatKeeper] Export failed:', error);
        }
    }

    async triggerBackup() {
        try {
            const response = await fetch(`/plugins/${PluginId}/api/v1/backup`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[ChatKeeper] Backup completed:', data);
            }
        } catch (error) {
            console.error('[ChatKeeper] Backup failed:', error);
        }
    }

    async addTag(channelId, tag) {
        try {
            await fetch(`/plugins/${PluginId}/api/v1/tags`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    channel_id: channelId,
                    tag: tag
                })
            });
        } catch (error) {
            console.error('[ChatKeeper] Tag failed:', error);
        }
    }

    async showSearchResults(query, channelId) {
        // Open dashboard with search query
        this.showDashboard(channelId);
    }
}

window.registerPlugin(PluginId, new Plugin());
