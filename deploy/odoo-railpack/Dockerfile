# Same Odoo-on-PaaS pattern as deploy/odoo-render (Render). Use this Dockerfile on Railway so the
# service does not rely on Nixpacks + pip install from git (slow / brittle).
FROM odoo:18

USER root
COPY entrypoint-render.sh /usr/local/bin/entrypoint-render.sh
RUN chmod +x /usr/local/bin/entrypoint-render.sh
USER odoo

EXPOSE 8069

ENTRYPOINT ["/usr/local/bin/entrypoint-render.sh"]
