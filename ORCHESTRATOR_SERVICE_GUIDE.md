# Motadata Orchestrator Service Guide

## Overview

The Motadata AI Services Orchestrator is now managed as a systemd service, allowing automatic startup on boot and easy management via `systemctl` commands.

## Service Details

- **Service Name**: `motadata-orchestrator`
- **Service File**: `/etc/systemd/system/motadata-orchestrator.service`
- **Script**: `/home/harshil/Harshil-PoCs/rag/scripts/orchestrator_unified.sh`
- **User**: `harshil` (with passwordless sudo access via sudoers)
- **Auto-start**: Enabled (starts automatically on system boot)

## Common Commands

### Start the service
```bash
sudo systemctl start motadata-orchestrator
```

### Stop the service
```bash
sudo systemctl stop motadata-orchestrator
```

### Restart the service
```bash
sudo systemctl restart motadata-orchestrator
```

### Check service status
```bash
sudo systemctl status motadata-orchestrator
```

### View service logs
```bash
journalctl -u motadata-orchestrator -f
```

### View last 50 lines of logs
```bash
journalctl -u motadata-orchestrator -n 50
```

### View logs from the last hour
```bash
journalctl -u motadata-orchestrator --since "1 hour ago"
```

### View logs with timestamps
```bash
journalctl -u motadata-orchestrator -o short-iso
```

## Viewing Logs for Each Endpoint

### Systemd Journal (All Services Combined)
```bash
# Follow all orchestrator logs in real-time
journalctl -u motadata-orchestrator -f

# View logs with more context
journalctl -xeu motadata-orchestrator.service
```

### Individual Service Logs

#### vLLM (Model Server - Port 8000)
```bash
# View vLLM logs from systemd journal
journalctl -u motadata-orchestrator -f | grep -i vllm

# Or check the service logs directly
tail -f rag/logs/vllm.log
```

#### RAG API (Application API - Port 8081)
```bash
# View RAG API logs from systemd journal
journalctl -u motadata-orchestrator -f | grep -i "rag\|api"

# Or check the service logs directly
tail -f rag/logs/rag_api.log
```

#### Qdrant (Vector Database - Port 6333)
```bash
# View Qdrant Docker logs
docker logs qdrant-motadata -f

# Or check recent logs
docker logs qdrant-motadata --tail 50
```

#### Neo4j (Graph Database - Port 7474)
```bash
# View Neo4j Docker logs
docker logs neo4j-motadata -f

# Or check recent logs
docker logs neo4j-motadata --tail 50
```

#### Health Monitor
```bash
# View health monitor logs
journalctl -u motadata-orchestrator -f | grep -i "health\|monitor"

# Or check the service logs directly
tail -f rag/logs/monitor.log
```

### Log Filtering Examples

```bash
# View only errors
journalctl -u motadata-orchestrator -p err

# View only warnings and errors
journalctl -u motadata-orchestrator -p warning

# View logs for a specific time range
journalctl -u motadata-orchestrator --since "2026-01-05 07:00:00" --until "2026-01-05 08:00:00"

# View logs and follow new entries
journalctl -u motadata-orchestrator -f

# View logs with full details
journalctl -u motadata-orchestrator -o verbose
```

## Service Components

The orchestrator manages the following services:

1. **Qdrant** (Vector Database) - Port 6333
2. **Neo4j** (Graph Database) - Port 7474
3. **vLLM** (Model Server) - Port 8000
4. **RAG API** (Application API) - Port 8081

## Health Checks

### Check vLLM model availability
```bash
curl -s http://localhost:8000/v1/models | python3 -m json.tool
```

### Check RAG API health
```bash
curl -s http://localhost:8081/health | python3 -m json.tool
```

## Authentication

The service uses passwordless sudo authentication configured in:
```
/etc/sudoers.d/motadata-orchestrator
```

This allows the `harshil` user to run docker-compose commands without entering a password.

## Troubleshooting

### Service fails to start
Check the logs:
```bash
journalctl -xeu motadata-orchestrator.service
```

### Services not starting
Verify Docker is running:
```bash
sudo systemctl status docker
```

### Port conflicts
Check which process is using a port:
```bash
sudo lsof -i :8000  # for vLLM
sudo lsof -i :8081  # for RAG API
```

## Auto-start on Boot

The service is enabled for auto-start. To verify:
```bash
sudo systemctl is-enabled motadata-orchestrator
```

To disable auto-start:
```bash
sudo systemctl disable motadata-orchestrator
```

To re-enable auto-start:
```bash
sudo systemctl enable motadata-orchestrator
```

