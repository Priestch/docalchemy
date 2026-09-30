# Pack Workers with Docker Providers

This guide explains how to run pack workers that connect to dockerized provider services.

## Architecture

- **Providers**: Run as Docker containers (docling, mineru, opendataloader, franken_ocr)
- **Workers**: Run as Celery workers in the main application environment
- **Communication**: Workers connect to providers via HTTP and shared storage

## Quick Start

### 1. Start Docker Providers

From the `docalchemy` repository:

```bash
cd ~/Enter/docalchemy
docker compose up -d
```

Check status:
```bash
docker ps --filter "name=docalchemy-provider"
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and ensure these are set:

```bash
# Storage path mapping (host -> container)
STORAGE_HOST_ROOT=/home/gaopeng/localstorage/docalchemy
STORAGE_PROVIDER_ROOT=/storage
```

**Important**: `STORAGE_HOST_ROOT` must match the host path mounted at `/storage` in the docalchemy repo's `docker-compose.yml` (`STORAGE_PATH` variable):
```yaml
volumes:
  - /home/gaopeng/localstorage/docalchemy:/storage
```

### 3. Start Pack Workers

```bash
make dev-workers
```

This starts 4 workers, one for each provider. Logs are saved to `logs/worker_*.log`.

View logs:
```bash
tail -f logs/worker_docling.log
```

Stop workers:
```bash
pkill -f 'celery.*pack_worker'
```

## How Path Mapping Works

### The Problem
Docker containers see a different filesystem than the host:
- Host path: `/home/gaopeng/localstorage/docalchemy/4b/file.pdf`
- Container path: `/storage/4b/file.pdf`

### The Solution
PackAdapter automatically detects path mapping from environment variables:
1. Worker sets `STORAGE_HOST_ROOT` and `STORAGE_PROVIDER_ROOT`
2. PackAdapter reads these on initialization
3. Paths are automatically translated when sending to providers

```python
# Old way (manual)
adapter = PackAdapter(
    storage=storage,
    provider_url='http://localhost:8081',
    pack_id='docling',
    storage_path_mapping=(Path('/home/user/storage'), Path('/storage'))
)

# New way (automatic)
# Just set env vars, no manual mapping needed!
adapter = PackAdapter(
    storage=storage,
    provider_url='http://localhost:8081',
    pack_id='docling'
)
```

## Manual Worker Start

If you need more control, start workers manually:

```bash
export STORAGE_HOST_ROOT=/home/gaopeng/localstorage/docalchemy
export STORAGE_PROVIDER_ROOT=/storage

# Docling worker
PACK_ID=docling \
PROVIDER_URL=http://localhost:8081 \
PACK_QUEUE=analysis.docling \
celery -A app.infrastructure.workers.pack_worker worker --loglevel=info

# Repeat for other providers (mineru, opendataloader, franken_ocr)
```

## Troubleshooting

### Container can't access files
**Symptom**: `input not found` error

**Check**:
1. The `/storage` volume is mounted correctly in the docalchemy repo's `docker-compose.yml`
2. `STORAGE_HOST_ROOT` matches the host path in docker-compose
3. File exists: `ls $STORAGE_HOST_ROOT/4b/`

### Models not downloading
**Symptom**: `Network is unreachable` or SSL errors

**Solution**: Check the docalchemy repo's `docker-compose.yml` has:
```yaml
environment:
  - HF_ENDPOINT=https://hf-mirror.com  # Use China mirror
```

### Worker can't connect to provider
**Symptom**: `Connection refused`

**Check**:
1. Providers are running: `docker ps`
2. Ports are accessible: `curl http://localhost:8081/health`
3. Provider URL in worker config is correct

## Provider Endpoints

- Docling: http://localhost:8081
- MinerU: http://localhost:8082
- OpenDataLoader: http://localhost:8083
- Franken OCR: http://localhost:8084
