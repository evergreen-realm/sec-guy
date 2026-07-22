#!/bin/bash
# SEC-GUY v3.1 Automated Installer
# Supports: Ubuntu 22.04/24.04, Debian 12
# Hardware: T490 (8GB) + Production Machine (40GB+4GB GPU)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SECGUY_USER="${SECGUY_USER:-secguy}"
SECGUY_DIR="${SECGUY_DIR:-/opt/sec-guy}"
PROD_IP="${PROD_IP:-}"
PYTHON_VERSION="3.11"

log() { echo -e "${GREEN}[INSTALL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# ============================================
# PHASE 0: Pre-flight Checks
# ============================================
log "Starting SEC-GUY v3.1 installation..."

if [[ $EUID -ne 0 ]]; then
   error "This installer must be run as root (use sudo)"
fi

# Detect hardware profile
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
HAS_GPU=$(lspci 2>/dev/null | grep -i nvidia | wc -l)

if [[ $TOTAL_RAM -lt 6144 ]]; then
    warn "Low RAM detected (${TOTAL_RAM}MB). T490 profile recommended."
fi

if [[ $HAS_GPU -gt 0 ]]; then
    log "NVIDIA GPU detected — Production Machine profile"
    MACHINE_TYPE="production"
else
    log "No GPU detected — T490 profile"
    MACHINE_TYPE="t490"
fi

# ============================================
# PHASE 1: System Dependencies
# ============================================
log "Phase 1: Installing system dependencies..."

apt-get update
apt-get install -y \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev \
    python3-pip git curl wget build-essential \
    libssl-dev libffi-dev libpq-dev pkg-config cmake \
    hashcat hashcat-utils john \
    fprintd libfprint-2-2 libpam-fprintd \
    redis-server \
    age age-keygen \
    sqlite3 jq \
    podman podman-compose \
    rustc cargo \
    libopenblas-dev libomp-dev \
    clinfo ocl-icd-libopencl1 pocl-opencl-icd \
    neofetch htop tmux tree \
    libz-dev libbz2-dev libreadline-dev \
    libncursesw5-dev libsqlite3-dev tk-dev \
    libgdbm-dev libc6-dev libczmq-dev

# ============================================
# PHASE 2: Create User & Directories
# ============================================
log "Phase 2: Creating user and directory structure..."

if ! id "$SECGUY_USER" &>/dev/null; then
    useradd -m -s /bin/bash -G video,render "$SECGUY_USER"
    log "Created user: $SECGUY_USER"
fi

mkdir -p "$SECGUY_DIR"/{src,models,data,config,logs,enrichment_data,docs,scripts,tools,wordlists,tests/fixtures/test_wallets}
mkdir -p "$SECGUY_DIR/src"/{core,agents,recovery,guardian,vault,learning,llm,ui,monitoring}
mkdir -p "$SECGUY_DIR/src/agents/prompt_templates"
mkdir -p "$SECGUY_DIR/src/guardian/src"
mkdir -p "$SECGUY_DIR/src/recovery"/{password,seed,zero_hint,online_enrichment,corruption,twofa}
mkdir -p "$SECGUY_DIR/src/vault/src"
mkdir -p "$SECGUY_DIR/src/llm"
mkdir -p "$SECGUY_DIR/src/learning"
mkdir -p "$SECGUY_DIR/src/ui"
mkdir -p "$SECGUY_DIR/src/monitoring"
mkdir -p "$SECGUY_DIR/data"/{wordlists,breach_db,trends}

chown -R "$SECGUY_USER:$SECGUY_USER" "$SECGUY_DIR"
chmod 700 "$SECGUY_DIR"
chmod 700 "$SECGUY_DIR/data"
chmod 700 "$SECGUY_DIR/enrichment_data"

# ============================================
# PHASE 3: Python Environment
# ============================================
log "Phase 3: Setting up Python environment..."

sudo -u "$SECGUY_USER" -H bash -c "
cd $SECGUY_DIR
python${PYTHON_VERSION} -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# Core dependencies
pip install \
    letta neo4j py2neo \
    pydantic jinja2 rich typer click \
    requests pyyaml psutil \
    cryptography mnemonic base58 ecdsa pysha3 scrypt pycryptodome \
    argon2-cffi prometheus-client \
    pytest pytest-asyncio ruff mypy bandit \
    json-repair pwnedpasswords pyhibp \
    textual

# ML/LLM dependencies
pip install \
    torch --index-url https://download.pytorch.org/whl/cpu \
    transformers datasets accelerate bitsandbytes peft trl \
    unsloth

# Cloud AI
pip install openai

# EXO distributed inference
pip install exo

# Monitoring
pip install pyzmq redis
"

# ============================================
# PHASE 4: Security Hardening
# ============================================
log "Phase 4: Security hardening..."

# Disable swap
swapoff -a
sed -i '/swap/d' /etc/fstab
rm -f /swapfile

# Mount tmpfs vault
mkdir -p /dev/shm/secguy-vault
mount -t tmpfs -o size=100M,mode=700,uid=$(id -u "$SECGUY_USER"),gid=$(id -g "$SECGUY_USER") tmpfs /dev/shm/secguy-vault

# Make permanent
echo "tmpfs /dev/shm/secguy-vault tmpfs size=100M,mode=700,uid=$(id -u $SECGUY_USER),gid=$(id -g $SECGUY_USER) 0 0" >> /etc/fstab

# ============================================
# PHASE 5: Install External Tools
# ============================================
log "Phase 5: Installing external tools..."

# BTCRecover
sudo -u "$SECGUY_USER" -H bash -c "
cd $SECGUY_DIR/tools
git clone https://github.com/3rdIteration/btcrecover.git
cd btcrecover
pip install -r requirements-full.txt
"

# exodus2hashcat.py
wget -q https://raw.githubusercontent.com/hashcat/hashcat/master/tools/exodus2hashcat.py -O "$SECGUY_DIR/tools/exodus2hashcat.py"
chmod +x "$SECGUY_DIR/tools/exodus2hashcat.py"

# CUPP
wget -q https://raw.githubusercontent.com/Mebus/cupp/master/cupp.py -O "$SECGUY_DIR/tools/cupp.py"
chmod +x "$SECGUY_DIR/tools/cupp.py"

# CeWL (Ruby tool)
apt-get install -y ruby ruby-dev
sudo -u "$SECGUY_USER" -H bash -c "
gem install --user-install cewl
"

# ============================================
# PHASE 6: Download Models (conditional)
# ============================================
log "Phase 6: Downloading LLM models..."

if [[ "$MACHINE_TYPE" == "t490" ]]; then
    log "Downloading lightweight models for T490..."
    sudo -u "$SECGUY_USER" -H bash -c "
cd $SECGUY_DIR/models
wget -q https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf \
    -O qwen2.5-coder-1.5b-q4_k_m.gguf
"
    info "Skipped 32B model — install on Production Machine"

elif [[ "$MACHINE_TYPE" == "production" ]]; then
    log "Downloading full models for Production Machine..."
    sudo -u "$SECGUY_USER" -H bash -c "
cd $SECGUY_DIR/models
wget -q https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf \
    -O qwen2.5-coder-1.5b-q4_k_m.gguf
wget -q https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF/resolve/main/qwen2.5-coder-32b-instruct-q4_k_m.gguf \
    -O qwen2.5-coder-32b-q4_k_m.gguf
"
fi

# ============================================
# PHASE 7: Services
# ============================================
log "Phase 7: Configuring services..."

# Redis
systemctl enable redis-server
systemctl start redis-server

# Neo4j (Podman)
podman pull neo4j:5.19-community
podman run -d \
    --name secguy-neo4j \
    --restart unless-stopped \
    -p 127.0.0.1:7474:7474 \
    -p 127.0.0.1:7687:7687 \
    -v "$SECGUY_DIR/data/neo4j:/data" \
    -e NEO4J_AUTH=neo4j/secguy_neo4j_2025 \
    neo4j:5.19-community

# ============================================
# PHASE 8: Configuration
# ============================================
log "Phase 8: Writing configuration..."

cat > "$SECGUY_DIR/config/secguy.yaml" << 'EOF'
secguy:
  version: "3.1.0"

  hardware:
    primary_machine: "t490"
    total_ram_mb: 8192
    available_ram_mb: 6144
    exo_cluster: true
    exo_peers:
      - "t490-primary.local:52415"
      - "prod-heavy.local:52415"

  llm:
    orchestrator_model: "Qwen2.5-Coder-32B-Q4_K_M"
    semantic_model: "Qwen2.5-Coder-8B-Q4_K_M"
    draft_model: "Qwen2.5-Coder-1.5B-Q4_K_M"
    lmstudio_url: "http://localhost:1234/v1"
    speculative_decoding: true
    model_paths:
      2b: "/opt/sec-guy/models/qwen2.5-coder-1.5b-q4_k_m.gguf"
      32b: "/opt/sec-guy/models/qwen2.5-coder-32b-q4_k_m.gguf"

  recovery:
    max_concurrent_jobs: 5
    max_entropy_bits: 80
    default_timeout_minutes: 240
    hashcat_mode: 28200
    john_fallback: true
    checkpoint_interval: 1000
    confidence_target: 30.0

  security:
    biometric_required: true
    ownership_proof_required: false
    time_delay_default: "5m"
    vault_ttl_seconds: 300
    swap_disabled: true
    firejail_enabled: true
    audit_log_mandatory: true
    legal_disclaimer_required: true

  vault:
    mount_point: "/dev/shm/secguy-vault"
    max_size_mb: 100
    encryption: "age"
    time_lock: "argon2id"
    auto_shred: true

  learning:
    neo4j_uri: "bolt://localhost:7687"
    neo4j_auth: ["neo4j", "secguy_neo4j_2025"]
    graphiti_enabled: true
    pattern_anonymization: true

  online_enrichment:
    enabled: true
    enable_runtime_queries: false
    data_dir: "/opt/sec-guy/enrichment_data"
    api_keys:
      groq: ""
      cerebras: ""
      sambanova: ""
      openrouter: ""
      google: ""
      dehashed: ""

  monitoring:
    prometheus_enabled: true
    prometheus_port: 8080
    grafana_enabled: true
    bugsink_enabled: true
    audit_log_enabled: true
EOF

chown "$SECGUY_USER:$SECGUY_USER" "$SECGUY_DIR/config/secguy.yaml"
chmod 600 "$SECGUY_DIR/config/secguy.yaml"

# ============================================
# PHASE 9: Online Enrichment Setup
# ============================================
log "Phase 9: Running online enrichment setup..."

sudo -u "$SECGUY_USER" -H bash -c "
cd $SECGUY_DIR
source venv/bin/activate
python3 src/recovery/online_enrichment/online_enrichment.py setup || true
"

# ============================================
# PHASE 10: Verification
# ============================================
log "Phase 10: Verification..."

# Check critical tools
for tool in hashcat john redis-cli podman age; do
    if command -v "$tool" &> /dev/null; then
        log "$tool: OK"
    else
        warn "$tool: NOT FOUND"
    fi
done

# Check Python packages
sudo -u "$SECGUY_USER" -H bash -c "
cd $SECGUY_DIR
source venv/bin/activate
python3 -c 'import letta, neo4j, rich, torch, transformers, openai; print("All Python packages OK")'
" || warn "Some Python packages missing"

# Check tmpfs vault
if mountpoint -q /dev/shm/secguy-vault; then
    log "RAM vault: MOUNTED"
else
    warn "RAM vault: NOT MOUNTED"
fi

# ============================================
# COMPLETION
# ============================================
log "============================================"
log "SEC-GUY v3.1 Installation Complete!"
log "============================================"
log "Installation directory: $SECGUY_DIR"
log "User: $SECGUY_USER"
log "Machine type: $MACHINE_TYPE"
log ""
log "Next steps:"
log "1. Configure API keys in $SECGUY_DIR/config/secguy.yaml"
log "2. Enroll biometric: fprintd-enroll (as $SECGUY_USER)"
log "3. On Production Machine: Start EXO with: exo --node-id prod-heavy --listen 0.0.0.0:52415"
log "4. On T490: Start EXO with: exo --node-id t490-primary --peer prod-heavy.local:52415"
log "5. Start recovery: sudo -u $SECGUY_USER python3 -m secguy.main"
log ""
log "For TUI mode: sudo -u $SECGUY_USER python3 -m secguy.ui.tui"
log "============================================"
