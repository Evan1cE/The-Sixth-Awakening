# The Sixth Awakening — container image
#
# The course requires the game to run in the official image without extra
# packages, and the submission is source code rather than a custom image.
# This Dockerfile therefore only wraps the official environment; it installs
# nothing and changes no configuration.
#
# Build and run:
#     docker build -t sixth-awakening .
#     docker run --rm -it sixth-awakening
#
# If the course image is not available locally, any Python 3 image works,
# because the game uses the standard library only:
#     docker build --build-arg BASE_IMAGE=python:3.12-slim -t sixth-awakening .
#     docker run --rm -it sixth-awakening

ARG BASE_IMAGE=engg1330-project:2026-v03
FROM ${BASE_IMAGE}

WORKDIR /project

# Copy only what the game needs; see .dockerignore
COPY main.py ./
COPY game ./game
COPY tests ./tests
COPY README.md ai_use.md ./

# Unbuffered output so the screen redraws immediately inside the container
ENV PYTHONUNBUFFERED=1

# -it is required when running: the game reads commands from the terminal
CMD ["python3", "-u", "main.py"]
