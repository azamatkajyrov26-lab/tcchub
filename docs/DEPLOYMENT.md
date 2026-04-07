# TCC HUB LMS — Deployment Guide

## Prerequisites

- Docker Engine 24+
- Docker Compose v2+
- Git
- Domain name (for production)
- At least 2 GB RAM, 20 GB disk

## 1. Clone and Configure

```bash
git clone <repository-url> tcchub
cd tcchub

# Create environment file from example
cp .env.example .env
```

Edit `.env` with your values:

```bash
# REQUIRED — change these:
SECRET_KEY=<generate-a-random-64-char-string>
DB_PASSWORD=<strong-database-password>
POSTGRES_PASSWORD=<same-as-DB_PASSWORD>
ALLOWED_HOSTS=tcchub.kz,www.tcchub.kz
SITE_URL=https://tcchub.kz

# Email settings (for password reset, notifications):
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

Generate a secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 2. Build and Start (Development)

```bash
# Build all images
make build

# Start all services
make up

# Check that everything is running
docker compose ps

# View logs
make logs
```

Services will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1/
- **Admin panel:** http://localhost:8000/admin/
- **Full app (via Nginx):** http://localhost

## 3. Initialize the Application

```bash
# Run database migrations
make migrate

# Create admin user
make createsuperuser

# Collect static files (already done by entrypoint, but just in case)
make collectstatic
```

## 4. Production Deployment

### 4.1 Server Setup (Ubuntu 22.04+)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt install docker-compose-plugin -y

# Install Certbot for SSL
sudo apt install certbot -y
```

### 4.2 SSL with Let's Encrypt

Create `/home/azamat/tcchub/docker/nginx-production.conf`:

```nginx
server {
    listen 80;
    server_name tcchub.kz www.tcchub.kz;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name tcchub.kz www.tcchub.kz;

    ssl_certificate /etc/letsencrypt/live/tcchub.kz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tcchub.kz/privkey.pem;

    # ... (copy location blocks from docker/nginx.conf)
}
```

Obtain certificate:
```bash
sudo certbot certonly --standalone -d tcchub.kz -d www.tcchub.kz
```

Add to docker-compose for production — mount certificate volumes to nginx:
```yaml
nginx:
  volumes:
    - /etc/letsencrypt:/etc/letsencrypt:ro
    - ./docker/nginx-production.conf:/etc/nginx/conf.d/default.conf:ro
  ports:
    - "80:80"
    - "443:443"
```

### 4.3 Production Environment Variables

Ensure these are set in `.env`:

```bash
DEBUG=0
SECRET_KEY=<long-random-string>
ALLOWED_HOSTS=tcchub.kz,www.tcchub.kz
SITE_URL=https://tcchub.kz
NEXT_PUBLIC_API_URL=https://tcchub.kz/api
CORS_ALLOWED_ORIGINS=https://tcchub.kz,https://www.tcchub.kz
```

### 4.4 Deploy

```bash
make build
make up
make migrate
```

### 4.5 Auto-renew SSL Certificate

Add a cron job:
```bash
crontab -e
# Add:
0 3 * * * certbot renew --quiet && docker compose -f /home/azamat/tcchub/docker-compose.yml restart nginx
```

## 5. Updating the Application

```bash
cd /home/azamat/tcchub

# Pull latest code
git pull origin main

# Rebuild and restart
make build
make up
make migrate
```

## 6. Backup and Restore

### Database Backup
```bash
# Create backup
make db-backup
# Output: backup_20260323_120000.sql

# Restore from backup
make db-restore FILE=backup_20260323_120000.sql
```

### Full Backup (data volumes)
```bash
# Stop services
make down

# Backup volumes
docker run --rm -v tcchub_postgres_data:/data -v $(pwd):/backup alpine \
    tar czf /backup/postgres_data.tar.gz -C /data .

docker run --rm -v tcchub_media_data:/data -v $(pwd):/backup alpine \
    tar czf /backup/media_data.tar.gz -C /data .

# Restart
make up
```

## 7. Monitoring

### View Logs
```bash
make logs                # All services
make backend-logs        # Django only
make frontend-logs       # Next.js only
make celery-logs         # Celery worker + beat
make db-logs             # PostgreSQL
```

### Check Service Health
```bash
docker compose ps
curl -s http://localhost/health  # Nginx health check
curl -s http://localhost:8000/api/v1/  # Backend API root
```

## 8. Troubleshooting

| Problem                        | Solution                                         |
|--------------------------------|--------------------------------------------------|
| Backend won't start            | `make backend-logs` — check for migration errors |
| Database connection refused    | Ensure `db` service is healthy: `docker compose ps` |
| Static files not loading       | `make collectstatic` then restart nginx          |
| Celery tasks not running       | `make celery-logs` — check broker connection     |
| Frontend build fails           | Check Node.js version, run `docker compose build frontend` |
| Permission denied on media     | `docker compose exec backend chown -R 1000:1000 /app/media` |
| Port already in use            | `sudo lsof -i :80` — stop conflicting service   |

## 9. Scaling (Optional)

Scale backend workers:
```bash
docker compose up -d --scale backend=3
```

Scale Celery workers:
```bash
docker compose up -d --scale celery_worker=4
```

Note: Do **not** scale `celery_beat` beyond 1 instance.
