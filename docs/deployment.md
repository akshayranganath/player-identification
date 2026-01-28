# Deployment Guide

## Prerequisites

- Python 3.12+
- uv package manager
- Docker (for containerized deployment)
- AWS credentials with Bedrock access
- SerpAPI key

## Local Development Setup

### 1. Clone and Install

```bash
# Clone repository
git clone <repository-url>
cd player-identification

# Install uv
pip install uv

# Install dependencies
uv sync

# Install development dependencies
uv sync --extra dev
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required variables:
```env
SERP_API_KEY=your_serpapi_key_here
AWS_PROFILE=your_aws_profile
AWS_REGION=us-east-1
```

### 3. Set File Permissions

```bash
# Secure .env file (Unix/Linux/Mac)
chmod 600 .env

# Install git hooks to prevent .env commits
bash scripts/setup_git_hooks.sh
```

### 4. Run Application

```bash
# Normal mode
uv run streamlit run app.py

# Verbose mode (debug logging)
uv run streamlit run app.py -- --verbose
```

Access at: http://localhost:8501

## Docker Deployment

### 1. Build Image

```bash
# Build Docker image
docker build -f infrastructure/docker/Dockerfile -t cfl-player-id:latest .
```

### 2. Run Container

```bash
# Run with .env file
docker run -p 8501:8501 --env-file .env cfl-player-id:latest

# Or with environment variables
docker run -p 8501:8501 \
  -e SERP_API_KEY=your_key \
  -e AWS_REGION=us-east-1 \
  cfl-player-id:latest
```

### 3. Docker Compose (Recommended)

```bash
# Start all services
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# View logs
docker-compose -f infrastructure/docker/docker-compose.yml logs -f

# Stop services
docker-compose -f infrastructure/docker/docker-compose.yml down
```

## Production Deployment

### Option 1: AWS ECS/Fargate

1. **Push image to ECR**
```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag cfl-player-id:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/cfl-player-id:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/cfl-player-id:latest
```

2. **Deploy to ECS**
```bash
# Using terraform
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### Option 2: Traditional Server

1. **Transfer files securely**
```bash
# Copy code (excluding .env)
rsync -av --exclude='.env' --exclude='data/' . user@server:/app/

# Copy .env separately (secure)
scp .env user@server:/app/.env
ssh user@server "chmod 600 /app/.env"
```

2. **Setup systemd service**
```ini
# /etc/systemd/system/cfl-player-id.service
[Unit]
Description=CFL Player Identification
After=network.target

[Service]
Type=simple
User=app-user
WorkingDirectory=/app
Environment="PATH=/app/.venv/bin:/usr/bin"
ExecStart=/app/.venv/bin/streamlit run app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable cfl-player-id
sudo systemctl start cfl-player-id
sudo systemctl status cfl-player-id
```

## Environment-Specific Configuration

### Development
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
MAX_RETRIES=1
```

### Staging
```env
ENVIRONMENT=staging
LOG_LEVEL=INFO
MAX_RETRIES=3
```

### Production
```env
ENVIRONMENT=production
LOG_LEVEL=WARNING
MAX_RETRIES=3
RATE_LIMIT_PER_MINUTE=60
```

## Secrets Management

### Local Development
- Use `.env` file
- Set permissions to 600
- Never commit to git

### Production Options

**Option 1: .env file on server**
```bash
# Secure transfer
scp .env user@prod-server:/app/.env
ssh user@prod-server "chmod 600 /app/.env; chown app-user /app/.env"
```

**Option 2: AWS Parameter Store (Free)**
```bash
# Store secrets
aws ssm put-parameter \
  --name "/cfl-player-id/serp-api-key" \
  --value "your_key" \
  --type "SecureString"

# Fetch at startup (modify src/core/config.py)
```

**Option 3: Environment Variables via CI/CD**
```yaml
# GitHub Actions
- name: Deploy with secrets
  run: |
    cat > .env << EOF
    SERP_API_KEY=${{ secrets.SERP_API_KEY }}
    AWS_REGION=us-east-1
    EOF
    deploy-script.sh
```

## Monitoring & Logging

### Application Logs
```bash
# Docker
docker logs cfl-player-id

# Systemd
journalctl -u cfl-player-id -f

# File-based
tail -f /var/log/cfl-player-id/app.log
```

### Health Checks
```bash
# Docker health check
docker ps --filter health=healthy

# HTTP endpoint (if implemented)
curl http://localhost:8501/_stcore/health
```

## Backup & Recovery

### Backup Player Database
```bash
# Backup
cp data/db/cfl_players.json data/db/cfl_players.json.backup.$(date +%Y%m%d)

# Restore
cp data/db/cfl_players.json.backup.20260128 data/db/cfl_players.json
```

### Backup Configuration
```bash
# Encrypted backup of .env
gpg -c .env
# Creates .env.gpg (safe to store)

# Restore
gpg .env.gpg
# Creates .env file
```

## Troubleshooting

### Common Issues

**1. AWS Credentials Error**
```bash
# Check AWS profile
aws sts get-caller-identity --profile your_profile

# Clear conflicting env vars
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

**2. Permission Denied (.env)**
```bash
chmod 600 .env
```

**3. Missing Dependencies**
```bash
# Reinstall
uv sync --reinstall
```

**4. Port Already in Use**
```bash
# Change port
uv run streamlit run app.py --server.port=8502
```

## Security Checklist

Before deploying to production:

- [ ] `.env` file has 600 permissions
- [ ] `.env` is in .gitignore
- [ ] Git hooks are installed
- [ ] Secrets are not in code
- [ ] AWS credentials are properly configured
- [ ] Firewall rules are configured
- [ ] HTTPS is enabled (if web-facing)
- [ ] Regular security updates planned
- [ ] Monitoring and alerting configured
- [ ] Backup strategy in place

## Performance Tuning

### For High Traffic

1. **Enable Redis caching**
```yaml
# docker-compose.yml already includes Redis
# Modify src/services/ to use caching
```

2. **Increase worker count**
```bash
# Multiple Streamlit instances behind load balancer
```

3. **Database optimization**
```python
# Migrate from JSON to PostgreSQL
# Add connection pooling
```

## Rollback Procedure

### Docker Deployment
```bash
# Rollback to previous version
docker pull cfl-player-id:previous-tag
docker stop cfl-player-id-container
docker run -d --name cfl-player-id-container cfl-player-id:previous-tag
```

### Server Deployment
```bash
# Restore from backup
cd /app
git checkout <previous-commit>
uv sync
sudo systemctl restart cfl-player-id
```

## Support & Maintenance

### Regular Tasks
- Weekly: Review logs for errors
- Monthly: Update dependencies
- Quarterly: Security audit
- Annually: Architecture review

### Useful Commands
```bash
# View resource usage
docker stats

# Check application status
systemctl status cfl-player-id

# Test configuration
uv run python -m src.core.config

# Run security scan
uv run bandit -r src/
uv run safety check
```
