# PolySaaS (DOSE) is Django — there is no root application image here.
# Build the real app:  docker build -f Dockerfile.django -t polysaas .
# Railway uses Dockerfile.django via railway.toml.
FROM alpine:3.19
RUN echo "ERROR: Refusing to build. Use Dockerfile.django (Django / DOSE), not the repo root Dockerfile." >&2 && exit 1
