# API Troubleshooting & FAQ

Common issues, solutions, and frequently asked questions for the Flood Prediction API.

## 🚨 Quick Start Issues

### API Not Responding
**Symptoms**: Connection refused, timeout errors, blank pages

**Solutions**:
1. **Check Docker Services**:
   ```bash
   docker compose ps
   # All services should show "running" state
   ```

2. **Verify Service Health**:
   ```bash
   curl http://localhost:8080/health
   # Should return: {"status":"ok","database":"connected"}
   ```

3. **Restart Services**:
   ```bash
   docker compose down
   docker compose up --build
   ```

### Database Connection Issues
**Symptoms**: "Database unavailable" health status, 500 errors

**Solutions**:
1. **Check Database Container**:
   ```bash
   docker compose logs backend
   # Look for database connection errors
   ```

2. **Verify Database Ready State**:
   ```bash
   # Database may take 30-60 seconds to initialize
   docker compose logs database | grep "ready to accept"
   ```

3. **Manual Database Check**:
   ```bash
   docker compose exec backend npm run test-db
   # Test database connection and queries
   ```

## 🌐 Access Issues

### Frontend Can't Reach API
**Symptoms**: 404 errors, CORS issues, blank API documentation

**Common Causes**:
1. **Wrong Port**: API is on port 8080, not 3000
2. **Service Naming**: Docker services renamed from 'api' to 'backend'
3. **Proxy Configuration**: nginx needs backend service reference

**Solutions**:
1. **Use Correct URLs**:
   - API: `http://localhost:8080/*`
   - Documentation: `http://localhost:8080/api-docs/`
   - Frontend: `http://localhost/`

2. **Check nginx Configuration**:
   ```bash
   # Verify nginx proxy passes to backend service
   docker compose exec frontend grep proxy_pass /etc/nginx/nginx.conf
   # Should show: proxy_pass http://backend:8080
   ```

3. **Rebuild Containers**:
   ```bash
   docker compose down
   docker compose up --build
   # Ensures latest configuration is applied
   ```

### CORS Errors
**Symptoms**: Browser console shows CORS policy errors

**Solutions**:
1. **API CORS Configuration**:
   ```javascript
   // Backend should have CORS enabled for frontend origin
   app.use(cors({
     origin: ['http://localhost', 'http://localhost:5173'],
     credentials: true
   }));
   ```

2. **Direct API Testing**:
   ```bash
   # Test CORS with curl
   curl -H "Origin: http://localhost" \
        -H "Access-Control-Request-Method: GET" \
        -H "Access-Control-Request-Headers: X-Requested-With" \
        -X OPTIONS http://localhost:8080/api/zones
   ```

## 📊 Documentation Issues

### Swagger UI Blank Screen
**Symptoms**: `http://localhost/api-docs/` shows empty page

**Root Cause**: nginx proxy blocking asset requests to Swagger UI

**Solution**: Use direct backend access
```bash
# Direct access to backend Swagger UI
http://localhost:8080/api-docs/

# Or use frontend proxy (if configured)
http://localhost/api-docs/
```

### OpenAPI Spec Not Loading
**Symptoms**: Error fetching OpenAPI specification

**Solutions**:
1. **Check Spec Endpoint**:
   ```bash
   curl http://localhost:8080/api/openapi.json
   # Should return JSON specification
   ```

2. **Verify Swagger Dependencies**:
   ```bash
   docker compose exec backend npm list swagger-ui-express
   # Should show swagger-ui-express installed
   ```

3. **Check Express Routes**:
   ```javascript
   // Verify Swagger routes are registered
   app.use('/api-docs', swaggerUi.serve);
   app.get('/api-docs', swaggerUi.setup(swaggerSpec));
   ```

## 🗄️ Database Issues

### No Data in Database
**Symptoms**: API returns empty arrays, 404 for existing resources

**Solutions**:
1. **Check Database Population**:
   ```bash
   docker compose exec database psql -U flood_user -d flood_prediction -c "SELECT COUNT(*) FROM zones;"
   # Should return > 0
   ```

2. **Run Data Seeding**:
   ```bash
   docker compose exec backend npm run seed
   # Populates database with sample data
   ```

3. **Check Migration Status**:
   ```bash
   docker compose exec backend npm run migrate
   # Runs database schema migrations
   ```

### PostGIS Extensions Missing
**Symptoms**: Errors with spatial functions, ST_Contains not found

**Solutions**:
1. **Verify PostGIS Installation**:
   ```bash
   docker compose exec database psql -U flood_user -d flood_prediction -c "SELECT PostGIS_Version();"
   ```

2. **Manual Extension Creation**:
   ```bash
   docker compose exec database psql -U flood_user -d flood_prediction -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   ```

### Spatial Query Errors
**Symptoms**: Invalid geometry errors, coordinate system issues

**Solutions**:
1. **Check SRID Format**:
   ```sql
   -- Ensure geometries use SRID 4326 (WGS84)
   SELECT ST_SRID(geometry) FROM zones LIMIT 1;
   -- Should return 4326
   ```

2. **Validate GeoJSON**:
   ```bash
   # Validate GeoJSON format
   curl http://localhost:8080/api/zones | python3 -m json.tool
   ```

## 🔧 Performance Issues

### Slow API Responses
**Symptoms**: Requests taking > 5 seconds

**Solutions**:
1. **Check Database Indexes**:
   ```sql
   -- Verify spatial indexes exist
   \di+ idx_zones_geometry
   ```

2. **Monitor Resource Usage**:
   ```bash
   docker stats
   # Check CPU and memory usage
   ```

3. **Enable Query Logging**:
   ```bash
   docker compose exec backend npm run debug
   # Shows slow queries and performance metrics
   ```

### Memory Issues
**Symptoms**: Container crashes, out-of-memory errors

**Solutions**:
1. **Increase Docker Memory**:
   ```yaml
   # In docker-compose.yml
   services:
     backend:
       deploy:
         resources:
           memory: 1G
   ```

2. **Monitor Connection Pool**:
   ```javascript
   // Check connection pool status
   console.log('Active connections:', pool.totalCount - pool.idleCount);
   console.log('Idle connections:', pool.idleCount);
   ```

## 🧪 Testing Issues

### E2E Tests Fail
**Symptoms**: Test framework can't find elements, timeouts

**Solutions**:
1. **Wait for Services**:
   ```bash
   # Ensure all services are ready before testing
   docker compose up -d
   sleep 60  # Wait for full initialization
   npm run test
   ```

2. **Check Test URLs**:
   ```javascript
   // Verify test configuration matches service URLs
   const baseURL = 'http://localhost';  // Frontend URL
   const apiURL = 'http://localhost:8080';  // API URL
   ```

### API Testing Failures
**Symptoms**: curl commands return errors, unexpected responses

**Debugging Steps**:
1. **Verbose curl Output**:
   ```bash
   curl -v http://localhost:8080/health
   # Shows full request/response headers
   ```

2. **Check Response Headers**:
   ```bash
   curl -I http://localhost:8080/api/zones
   # Check Content-Type and status codes
   ```

3. **Test with Different Methods**:
   ```bash
   # Test POST endpoints with sample data
   curl -X POST http://localhost:8080/api/comms \
        -H "Content-Type: application/json" \
        -d '{"channel":"sms","from":"test","to":"test","message":"test"}'
   ```

## 🔄 Common Development Issues

### Hot Reload Not Working
**Symptoms**: Code changes not reflected in running container

**Solutions**:
1. **Check Volume Mounts**:
   ```yaml
   # In docker-compose.yml
   services:
     backend:
       volumes:
         - ./backend:/usr/src/app
         - /usr/src/app/node_modules
   ```

2. **Restart with --build**:
   ```bash
   docker compose up --build --force-recreate
   ```

### Port Conflicts
**Symptoms**: "Port already in use" errors

**Solutions**:
1. **Find Process Using Port**:
   ```bash
   lsof -i :8080
   # Shows process using port 8080
   ```

2. **Kill Conflicting Process**:
   ```bash
   kill -9 <PID>
   # Or use different port in docker-compose.yml
   ```

## 📋 Debugging Checklist

### API Health Check
```bash
# 1. Check service status
docker compose ps

# 2. Test health endpoint
curl http://localhost:8080/health

# 3. Check logs
docker compose logs backend

# 4. Test database connection
docker compose exec backend npm run test-db

# 5. Verify sample endpoint
curl http://localhost:8080/api/zones
```

### Frontend-API Communication
```bash
# 1. Test direct API access
curl http://localhost:8080/api/zones

# 2. Test through nginx proxy
curl http://localhost/api/zones

# 3. Check nginx configuration
docker compose exec frontend nginx -t

# 4. Test CORS preflight
curl -X OPTIONS http://localhost:8080/api/zones
```

## 🆘 Getting Help

### Log Analysis
```bash
# Real-time log monitoring
docker compose logs -f

# Specific service logs
docker compose logs backend
docker compose logs database

# Error-only logs
docker compose logs backend | grep ERROR
```

### Community Resources
1. **Documentation**: Check all docs in `/docs/api/` folder
2. **GitHub Issues**: Search for similar problems
3. **Docker Documentation**: Container and compose issues
4. **PostgreSQL Documentation**: Database and PostGIS questions

### Bug Report Template
When reporting issues, include:
1. **Environment**: Docker version, OS, browser
2. **Error Messages**: Full error logs and stack traces
3. **Steps to Reproduce**: Exact commands that trigger the issue
4. **Expected vs Actual**: What you expected vs what happened
5. **System Status**: Output of `docker compose ps` and health checks

---

**Last Updated**: 2025-11-13
**API Version**: v2.0.0
**Database Version**: PostgreSQL 15 + PostGIS 3.3