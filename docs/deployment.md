# Deployment Guide

This guide covers deployment options for the Agentic Workflow Framework.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Production Best Practices](#production-best-practices)
5. [Monitoring and Logging](#monitoring-and-logging)

## Local Development

### Prerequisites

- Python 3.11+
- pip or uv
- Git

### Setup Steps

```bash
# Clone repository
git clone <repository-url>
cd agentic-workflow-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# ANTHROPIC_API_KEY=sk-ant-v3-...
```

### Running Locally

```bash
# Run parent workflow via CLI
python main.py --story-file examples/stories/api_development.md

# Start API Enhancement service (separate terminal)
python -m uvicorn workflows.children.api_enhancement.service:app --port 8001

# Run tests
pytest tests/ -v
```

## Docker Compose Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- 4GB+ RAM available

### Quick Start

```bash
# Create environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api_enhancement_service
```

### Service Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| API Enhancement | http://localhost:8001 | Workflow execution |
| Nginx Gateway | http://localhost:80 | API gateway (optional) |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache/jobs |
| Prometheus | http://localhost:9090 | Metrics |

### Configuration

**docker-compose.yaml** includes:

- **api_enhancement_service**: FastAPI workflow service
- **postgres**: Database for state persistence
- **redis**: Caching and job queue
- **nginx**: Reverse proxy and API gateway
- **prometheus**: Metrics collection

### Environment Variables

```env
ANTHROPIC_API_KEY=your-api-key
POSTGRES_PASSWORD=secure-password
```

See `.env.example` for complete configuration options.

### Managing Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# View service logs
docker-compose logs -f <service_name>

# Rebuild images
docker-compose build --no-cache

# Scale service (if configured)
docker-compose up -d --scale api_enhancement_service=3
```

## Kubernetes Deployment

For production Kubernetes deployments, use Helm charts or Kustomize.

### Example Kubernetes Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-enhancement-service
  labels:
    app: api-enhancement-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-enhancement-service
  template:
    metadata:
      labels:
        app: api-enhancement-service
    spec:
      containers:
      - name: api-enhancement-service
        image: api-enhancement-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /metadata
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: api-enhancement-service
spec:
  selector:
    app: api-enhancement-service
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8001
  type: ClusterIP
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace agentic

# Create secrets
kubectl create secret generic api-keys \
  --from-literal=anthropic-key=$ANTHROPIC_API_KEY \
  -n agentic

# Deploy
kubectl apply -f k8s-manifests/ -n agentic

# Check status
kubectl get pods -n agentic
kubectl logs -f deployment/api-enhancement-service -n agentic
```

## Production Best Practices

### 1. Security

```bash
# Use strong passwords
openssl rand -base64 32  # Generate random password

# Store secrets in environment variables or secret manager
export ANTHROPIC_API_KEY=...
export POSTGRES_PASSWORD=...

# Enable HTTPS
# Update docker-compose.yaml to use SSL certificates
# Use Let's Encrypt for free certificates
```

### 2. Resource Management

```yaml
# In docker-compose.yaml
services:
  api_enhancement_service:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 3. Scaling

```bash
# Scale API Enhancement service to 3 instances
docker-compose up -d --scale api_enhancement_service=3

# For Kubernetes
kubectl scale deployment api-enhancement-service --replicas=3 -n agentic
```

### 4. Database Backups

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U agentic_user agentic_workflows > backup.sql

# Restore backup
cat backup.sql | docker-compose exec -T postgres psql -U agentic_user agentic_workflows
```

### 5. Health Checks

```bash
# Check service health
curl http://localhost:8001/health

# Check all services
docker-compose ps

# Kubernetes health checks
kubectl get pods -n agentic
kubectl describe pod <pod-name> -n agentic
```

### 6. Logging and Monitoring

**Configure structured logging**:

```env
LOG_FORMAT=json
LOG_LEVEL=WARNING  # Production: INFO or WARNING
```

**Monitor with Prometheus**:

```bash
# Access Prometheus
open http://localhost:9090

# Query metrics
rate(workflow_executions_total[5m])
histogram_quantile(0.95, workflow_execution_duration_seconds)
```

## Monitoring and Logging

### Prometheus Metrics

Available metrics:

```
workflow_executions_total           # Total workflow executions
workflow_executions_failed_total    # Failed executions
workflow_execution_duration_seconds # Execution duration histogram
workflow_tasks_total                # Total tasks executed
cache_hits_total                    # Cache hit rate
api_requests_total                  # API request count
```

### Log Aggregation

With ELK Stack (Elasticsearch, Logstash, Kibana):

```yaml
logstash:
  image: docker.elastic.co/logstash/logstash:7.14.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/config/logstash.conf
  environment:
    LS_JAVA_OPTS: "-Xmx256m -Xms256m"
```

### Alerting

Prometheus alerting rules:

```yaml
groups:
- name: agentic_workflows
  interval: 1m
  rules:
  - alert: HighErrorRate
    expr: rate(workflow_executions_failed_total[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High workflow error rate"

  - alert: ServiceDown
    expr: up{job="api_enhancement_service"} == 0
    for: 1m
    annotations:
      summary: "API Enhancement service is down"
```

## Troubleshooting

### Common Issues

**Service won't start**:
```bash
# Check logs
docker-compose logs api_enhancement_service

# Verify environment variables
docker-compose config | grep ANTHROPIC
```

**Database connection error**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Verify connection
docker-compose exec postgres psql -U agentic_user -d agentic_workflows -c "SELECT 1"
```

**Out of memory**:
```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yaml
# or adjust Kubernetes requests/limits
```

**API timeouts**:
```bash
# Increase timeout in configuration
COORDINATOR_TIMEOUT=600  # seconds
INVOKER_TIMEOUT=120      # seconds
```

## Performance Tuning

### PostgreSQL

```sql
-- Increase shared_buffers
-- shared_buffers = 256MB (default 40MB)

-- Enable connection pooling
-- Use pgBouncer or similar
```

### Redis

```bash
# Configure persistence
appendonly yes
appendfsync everysec

# Monitor memory usage
redis-cli INFO memory
```

### Application

```env
# Increase worker processes
WORKER_PROCESSES=4

# Adjust cache size
INVOKER_CACHE_SIZE=1000

# Tune timeouts
COORDINATOR_TIMEOUT=600
```

## Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# Daily backup script

BACKUP_DIR=/backups/agentic
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U agentic_user agentic_workflows | \
    gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup Redis
docker-compose exec redis redis-cli BGSAVE

# Backup application files
tar -czf $BACKUP_DIR/app_$TIMESTAMP.tar.gz ./workflows ./config

# Keep only last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
```

### Recovery Procedure

```bash
# Restore PostgreSQL
docker-compose down
gunzip < backup.sql.gz | docker-compose exec -T postgres \
    psql -U agentic_user agentic_workflows
docker-compose up -d
```

---

For more information:
- [Configuration Guide](configuration.md)
- [Architecture Documentation](architecture.md)
- [API Reference](api_reference.md)
