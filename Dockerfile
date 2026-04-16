FROM debian:bullseye-slim

# Flutter Development Container
# Purpose: Creates isolated Flutter dev environments spawned by Python backend
# Usage: Python backend creates containers from this image for user sessions

# Install dependencies for Flutter development server including git
RUN apt-get update && apt-get install -y \
  curl git unzip ca-certificates bash \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean

# Configure git globally for the container
RUN git config --global init.defaultBranch main \
  && git config --global user.name "FlutterAI" \
  && git config --global user.email "ai@flutterai.dev" \
  && git config --global safe.directory '*'

# Install Flutter with specific version for reproducibility
ENV FLUTTER_VERSION=3.16.0
RUN git clone https://github.com/flutter/flutter.git /opt/flutter \
  --depth 1 -b ${FLUTTER_VERSION} \
  && /opt/flutter/bin/flutter config --no-analytics \
  && /opt/flutter/bin/flutter config --enable-web \
  && /opt/flutter/bin/flutter precache --web

ENV PATH="/opt/flutter/bin:${PATH}"

WORKDIR /app

# Expose the dev server port range (8081-8200 for multiple sessions)
EXPOSE 8081-8200

# Default command - will be overridden with specific port
CMD ["flutter", "run", "-d", "web-server", "--web-hostname", "0.0.0.0", "--hot"]