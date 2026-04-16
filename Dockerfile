# PolySaaS (DOSE) is Django. The production image is defined in Dockerfile.django.
#
# Render: set the service "Dockerfile Path" to Dockerfile.django (not this file).
# Local:  docker build -f Dockerfile.django -t polysaas .
FROM alpine:3.19
RUN echo "ERROR: Use Dockerfile.django for the Django/Gunicorn image. On Render, set Dockerfile Path to Dockerfile.django." >&2 && exit 1
