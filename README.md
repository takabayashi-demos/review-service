# review-service

Product reviews and ratings service

## Tech Stack
- **Language**: python
- **Team**: customer
- **Platform**: Walmart Global K8s

## Quick Start
```bash
docker build -t review-service:latest .
docker run -p 8080:8080 review-service:latest
curl http://localhost:8080/health
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /ready | Readiness probe |
| GET | /metrics | Prometheus metrics |
