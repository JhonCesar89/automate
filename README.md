# Network Migration Automation

Automation tools for PEI → AGGI network migration at Claro Argentina.

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USER/network-migration-automation.git
cd network-migration-automation
```

### 2. Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Credentials

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
notepad .env  # Windows
nano .env     # Linux
```

### 5. Test WID Connection

```bash
# Test connection only
python test_wid_collector.py

# Test with a specific service
python test_wid_collector.py 14815103
```

## Project Structure

```
network-migration-automation/
├── src/
│   ├── collectors/          # Data collection from systems
│   │   ├── base.py          # Base collector class
│   │   ├── wid_collector.py # WID scraper
│   │   ├── sap_collector.py # SAP (TODO)
│   │   └── jarvis_collector.py # Jarvis API (TODO)
│   ├── processors/          # Data normalization & comparison
│   ├── reporters/           # Output generation
│   └── config/              # Settings management
├── tests/                   # Unit tests
├── data/
│   ├── raw/                 # Raw data from systems
│   └── processed/           # Normalized data
├── docs/                    # Documentation
├── requirements.txt
├── .env.example
└── README.md
```

## Usage

### Collect Single Service from WID

```python
from src.collectors import WIDCollector

with WIDCollector() as wid:
    service = wid.search_by_service("14815103")
    print(f"Ring: {service.ring_name}")
    print(f"VLAN: {service.bvi_vlan}")
```

### Collect All Services in Ring (TODO)

```python
from src.collectors import WIDCollector

with WIDCollector() as wid:
    services = wid.search_by_ring("ME-BHBA_0015")
    for svc in services:
        print(f"{svc.service_id}: {svc.client_name}")
```

## Configuration

Environment variables in `.env`:

| Variable | Description |
|----------|-------------|
| `WID_BASE_URL` | WID web interface URL |
| `WID_USERNAME` | Your WID username |
| `WID_PASSWORD` | Your WID password |
| `HEADLESS_BROWSER` | Run browser in background (true/false) |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) |

## Development Status

- [x] Project structure
- [x] WID Collector (basic)
- [ ] WID Collector (ring search)
- [ ] SAP Collector
- [ ] Jarvis Collector
- [ ] Flowone Collector
- [ ] Data normalizer
- [ ] Discrepancy detector
- [ ] Report generator

## License

Internal use only - Claro Argentina
