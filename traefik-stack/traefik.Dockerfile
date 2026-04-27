FROM traefik:v3.0

# Create directory for Let's Encrypt certificates
RUN mkdir -p /letsencrypt

# Copy Traefik configuration
COPY traefik.yml /etc/traefik/traefik.yml

# Expose ports
EXPOSE 80 443 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ping || exit 1
