# SEC-GUY

**SEC-GUY** is a modular data recovery framework designed to assist legitimate data owners and security professionals in restoring access to encrypted backup files and legacy data stores.

> **Disclaimer**: This tool is provided strictly for authorized data recovery purposes by legitimate asset owners or authorized personnel. Unauthorized access to data or systems is strictly illegal.

---

## Overview

SEC-GUY unifies multiple specialized recovery engines into an extensible orchestration environment. It provides structured strategy selection, semantic pattern estimation, and automated verification workflows to recover lost credentials or structural backups.

## Key Features

- **Automated Vector Detection**: Analyzes backup file headers and metadata to determine the optimal recovery workflow.
- **AI-Assisted Candidate Generation**: Utilizes local and cloud LLM backends for contextual and semantic candidate estimation.
- **Extensible Recovery Adapters**: Modular wrappers for standard data validation and recovery tools.
- **Terminal User Interface (TUI)**: Rich dashboard for monitoring job execution, vector confidence scores, and processing logs.
- **Audit Logging & Secure Vaulting**: Structured logging of recovery events and secure temporary vaulting of recovered structures.

---

## Installation

### Prerequisites

- Python 3.10+
- Recommended: `pip` and virtual environment setup

### Setup

```bash
git clone https://github.com/your-username/sec-guy.git
cd sec-guy
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
secguy --help
```

---

## Basic Usage

### Command Line Interface (CLI)

Run health checks or evaluate recovery vectors:

```bash
secguy --analyze --target ./backup.dat
```

### Terminal User Interface (TUI)

Launch the interactive dashboard to manage recovery jobs and monitor candidate estimation in real-time:

```bash
secguy ui --dashboard
```

### Partial Seed Recovery

Recover specific data blocks using a known partial seed or entropy pattern:

```bash
secguy recover --seed "partial_data_string" --input ./encrypted.vault
```

---

## License

Distributed under the terms of the GNU General Public License v3.0 or later (GPL-3.0-or-later). See [LICENSE](LICENSE) for details.
