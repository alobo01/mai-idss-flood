FROM node:20-alpine
WORKDIR /srv

# Install curl for health checks
RUN apk add --no-cache curl

# Copy package files first for better cache layering
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Copy OpenAPI specification
COPY openapi.yaml ./

# Make sure healthcheck is executable
RUN chmod +x ./healthcheck.sh

EXPOSE 18080

# Use healthcheck for Docker
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ./healthcheck.sh

CMD ["node","server.js"]
