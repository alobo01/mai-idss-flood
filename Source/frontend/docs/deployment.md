# 🚀 Deployment

Comprehensive deployment guide for the Flood Prediction Frontend application in various environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Development Deployment](#development-deployment)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Environment Configuration](#environment-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Overview

The Flood Prediction Frontend supports multiple deployment strategies optimized for different use cases:

- **Development**: Hot-reload local development with the API
- **Docker**: Containerized deployment with orchestration
- **Production**: Optimized builds with CDN and load balancing
- **Cloud**: Managed services and auto-scaling

## Prerequisites

### System Requirements

**Minimum**:
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 10GB available space
- **Network**: Stable internet connection

**Recommended**:
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ SSD
- **Network**: High-speed internet

### Software Requirements

- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for orchestration)
- **Node.js**: 18+ (for local development)
- **Git**: 2.30+ (for source control)

## Development Deployment

### Local Development Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd flood-prediction-frontend

# 2. Install dependencies
npm install

# 3. Install Playwright browsers (for testing)
npx playwright install

# 4. Start API (in terminal 1)
npm run api

# 5. Start frontend (in terminal 2)
cd ..
npm run dev
```

### Development URLs

- **Frontend**: http://localhost:5173
- **API**: http://localhost:18080
- **API Health**: http://localhost:18080/health

### Development Configuration

```env
# .env.development
VITE_API_BASE_URL=http://localhost:18080
VITE_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
VITE_WS_URL=ws://localhost:18080
VITE_ENVIRONMENT=development
VITE_LOG_LEVEL=debug
```

## Docker Deployment

### Quick Start

```bash
# Build and start all services
docker compose up --build

# Run in background
docker compose up --build -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: "3.9"

services:
  postgres:
    image: postgis/postgis:15-3.3
    container_name: flood-postgres
    environment:
      - POSTGRES_DB=flood_prediction
      - POSTGRES_USER=flood_user
      - POSTGRES_PASSWORD=flood_password
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: flood-backend
    ports:
      - "18080:18080"
    environment:
      - NODE_ENV=production
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_USER=flood_user
      - DB_PASSWORD=flood_password
      - DB_NAME=flood_prediction
    restart: unless-stopped
    networks:
      - flood-network
    depends_on:
      - postgres
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:18080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: flood-frontend
    ports:
      - "5173:80"
    environment:
      - NODE_ENV=production
      - VITE_API_BASE_URL=http://backend:18080
      - VITE_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - flood-network

networks:
  flood-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  postgres_data:
    driver: local

```

### Multi-Stage Dockerfile

```dockerfile
# Dockerfile
FROM node:20-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application
COPY --from=build /app/dist /usr/share/nginx/html

# Copy mock data (if needed)
COPY public/mock /usr/share/nginx/html/mock

# Create non-root user
RUN addgroup -g 1001 -S nginx && \
    adduser -S nginx -u 1001

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d

# Switch to non-root user
USER nginx

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Production Docker Configuration

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  web:
    extends:
      file: docker-compose.yml
      service: web
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  nginx-proxy:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-proxy.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - flood-network

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - flood-network

volumes:
  redis-data:
    driver: local
```

## Production Deployment

### Production Build

```bash
# Create production build
npm run build

# Preview production build
npm run preview

# Build for specific environment
npm run build:production
```

### Nginx Configuration

```nginx
# nginx-proxy.conf
upstream flood_backend {
    server web:80;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=flood_api:10m rate=10r/s;

server {
    listen 80;
    server_name flood-prediction.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name flood-prediction.example.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }

    # API proxy with rate limiting
    location /api/ {
        limit_req zone=flood_api burst=20 nodelay;
        proxy_pass http://flood_backend/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /ws {
        proxy_pass http://flood_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Main application
    location / {
        proxy_pass http://flood_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Handle client-side routing
        try_files $uri $uri/ @fallback;
    }

    location @fallback {
        proxy_pass http://flood_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://flood_backend/health;
    }
}
```

### Production Environment Variables

```env
# .env.production
NODE_ENV=production
VITE_API_BASE_URL=https://api.flood-prediction.example.com
VITE_MAP_TILES_URL=https://tiles.flood-prediction.example.com/{z}/{x}/{y}.png
VITE_WS_URL=wss://ws.flood-prediction.example.com
VITE_ENVIRONMENT=production
VITE_LOG_LEVEL=error
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
VITE_GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID
```

## Cloud Deployment

### AWS Deployment

#### ECS (Elastic Container Service)

```json
{
  "family": "flood-prediction",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "flood-frontend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/flood-frontend:latest",
      "portMappings": [
        {
          "containerPort": 80,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "VITE_API_BASE_URL",
          "value": "https://api.flood-prediction.example.com"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/flood-prediction",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### CloudFront Distribution

```json
{
  "DistributionConfig": {
    "CallerReference": "flood-prediction-cdn",
    "Origins": {
      "Quantity": 1,
      "Items": [
        {
          "Id": "ECS-Origin",
          "DomainName": "load-balancer.example.com",
          "CustomOriginConfig": {
            "HTTPPort": 80,
            "HTTPSPort": 443,
            "OriginProtocolPolicy": "https-only"
          }
        }
      ]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "ECS-Origin",
      "ViewerProtocolPolicy": "redirect-to-https",
      "TrustedSigners": {
        "Enabled": false,
        "Quantity": 0
      },
      "ForwardedValues": {
        "QueryString": true,
        "Cookies": {
          "Forward": "all"
        }
      },
      "MinTTL": 0,
      "Compress": true
    },
    "Enabled": true,
    "HttpVersion": "http2",
    "PriceClass": "PriceClass_All"
  }
}
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/flood-frontend

# Deploy to Cloud Run
gcloud run deploy flood-frontend \
  --image gcr.io/PROJECT-ID/flood-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300s \
  --set-env-vars VITE_API_BASE_URL=https://api.example.com
```

#### Cloud Load Balancer

```yaml
# cloud-load-balancer.yaml
apiVersion: cloud.google.com/v1
kind: Service
metadata:
  name: flood-frontend-lb
  annotations:
    cloud.google.com/load-balancer-type: "External"
spec:
  type: LoadBalancer
  selector:
    app: flood-frontend
  ports:
    - port: 80
      targetPort: 80
    - port: 443
      targetPort: 443
```

### Azure Container Instances

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group flood-prediction-rg \
  --name flood-frontend \
  --image your-registry.azurecr.io/flood-frontend:latest \
  --cpu 1 \
  --memory 2 \
  --ports 80 443 \
  --environment-variables VITE_API_BASE_URL=https://api.example.com
```

## Environment Configuration

### Environment-Specific Builds

```json
// package.json scripts
{
  "scripts": {
    "build:development": "vite build --mode development",
    "build:staging": "vite build --mode staging",
    "build:production": "vite build --mode production",
    "build:test": "vite build --mode test"
  }
}
```

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: mode !== 'production',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            router: ['react-router-dom'],
            query: ['@tanstack/react-query'],
            ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          },
        },
      },
    },
    server: {
      host: true,
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:18080',
          changeOrigin: true,
        },
      },
    },
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    },
  };
});
```

## Monitoring and Logging

### Health Checks

```typescript
// src/health.ts
export const healthCheck = async () => {
  try {
    const response = await fetch('/api/health');
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Health check error:', error);
    throw error;
  }
};

// Periodic health monitoring
setInterval(async () => {
  try {
    await healthCheck();
  } catch (error) {
    // Report health check failure
    reportError(error);
  }
}, 60000); // Check every minute
```

### Error Reporting

```typescript
// src/errorReporting.ts
import * as Sentry from '@sentry/react';

if (import.meta.env.PROD) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
    release: `flood-frontend@${__APP_VERSION__}`,
  });
}

export const reportError = (error: Error, context?: any) => {
  if (import.meta.env.PROD) {
    Sentry.captureException(error, { extra: context });
  } else {
    console.error('Error reported:', error, context);
  }
};
```

### Performance Monitoring

```typescript
// src/performance.ts
export const reportPerformance = (name: string, duration: number) => {
  // Send to analytics service
  if (window.gtag) {
    window.gtag('event', 'performance_metric', {
      event_category: 'Web Vitals',
      event_label: name,
      value: Math.round(duration),
      custom_map: { metric_name: name, metric_value: duration }
    });
  }
};

// Core Web Vitals monitoring
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(reportPerformance);
getFID(reportPerformance);
getFCP(reportPerformance);
getLCP(reportPerformance);
getTTFB(reportPerformance);
```

## Security Considerations

### Content Security Policy

```html
<!-- index.html -->
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://www.googletagmanager.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self' data:;
  connect-src 'self' https://api.flood-prediction.example.com wss://ws.flood-prediction.example.com;
  frame-src 'none';
  base-uri 'self';
  form-action 'self';
">
```

### Security Headers

```nginx
# Security headers in nginx configuration
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

### Environment Variable Security

```bash
# Use encrypted secrets in production
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id flood-prediction/secrets

# Google Secret Manager
gcloud secrets versions access latest --secret=flood-prediction-secrets

# Azure Key Vault
az keyvault secret show --vault-name flood-prediction-kv --name app-secrets
```

## Troubleshooting

### Common Deployment Issues

**Build Failures**:
```bash
# Clear build cache
rm -rf node_modules dist
npm install
npm run build

# Check for missing dependencies
npm audit
npm audit fix
```

**Container Issues**:
```bash
# Check container logs
docker compose logs web
docker compose logs backend

# Inspect container
docker compose exec web sh
docker compose exec backend sh

# Rebuild containers
docker compose build --no-cache
```

**Performance Issues**:
```bash
# Analyze bundle size
npm run build:analyze

# Check network requests
# Open browser dev tools > Network tab

# Monitor memory usage
docker stats
```

### Health Check Failures

```bash
# Test health endpoint manually
curl http://localhost:18080/health

# Check container health
docker compose ps

# Restart unhealthy services
docker compose restart
```

### Network Issues

```bash
# Check network connectivity
docker network ls
docker network inspect flood-prediction_flood-network

# Test API connectivity
curl -v http://localhost:18080/api/zones

# Check DNS resolution
nslookup api.flood-prediction.example.com
```

### Debug Commands

```bash
# Full debug information
docker compose version
docker info
docker system df
docker system events

# Production debugging
docker compose --file docker-compose.prod.yml logs --tail=100
docker compose --file docker-compose.prod.yml exec web nginx -t
```

This deployment guide provides comprehensive instructions for deploying the Flood Prediction Frontend across various environments and platforms. Choose the deployment method that best fits your infrastructure requirements and scaling needs.
