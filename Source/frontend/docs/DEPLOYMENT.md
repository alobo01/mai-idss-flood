# Deployment Guide

This guide covers deployment options for the Flood Prediction Frontend application, including Docker, production builds, and development setup.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Production Build](#production-build)
- [Environment Configuration](#environment-configuration)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Node.js 18+ (for local development)
- Docker & Docker Compose (for containerized deployment)
- Nginx (for production reverse proxy, optional)
- SSL certificate (for production HTTPS)

### System Requirements

- **Minimum**: 2GB RAM, 1 CPU core
- **Recommended**: 4GB RAM, 2+ CPU cores
- **Storage**: 500MB for application + mock data

## Quick Start

### Docker (Recommended)

```bash
# Clone and start the application
git clone <repository-url>
cd frontend
docker compose up -d

# Access the application
open http://localhost:8080
```

### Local Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Start mock API (in another terminal)
cd mock-api && node server.js
```

## Docker Deployment

### Production Docker Compose

The provided `docker-compose.yml` is configured for production use:

```yaml
services:
  api:
    build:
      context: .
      dockerfile: mock-api/Dockerfile
    container_name: flood-api
    ports:
      - "8081:8080"
    environment:
      - NODE_ENV=production
    restart: unless-stopped

  web:
    build: .
    container_name: flood-frontend
    ports:
      - "8080:80"
    depends_on:
      - api
    restart: unless-stopped
```

### Building and Running

```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Container Architecture

- **Frontend Container**: Nginx serving optimized static files
- **API Container**: Node.js Express server with mock data
- **Network**: Internal Docker network for service communication
- **Health Checks**: Built-in health monitoring

## Production Build

### Building Locally

```bash
# Install dependencies
npm install

# Build for production
npm run build

# The build output is in ./dist/
```

### Build Configuration

The production build includes:
- TypeScript compilation
- Code minification and optimization
- Asset bundling and compression
- Source map generation (disabled in production)

### Environment Variables

Configure these environment variables for production:

```bash
# API Configuration
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_MAP_TILES_URL=https://tile-server.yourdomain.com/{z}/{x}/{y}.png

# Build Configuration
NODE_ENV=production
```

## Environment Configuration

### Development

Create `.env.development`:
```env
VITE_API_BASE_URL=http://localhost:8081
VITE_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
NODE_ENV=development
```

### Production

Create `.env.production`:
```env
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_MAP_TILES_URL=https://tile-server.yourdomain.com/{z}/{x}/{y}.png
NODE_ENV=production
```

### Configuration Files

- `vite.config.ts` - Vite build configuration
- `nginx.conf` - Production Nginx configuration
- `docker-compose.yml` - Docker service orchestration

## Reverse Proxy Setup

### Nginx Configuration

For production deployment behind Nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Frontend static files
    location / {
        root /var/www/flood-frontend/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL Configuration

```bash
# Generate SSL certificate (Let's Encrypt recommended)
certbot --nginx -d your-domain.com

# Or use self-signed for development
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/nginx-selfsigned.key \
  -out /etc/ssl/certs/nginx-selfsigned.crt
```

## Monitoring and Health Checks

### Application Health

- **Frontend**: Health check via Nginx status
- **API**: `GET /health` endpoint returns service status
- **Containers**: Built-in Docker health checks

### Monitoring Endpoints

```bash
# API Health Check
curl http://localhost:8081/health

# Container Status
docker compose ps

# Resource Usage
docker stats
```

### Logging

```bash
# View application logs
docker compose logs -f

# View specific service logs
docker compose logs -f api
docker compose logs -f web
```

## Troubleshooting

### Common Issues

#### 1. Containers Won't Start

```bash
# Check for port conflicts
netstat -tulpn | grep :8080
netstat -tulpn | grep :8081

# Check Docker daemon
docker version
docker compose version
```

#### 2. API Connection Errors

```bash
# Verify API is accessible
curl http://localhost:8081/health
curl http://localhost:8081/api/zones

# Check network connectivity
docker network ls
docker network inspect flood-network
```

#### 3. Build Failures

```bash
# Clear build cache
docker builder prune

# Rebuild from scratch
docker compose build --no-cache

# Check disk space
df -h
```

#### 4. Memory Issues

```bash
# Check container resource usage
docker stats

# Increase memory limits in docker-compose.yml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 1G
```

### Performance Optimization

#### 1. Frontend Optimization

- Enable Gzip compression (configured in nginx.conf)
- Use CDN for static assets
- Implement proper caching headers
- Monitor bundle size

#### 2. API Optimization

- Enable response compression
- Implement API rate limiting
- Use Redis for caching (when replacing mock API)
- Monitor response times

#### 3. Container Optimization

```bash
# Use multi-stage builds (already implemented)
# Minimize image layers
# Use specific version tags
FROM nginx:alpine  # Good
FROM nginx:latest  # Avoid
```

## Security Considerations

### Container Security

- Use non-root users when possible
- Regular base image updates
- Scan images for vulnerabilities
```bash
docker scan frontend-api
docker scan frontend-web
```

### Network Security

- Use HTTPS in production
- Implement firewall rules
- Secure API endpoints with authentication
- Rate limiting and DDoS protection

### Data Security

- Validate all inputs (Zod schemas implemented)
- Sanitize user inputs
- Secure sensitive configuration
- Regular security audits

## Scaling and High Availability

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  web:
    deploy:
      replicas: 3

  api:
    deploy:
      replicas: 2
```

### Load Balancing

Configure Nginx as load balancer:

```nginx
upstream api_servers {
    server api1:8080;
    server api2:8080;
    server api3:8080;
}

server {
    location /api/ {
        proxy_pass http://api_servers;
    }
}
```

## Backup and Recovery

### Data Backup

```bash
# Backup static assets
tar -czf backup-$(date +%Y%m%d).tar.gz dist/

# Backup configuration
cp docker-compose.yml docker-compose.yml.backup
cp nginx.conf nginx.conf.backup
```

### Disaster Recovery

1. Maintain regular backups
2. Document recovery procedures
3. Test backup restoration
4. Monitor system health

## Support and Maintenance

### Regular Maintenance

- Update dependencies regularly
```bash
npm audit
npm update
```

- Monitor Docker image updates
- Review and rotate SSL certificates
- Update security patches

### Performance Monitoring

Set up monitoring for:
- Response times
- Error rates
- Resource utilization
- User experience metrics

---

For additional support or questions, refer to the project documentation or create an issue in the repository.