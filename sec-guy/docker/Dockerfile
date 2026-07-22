FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV SECGUY_DIR=/opt/sec-guy

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    git curl wget build-essential \
    libssl-dev libffi-dev libpq-dev pkg-config cmake \
    hashcat hashcat-utils john \
    fprintd libfprint-2-2 \
    redis-server \
    age age-keygen \
    sqlite3 jq \
    podman \
    neofetch htop tmux tree \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -s /bin/bash -G video,render secguy

# Copy project
COPY --chown=secguy:secguy . $SECGUY_DIR
WORKDIR $SECGUY_DIR

# Setup Python environment
RUN python3.11 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Make scripts executable
RUN chmod +x scripts/install.sh tools/exodus2hashcat.py tools/cupp.py

# Vault tmpfs
RUN mkdir -p /dev/shm/secguy-vault && \
    chown secguy:secguy /dev/shm/secguy-vault

USER secguy
EXPOSE 8080 8081 52415

CMD ["python3", "-m", "secguy.main"]
