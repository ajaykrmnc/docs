# Docker Networking, Storage, and Compose: Complete Guide

## Table of Contents

1. [Docker Networking](#docker-networking)
2. [Docker Storage](#docker-storage)
3. [Docker Compose](#docker-compose)
4. [Advanced Configurations](#advanced-configurations)
5. [Production Best Practices](#production-best-practices)

---

## 1. Docker Networking

### 1.1 Network Drivers Overview

Docker provides several network drivers for different use cases:

| Driver | Description | Use Case |
|--------|-------------|----------|
| **bridge** | Default network driver | Single-host containers |
| **host** | Remove network isolation | Performance-critical apps |
| **overlay** | Multi-host networking | Swarm services |
| **macvlan** | Assign MAC address | Legacy apps needing direct network access |
| **none** | Disable networking | Isolated containers |
| **ipvlan** | Control over IPv4/IPv6 | Advanced networking |

### 1.2 Bridge Network (Default)

The default network driver for containers on a single host.

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                         │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │         docker0 Bridge (172.17.0.1)              │   │
│  └──────────────────────────────────────────────────┘   │
│         │                    │                          │
│    ┌────────┐          ┌────────┐                       │
│    │ veth0  │          │ veth1  │                       │
│    └────────┘          └────────┘                       │
│         │                    │                          │
│  ┌─────────────┐      ┌─────────────┐                   │
│  │ Container 1 │      │ Container 2 │                   │
│  │ 172.17.0.2  │      │ 172.17.0.3  │                   │
│  └─────────────┘      └─────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

**Default Bridge Network:**
```bash
# Containers on default bridge
docker run -d --name web1 nginx
docker run -d --name web2 nginx

# Containers can communicate by IP
docker exec web1 ping 172.17.0.3

# But NOT by name (no automatic DNS)
docker exec web1 ping web2  # Fails
```

**Custom Bridge Network:**
```bash
# Create custom bridge network
docker network create mynetwork

# Run containers on custom network
docker run -d --name web1 --network mynetwork nginx
docker run -d --name web2 --network mynetwork nginx

# Containers can communicate by name (automatic DNS)
docker exec web1 ping web2  # Works!

# Inspect network
docker network inspect mynetwork
```

**Bridge Network Configuration:**
```bash
# Create with custom subnet
docker network create \
  --driver bridge \
  --subnet 192.168.100.0/24 \
  --gateway 192.168.100.1 \
  --ip-range 192.168.100.128/25 \
  mynetwork

# Create with options
docker network create \
  --driver bridge \
  --opt "com.docker.network.bridge.name"="br-custom" \
  --opt "com.docker.network.bridge.enable_icc"="true" \
  --opt "com.docker.network.bridge.enable_ip_masquerade"="true" \
  mynetwork
```

**Connecting Containers:**
```bash
# Connect running container to network
docker network connect mynetwork web3

# Disconnect from network
docker network disconnect mynetwork web3

# Connect with specific IP
docker network connect --ip 192.168.100.50 mynetwork web4

# Connect with alias
docker network connect --alias webserver mynetwork web5
```

### 1.3 Host Network

Removes network isolation between container and host.

```bash
# Run with host network
docker run -d --network host nginx

# Container uses host's network stack
# No port mapping needed
# Container listens on host's ports directly
```

**Characteristics:**
- **Performance**: No network translation overhead
- **Port conflicts**: Container ports must not conflict with host
- **No isolation**: Container sees all host network interfaces
- **Use case**: High-performance networking, network monitoring tools

**Example:**
```bash
# Container binds to host's port 80
docker run -d --network host nginx

# Access directly on host
curl http://localhost:80
```

### 1.4 Overlay Network

Enables multi-host networking for Swarm services.

```bash
# Create overlay network (requires Swarm mode)
docker network create \
  --driver overlay \
  --attachable \
  myoverlay

# Deploy service on overlay network
docker service create \
  --name web \
  --network myoverlay \
  --replicas 3 \
  nginx
```

**Architecture:**
```
Host 1                          Host 2
┌─────────────────┐            ┌─────────────────┐
│  Container A    │            │  Container B    │
│  10.0.0.2       │            │  10.0.0.3       │
└─────────────────┘            └─────────────────┘
        │                              │
   ┌────────────┐                 ┌────────────┐
   │  Overlay   │←────VXLAN───────→│  Overlay   │
   │  Network   │                 │  Network   │
   └────────────┘                 └────────────┘
        │                              │
   Physical Network              Physical Network
```

**Features:**
- Spans multiple Docker hosts
- Encrypted by default (with `--opt encrypted`)
- Automatic service discovery
- Load balancing

### 1.5 Macvlan Network

Assigns MAC address to container, making it appear as physical device.

```bash
# Create macvlan network
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 \
  mymacvlan

# Run container with macvlan
docker run -d \
  --network mymacvlan \
  --ip 192.168.1.100 \
  nginx
```

**Use Cases:**
- Legacy applications expecting direct network access
- Network monitoring tools
- Applications requiring specific MAC addresses

### 1.6 Network Commands

```bash
# List networks
docker network ls

# Create network
docker network create mynetwork

# Inspect network
docker network inspect mynetwork

# Remove network
docker network rm mynetwork

# Remove unused networks
docker network prune

# Connect container to network
docker network connect mynetwork container_name

# Disconnect container from network
docker network disconnect mynetwork container_name
```

### 1.7 DNS and Service Discovery

**Automatic DNS in Custom Networks:**

```bash
# Create network
docker network create myapp

# Run containers
docker run -d --name db --network myapp postgres
docker run -d --name web --network myapp nginx
docker run -d --name api --network myapp node:18

# Containers can resolve each other by name
docker exec web ping db
docker exec api curl http://web
```

**DNS Configuration:**

```bash
# Custom DNS servers
docker run --dns 8.8.8.8 --dns 8.8.4.4 nginx

# Custom DNS search domains
docker run --dns-search example.com nginx

# Add host entries
docker run --add-host db:192.168.1.100 nginx

# Hostname
docker run --hostname mycontainer nginx
```

### 1.8 Port Publishing

**Port Mapping Syntax:**

```bash
# Map container port to host port
docker run -p 8080:80 nginx
# Host:8080 → Container:80

# Map to specific host interface
docker run -p 127.0.0.1:8080:80 nginx
# Only accessible on localhost

# Map to random host port
docker run -P nginx
# Docker assigns random port

# Map multiple ports
docker run -p 80:80 -p 443:443 nginx

# Map UDP port
docker run -p 53:53/udp dns-server

# Map range of ports
docker run -p 8000-8010:8000-8010 myapp
```

**Viewing Port Mappings:**

```bash
# Show port mappings
docker port container_name

# Inspect specific port
docker port container_name 80

# Using inspect
docker inspect --format='{{json .NetworkSettings.Ports}}' container_name | jq
```

### 1.9 Network Security

**Network Isolation:**

```bash
# Create isolated networks
docker network create frontend
docker network create backend

# Web server on both networks
docker run -d --name web \
  --network frontend \
  nginx

docker network connect backend web

# Database only on backend
docker run -d --name db \
  --network backend \
  postgres

# App server only on backend
docker run -d --name app \
  --network backend \
  myapp
```

**Internal Networks:**

```bash
# Create internal network (no external access)
docker network create --internal backend

# Containers can communicate internally
# But cannot reach external networks
```

**Encrypted Overlay Networks:**

```bash
# Create encrypted overlay network
docker network create \
  --driver overlay \
  --opt encrypted \
  secure-network
```

---

## 2. Docker Storage

### 2.1 Storage Types

Docker provides three ways to persist data:

| Type | Description | Use Case |
|------|-------------|----------|
| **Volumes** | Managed by Docker | Preferred for persistence |
| **Bind Mounts** | Mount host directory | Development, config files |
| **tmpfs** | Stored in memory | Temporary data, secrets |

**Storage Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    Host Filesystem                      │
│                                                         │
│  /var/lib/docker/volumes/                               │
│  ├── myvolume/                                          │
│  │   └── _data/          ← Docker-managed volume        │
│  │                                                      │
│  /home/user/app/          ← Bind mount source           │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Container                            │
│                                                         │
│  /data                  ← Volume mount point            │
│  /app                   ← Bind mount point              │
│  /tmp                   ← tmpfs mount                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Volumes

Docker-managed storage, preferred for production.

**Creating and Using Volumes:**

```bash
# Create volume
docker volume create mydata

# List volumes
docker volume ls

# Inspect volume
docker volume inspect mydata

# Remove volume
docker volume rm mydata

# Remove unused volumes
docker volume prune

# Run container with volume
docker run -d \
  --name db \
  -v mydata:/var/lib/postgresql/data \
  postgres

# Anonymous volume (created automatically)
docker run -d -v /data nginx

# Read-only volume
docker run -d -v mydata:/data:ro nginx
```

**Volume Drivers:**

```bash
# Local driver (default)
docker volume create --driver local myvolume

# NFS volume
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.100,rw \
  --opt device=:/path/to/dir \
  nfs-volume

# Create volume with options
docker volume create \
  --driver local \
  --opt type=none \
  --opt device=/mnt/data \
  --opt o=bind \
  myvolume
```

**Volume Backup and Restore:**

```bash
# Backup volume
docker run --rm \
  -v mydata:/data \
  -v $(pwd):/backup \
  ubuntu \
  tar czf /backup/mydata-backup.tar.gz /data

# Restore volume
docker run --rm \
  -v mydata:/data \
  -v $(pwd):/backup \
  ubuntu \
  tar xzf /backup/mydata-backup.tar.gz -C /
```

### 2.3 Bind Mounts

Mount host directory or file into container.

```bash
# Mount directory
docker run -d \
  -v /host/path:/container/path \
  nginx

# Using --mount (more explicit)
docker run -d \
  --mount type=bind,source=/host/path,target=/container/path \
  nginx

# Read-only bind mount
docker run -d \
  -v /host/path:/container/path:ro \
  nginx

# Mount single file
docker run -d \
  -v /host/config.json:/app/config.json \
  myapp

# Mount with specific permissions
docker run -d \
  --mount type=bind,source=/host/path,target=/container/path,readonly \
  nginx
```

**Bind Mount Use Cases:**

1. **Development**: Live code updates
```bash
docker run -d \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/package.json:/app/package.json \
  node:18
```

2. **Configuration**: Inject config files
```bash
docker run -d \
  -v /etc/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx
```

3. **Logs**: Access logs on host
```bash
docker run -d \
  -v /var/log/myapp:/var/log/app \
  myapp
```

### 2.4 tmpfs Mounts

Store data in host memory (not persisted).

```bash
# Create tmpfs mount
docker run -d \
  --tmpfs /tmp \
  nginx

# Using --mount
docker run -d \
  --mount type=tmpfs,target=/tmp,tmpfs-size=100m \
  nginx

# Multiple tmpfs mounts
docker run -d \
  --tmpfs /tmp \
  --tmpfs /run \
  nginx
```

**Use Cases:**
- Temporary files
- Sensitive data (not written to disk)
- Performance-critical temporary storage
- Secrets that shouldn't persist

### 2.5 Storage Best Practices

**1. Use Volumes for Persistence:**

```bash
# Good: Named volume
docker run -d -v postgres-data:/var/lib/postgresql/data postgres

# Avoid: Storing data in container layer
docker run -d postgres  # Data lost when container removed
```

**2. Use Bind Mounts for Development:**

```bash
# Development
docker run -d \
  -v $(pwd):/app \
  -v /app/node_modules \
  node:18

# Production: Use volumes or COPY in Dockerfile
```

**3. Clean Up Unused Volumes:**

```bash
# Remove unused volumes
docker volume prune

# Remove specific volume
docker volume rm myvolume

# Remove volume with container
docker rm -v container_name
```

**4. Backup Important Data:**

```bash
# Regular backups
docker run --rm \
  -v mydata:/data \
  -v $(pwd):/backup \
  ubuntu \
  tar czf /backup/backup-$(date +%Y%m%d).tar.gz /data
```

---

## 3. Docker Compose

Docker Compose is a tool for defining and running multi-container applications.

### 3.1 Compose File Structure

**Basic docker-compose.yml:**

```yaml
version: '3.8'

services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html
    networks:
      - frontend
    depends_on:
      - api

  api:
    build: ./api
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DB_HOST=db
    networks:
      - frontend
      - backend
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=myapp
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - backend

networks:
  frontend:
  backend:

volumes:
  db-data:
```

### 3.2 Service Configuration

**Image and Build:**

```yaml
services:
  # Using pre-built image
  web:
    image: nginx:1.23

  # Building from Dockerfile
  app:
    build: .

  # Build with context and Dockerfile
  api:
    build:
      context: ./api
      dockerfile: Dockerfile.prod
      args:
        - NODE_VERSION=18
        - BUILD_ENV=production
      target: production
      cache_from:
        - myapp:latest
```

**Ports:**

```yaml
services:
  web:
    ports:
      # HOST:CONTAINER
      - "8080:80"

      # Specific interface
      - "127.0.0.1:8080:80"

      # Random host port
      - "80"

      # UDP port
      - "53:53/udp"

      # Port range
      - "8000-8010:8000-8010"
```

**Environment Variables:**

```yaml
services:
  app:
    environment:
      # Key-value pairs
      - NODE_ENV=production
      - DEBUG=false
      - API_KEY=secret123

    # Or as object
    environment:
      NODE_ENV: production
      DEBUG: "false"

    # From .env file
    env_file:
      - .env
      - .env.production
```

**Volumes:**

```yaml
services:
  app:
    volumes:
      # Named volume
      - data:/app/data

      # Bind mount
      - ./src:/app/src

      # Read-only
      - ./config:/app/config:ro

      # tmpfs
      - type: tmpfs
        target: /tmp

      # Long syntax
      - type: volume
        source: data
        target: /app/data
        volume:
          nocopy: true

volumes:
  data:
```

**Networks:**

```yaml
services:
  web:
    networks:
      - frontend
      - backend

  # With aliases
  api:
    networks:
      frontend:
        aliases:
          - api-server
      backend:
        ipv4_address: 172.16.238.10

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.16.238.0/24
```

**Dependencies:**

```yaml
services:
  web:
    depends_on:
      - api
      - cache

  # With conditions (Compose v3.8+)
  api:
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
```

**Health Checks:**

```yaml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Resource Limits:**

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

**Restart Policies:**

```yaml
services:
  app:
    restart: always
    # Options: no, always, on-failure, unless-stopped
```

### 3.3 Compose Commands

```bash
# Start services
docker-compose up

# Start in detached mode
docker-compose up -d

# Build images before starting
docker-compose up --build

# Start specific services
docker-compose up web api

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove containers, volumes, and images
docker-compose down -v --rmi all

# View logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Logs for specific service
docker-compose logs web

# List containers
docker-compose ps

# Execute command in service
docker-compose exec web bash

# Run one-off command
docker-compose run web python manage.py migrate

# Scale services
docker-compose up -d --scale web=3

# Validate compose file
docker-compose config

# View config with resolved values
docker-compose config --resolve-image-digests
```

### 3.4 Real-World Compose Examples

**Example 1: Web Application Stack**

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static-content:/usr/share/nginx/html
    depends_on:
      - web
    networks:
      - frontend
    restart: unless-stopped

  web:
    build:
      context: ./app
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
      - REDIS_URL=redis://cache:6379
      - SECRET_KEY_FILE=/run/secrets/secret_key
    volumes:
      - ./app:/app
      - static-content:/app/static
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    networks:
      - frontend
      - backend
    secrets:
      - secret_key
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
      - POSTGRES_DB=myapp
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5
    secrets:
      - db_password
    restart: unless-stopped

  cache:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    networks:
      - backend
    restart: unless-stopped

  worker:
    build:
      context: ./app
      dockerfile: Dockerfile
    command: celery -A app worker -l info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache
    networks:
      - backend
    restart: unless-stopped

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

volumes:
  postgres-data:
  redis-data:
  static-content:

secrets:
  secret_key:
    file: ./secrets/secret_key.txt
  db_password:
    file: ./secrets/db_password.txt
```

**Example 2: Microservices Architecture**

```yaml
version: '3.8'

services:
  api-gateway:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./gateway.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - user-service
      - product-service
      - order-service
    networks:
      - frontend

  user-service:
    build: ./services/user
    environment:
      - DB_HOST=user-db
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - user-db
      - kafka
    networks:
      - frontend
      - user-backend
    deploy:
      replicas: 2

  product-service:
    build: ./services/product
    environment:
      - DB_HOST=product-db
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - product-db
      - kafka
    networks:
      - frontend
      - product-backend

  order-service:
    build: ./services/order
    environment:
      - DB_HOST=order-db
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - order-db
      - kafka
    networks:
      - frontend
      - order-backend

  user-db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=users
      - POSTGRES_PASSWORD=secret
    volumes:
      - user-db-data:/var/lib/postgresql/data
    networks:
      - user-backend

  product-db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=products
      - POSTGRES_PASSWORD=secret
    volumes:
      - product-db-data:/var/lib/postgresql/data
    networks:
      - product-backend

  order-db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=orders
      - POSTGRES_PASSWORD=secret
    volumes:
      - order-db-data:/var/lib/postgresql/data
    networks:
      - order-backend

  kafka:
    image: confluentinc/cp-kafka:latest
    environment:
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
    depends_on:
      - zookeeper
    networks:
      - user-backend
      - product-backend
      - order-backend

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      - ZOOKEEPER_CLIENT_PORT=2181
    networks:
      - user-backend
      - product-backend
      - order-backend

networks:
  frontend:
  user-backend:
    internal: true
  product-backend:
    internal: true
  order-backend:
    internal: true

volumes:
  user-db-data:
  product-db-data:
  order-db-data:
```

**Example 3: Development Environment**

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      target: development
    volumes:
      # Live code reload
      - ./src:/app/src
      - ./package.json:/app/package.json
      - ./package-lock.json:/app/package-lock.json
      # Prevent overwriting node_modules
      - /app/node_modules
    ports:
      - "3000:3000"
      - "9229:9229"  # Node.js debugger
    environment:
      - NODE_ENV=development
      - DEBUG=*
    command: npm run dev
    depends_on:
      - db
      - mailhog
    networks:
      - dev

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=dev
      - POSTGRES_USER=dev
      - POSTGRES_PASSWORD=dev
    ports:
      - "5432:5432"  # Expose for local tools
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - dev

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - dev

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
    networks:
      - dev

  adminer:
    image: adminer
    ports:
      - "8080:8080"
    environment:
      - ADMINER_DEFAULT_SERVER=db
    networks:
      - dev

networks:
  dev:

volumes:
  postgres-data:
```

### 3.5 Environment Variables and Secrets

**Using .env File:**

```bash
# .env file
POSTGRES_VERSION=15
POSTGRES_PASSWORD=secret123
APP_PORT=3000
NODE_ENV=production
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:${POSTGRES_VERSION}
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

  app:
    build: .
    ports:
      - "${APP_PORT}:3000"
    environment:
      - NODE_ENV=${NODE_ENV}
```

**Multiple Environment Files:**

```yaml
services:
  app:
    env_file:
      - .env
      - .env.local
      - .env.${NODE_ENV}
```

**Secrets (Swarm Mode):**

```yaml
version: '3.8'

services:
  app:
    image: myapp
    secrets:
      - db_password
      - api_key
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
      - API_KEY_FILE=/run/secrets/api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true
```

### 3.6 Extending and Overriding

**Base Configuration:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    image: nginx
    volumes:
      - ./html:/usr/share/nginx/html
```

**Override for Development:**

```yaml
# docker-compose.override.yml (automatically loaded)
version: '3.8'

services:
  web:
    ports:
      - "8080:80"
    environment:
      - DEBUG=true
```

**Production Override:**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    ports:
      - "80:80"
    environment:
      - DEBUG=false
    restart: always
```

```bash
# Use production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Extending Services:**

```yaml
# common.yml
version: '3.8'

x-common-variables: &common-variables
  ENVIRONMENT: production
  LOG_LEVEL: info

x-common-healthcheck: &common-healthcheck
  interval: 30s
  timeout: 10s
  retries: 3

services:
  base-service:
    image: mybase
    environment: *common-variables
    healthcheck: *common-healthcheck
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    extends:
      file: common.yml
      service: base-service
    ports:
      - "80:80"
```

---

## 4. Advanced Configurations

### 4.1 Container Resource Management

**CPU Limits:**

```yaml
services:
  app:
    image: myapp
    deploy:
      resources:
        limits:
          cpus: '2.0'
        reservations:
          cpus: '1.0'

    # Or using runtime flags
    cpus: 1.5
    cpu_shares: 1024
    cpuset: "0,1"
```

**Memory Limits:**

```yaml
services:
  app:
    image: myapp
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

    # Or using runtime flags
    mem_limit: 1g
    mem_reservation: 512m
    memswap_limit: 2g
```

**I/O Limits:**

```yaml
services:
  app:
    image: myapp
    blkio_config:
      weight: 500
      device_read_bps:
        - path: /dev/sda
          rate: '10mb'
      device_write_bps:
        - path: /dev/sda
          rate: '5mb'
```

### 4.2 Logging Configuration

**Logging Drivers:**

```yaml
services:
  app:
    image: myapp
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        labels: "production"

  # Syslog
  web:
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://192.168.1.100:514"
        tag: "web"

  # Fluentd
  api:
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: api.{{.Name}}
```

### 4.3 Security Configurations

**User and Permissions:**

```yaml
services:
  app:
    image: myapp
    user: "1000:1000"

  # Read-only root filesystem
  secure-app:
    image: myapp
    read_only: true
    tmpfs:
      - /tmp
      - /run
```

**Capabilities:**

```yaml
services:
  app:
    image: myapp
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
      - CHOWN
```

**Security Options:**

```yaml
services:
  app:
    image: myapp
    security_opt:
      - no-new-privileges:true
      - apparmor:docker-default
      - seccomp:./seccomp-profile.json
```

### 4.4 Advanced Networking

**Custom Network Configuration:**

```yaml
networks:
  frontend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-frontend
      com.docker.network.bridge.enable_icc: "true"
    ipam:
      driver: default
      config:
        - subnet: 172.28.0.0/16
          ip_range: 172.28.5.0/24
          gateway: 172.28.0.1
          aux_addresses:
            host1: 172.28.1.5
            host2: 172.28.1.6
    labels:
      com.example.description: "Frontend network"
```

**IPv6 Support:**

```yaml
networks:
  app-network:
    enable_ipv6: true
    ipam:
      config:
        - subnet: 172.28.0.0/16
        - subnet: 2001:db8:1::/64
```

---

## 5. Production Best Practices

### 5.1 High Availability

**Health Checks:**

```yaml
services:
  web:
    image: nginx
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Restart Policies:**

```yaml
services:
  app:
    image: myapp
    restart: unless-stopped
    # Options: no, always, on-failure, unless-stopped

  critical-service:
    image: critical
    restart: always
    deploy:
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
```

### 5.2 Monitoring and Observability

**Prometheus and Grafana:**

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

  node-exporter:
    image: prom/node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'

volumes:
  prometheus-data:
  grafana-data:
```

### 5.3 Backup and Disaster Recovery

**Automated Backups:**

```yaml
services:
  backup:
    image: postgres:15-alpine
    volumes:
      - ./backups:/backups
      - db-data:/var/lib/postgresql/data:ro
    environment:
      - PGPASSWORD=secret
    command: >
      sh -c "while true; do
        pg_dump -h db -U user myapp > /backups/backup-$$(date +%Y%m%d-%H%M%S).sql;
        find /backups -name 'backup-*.sql' -mtime +7 -delete;
        sleep 86400;
      done"
    depends_on:
      - db
```

### 5.4 Performance Optimization

**Build Cache:**

```yaml
services:
  app:
    build:
      context: .
      cache_from:
        - myapp:latest
        - myapp:cache
```

**Resource Allocation:**

```yaml
services:
  app:
    image: myapp
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## Summary

### Key Takeaways

**Networking:**
- Use custom bridge networks for container communication
- Leverage automatic DNS for service discovery
- Implement network isolation for security
- Choose appropriate network driver for use case

**Storage:**
- Prefer volumes over bind mounts for production
- Use bind mounts for development
- Implement regular backup strategies
- Clean up unused volumes

**Docker Compose:**
- Define infrastructure as code
- Use environment variables for configuration
- Implement health checks
- Follow security best practices
- Monitor and log appropriately

### Next Steps

- Practice with real-world applications
- Implement CI/CD pipelines
- Explore container orchestration (Kubernetes, Docker Swarm)
- Study security hardening
- Learn performance tuning
- Implement monitoring and logging

---

**Document Version**: 1.0
**Last Updated**: 2026-03-26


