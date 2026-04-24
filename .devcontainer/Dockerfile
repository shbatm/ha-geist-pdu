ARG VARIANT="debian"
FROM mcr.microsoft.com/vscode/devcontainers/base:${VARIANT}

# Install system packages needed for building Python packages and Home Assistant tests
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      python3-dev \
      python3-venv \
      python3-pip \
      python3-setuptools \
      python3-full \
      git \
      curl \
      jq \
      ca-certificates \
      libssl-dev \
      libffi-dev \
      libjpeg-dev \
      zlib1g-dev \
      pkg-config \
      cargo \
    && rm -rf /var/lib/apt/lists/*

# Create a venv for the workspace during image build so pip is available
RUN mkdir -p /workspaces/ha-geist-pdu \
  && python3 -m venv /workspaces/ha-geist-pdu/.venv \
  && /workspaces/ha-geist-pdu/.venv/bin/python -m pip install -U pip setuptools wheel || true

# Also create a prebuilt venv in /opt/venv to copy into the workspace at runtime
RUN python3 -m venv /opt/venv \
  && /opt/venv/bin/python -m pip install -U pip setuptools wheel || true

# Make sure the venvs are writable by the non-root 'vscode' user
RUN chown -R vscode:vscode /opt/venv /workspaces/ha-geist-pdu/.venv || true
