# Same Odoo-on-PaaS pattern as deploy/odoo. Use this Dockerfile on Railway so the
# service does not rely on Nixpacks + pip install from git (slow / brittle).
FROM odoo:18

USER root
COPY entrypoint-hosted.sh /usr/local/bin/entrypoint-hosted.sh
RUN chmod +x /usr/local/bin/entrypoint-hosted.sh
USER odoo

EXPOSE 8069

ENTRYPOINT ["/usr/local/bin/entrypoint-hosted.sh"]
