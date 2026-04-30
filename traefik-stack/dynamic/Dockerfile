FROM traefik:v3.1

# Copy config files
COPY traefik.yml /etc/traefik/traefik.yml
COPY dynamic/ /etc/traefik/dynamic/

# Expose ports
EXPOSE 80
EXPOSE 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/ping || exit 1