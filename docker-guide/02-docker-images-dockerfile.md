# Docker Images and Dockerfile: Complete Guide

## Table of Contents

1. [Understanding Docker Images](#understanding-docker-images)
2. [Dockerfile Syntax](#dockerfile-syntax)
3. [Building Images](#building-images)
4. [Multi-Stage Builds](#multi-stage-builds)
5. [Image Optimization](#image-optimization)
6. [Best Practices](#best-practices)
7. [Image Management](#image-management)
8. [Registry Operations](#registry-operations)

---

## 1. Understanding Docker Images

### 1.1 What is a Docker Image?

A Docker image is a read-only template containing:
- Application code
- Runtime environment
- Libraries and dependencies
- Environment variables
- Configuration files
- Metadata

**Image Characteristics:**
- **Immutable**: Cannot be changed once created
- **Layered**: Built from multiple layers
- **Portable**: Can run on any Docker host
- **Versioned**: Tagged for version control
- **Shareable**: Stored in registries

### 1.2 Image Layers

Images are composed of layers stacked on top of each other:

```
┌─────────────────────────────────────┐
│  Layer 5: CMD ["python", "app.py"]  │  ← Metadata layer (0 bytes)
├─────────────────────────────────────┤
│  Layer 4: COPY app.py /app/         │  ← Application code (1 MB)
├─────────────────────────────────────┤
│  Layer 3: RUN pip install flask     │  ← Dependencies (50 MB)
├─────────────────────────────────────┤
│  Layer 2: RUN apt-get install py... │  ← Python runtime (100 MB)
├─────────────────────────────────────┤
│  Layer 1: FROM ubuntu:22.04         │  ← Base OS (80 MB)
└─────────────────────────────────────┘
Total: ~231 MB
```

**Layer Benefits:**
- **Caching**: Unchanged layers are reused
- **Sharing**: Multiple images share common layers
- **Efficiency**: Only changed layers need to be transferred
- **Speed**: Faster builds and deployments

### 1.3 Image Naming and Tagging

**Image Name Format:**
```
[registry/][namespace/]repository[:tag][@digest]

Examples:
nginx                           # Official image, latest tag
nginx:1.23                      # Specific version
ubuntu:22.04                    # Ubuntu version
myregistry.com/myapp:v1.0      # Private registry
docker.io/library/nginx:latest  # Full format
nginx@sha256:abc123...          # By digest
```

**Components:**
- **Registry**: Where image is stored (default: docker.io)
- **Namespace**: User or organization (default: library for official)
- **Repository**: Image name
- **Tag**: Version identifier (default: latest)
- **Digest**: SHA256 hash of image content

### 1.4 Image Manifest

The manifest describes the image structure:

```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
  "config": {
    "mediaType": "application/vnd.docker.container.image.v1+json",
    "size": 7023,
    "digest": "sha256:abc123..."
  },
  "layers": [
    {
      "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
      "size": 2802957,
      "digest": "sha256:def456..."
    },
    {
      "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
      "size": 1234567,
      "digest": "sha256:ghi789..."
    }
  ]
}
```

---

## 2. Dockerfile Syntax

### 2.1 Basic Structure

A Dockerfile is a text file with instructions to build an image:

```dockerfile
# Comment
INSTRUCTION arguments
```

**Example Dockerfile:**

```dockerfile
# Use official Python runtime as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variable
ENV FLASK_APP=app.py

# Define default command
CMD ["python", "app.py"]
```

### 2.2 Dockerfile Instructions

#### FROM - Base Image

Specifies the base image to build upon.

```dockerfile
# Official image
FROM ubuntu:22.04

# Specific version
FROM python:3.11-slim

# Multi-stage build
FROM golang:1.20 AS builder

# Scratch (empty base)
FROM scratch
```

**Best Practices:**
- Use official images when possible
- Specify exact versions (not `latest`)
- Use minimal base images (alpine, slim)
- Consider security and size

#### RUN - Execute Commands

Executes commands during image build.

```dockerfile
# Shell form (runs in /bin/sh -c)
RUN apt-get update && apt-get install -y nginx

# Exec form (doesn't invoke shell)
RUN ["apt-get", "update"]

# Multiple commands
RUN apt-get update && \
    apt-get install -y \
        package1 \
        package2 \
        package3 && \
    rm -rf /var/lib/apt/lists/*

# Change shell
SHELL ["/bin/bash", "-c"]
RUN source ~/.bashrc && echo $PATH
```

**Best Practices:**
- Combine related commands to reduce layers
- Clean up in same layer (remove cache, temp files)
- Use `&&` to chain commands
- Add `\` for readability

#### COPY - Copy Files

Copies files from build context to image.

```dockerfile
# Copy single file
COPY app.py /app/

# Copy directory
COPY ./src /app/src

# Copy multiple files
COPY file1.txt file2.txt /app/

# Copy with wildcards
COPY *.py /app/

# Copy and rename
COPY config.json /app/config/app-config.json

# Copy with ownership
COPY --chown=user:group app.py /app/

# Preserve timestamps
COPY --chown=1000:1000 --chmod=755 script.sh /usr/local/bin/
```

**COPY vs ADD:**
- Use `COPY` for simple file copying
- Use `ADD` for auto-extraction of tar files or remote URLs
- `COPY` is more transparent and preferred

#### ADD - Advanced Copy

Similar to COPY but with additional features.

```dockerfile
# Copy file (same as COPY)
ADD app.py /app/

# Auto-extract tar archive
ADD archive.tar.gz /app/

# Download from URL (not recommended)
ADD https://example.com/file.txt /app/

# Copy with ownership
ADD --chown=user:group app.py /app/
```

**When to use ADD:**
- Extracting local tar archives
- Otherwise, prefer COPY

#### CMD - Default Command

Specifies the default command to run when container starts.

```dockerfile
# Exec form (preferred)
CMD ["python", "app.py"]

# Shell form
CMD python app.py

# As parameters to ENTRYPOINT
CMD ["--port", "8000"]
```

**Important:**
- Only last CMD in Dockerfile takes effect
- Can be overridden at runtime: `docker run myimage python other.py`
- Exec form doesn't invoke shell (no variable substitution)

#### ENTRYPOINT - Container Executable

Configures container to run as an executable.

```dockerfile
# Exec form
ENTRYPOINT ["python", "app.py"]

# Shell form
ENTRYPOINT python app.py

# Combined with CMD
ENTRYPOINT ["python", "app.py"]
CMD ["--port", "8000"]
```

**ENTRYPOINT vs CMD:**

```dockerfile
# CMD only - can be completely overridden
CMD ["python", "app.py"]
# docker run myimage ls  → runs ls

# ENTRYPOINT only - always runs
ENTRYPOINT ["python", "app.py"]
# docker run myimage ls  → runs python app.py ls

# ENTRYPOINT + CMD - CMD provides defaults
ENTRYPOINT ["python", "app.py"]
CMD ["--port", "8000"]
# docker run myimage  → python app.py --port 8000
# docker run myimage --port 9000  → python app.py --port 9000
```

#### ENV - Environment Variables

Sets environment variables.

```dockerfile
# Single variable
ENV NODE_ENV=production

# Multiple variables
ENV NODE_ENV=production \
    PORT=8000 \
    LOG_LEVEL=info

# Using in subsequent instructions
ENV APP_HOME=/app
WORKDIR $APP_HOME
COPY . $APP_HOME
```

**Best Practices:**
- Use for configuration
- Can be overridden at runtime: `docker run -e PORT=9000`
- Available to all subsequent instructions

#### WORKDIR - Working Directory

Sets the working directory for subsequent instructions.

```dockerfile
# Set working directory
WORKDIR /app

# Creates directory if it doesn't exist
WORKDIR /app/src

# Can use environment variables
ENV APP_DIR=/application
WORKDIR $APP_DIR

# Relative paths
WORKDIR /app
WORKDIR src  # Now in /app/src
```

**Best Practices:**
- Use absolute paths
- Prefer WORKDIR over `RUN cd /app`
- Creates directory automatically

#### EXPOSE - Document Ports

Documents which ports the container listens on.

```dockerfile
# Single port
EXPOSE 80

# Multiple ports
EXPOSE 80 443

# UDP port
EXPOSE 53/udp

# TCP and UDP
EXPOSE 8080/tcp 8080/udp
```

**Important:**
- Documentary only, doesn't actually publish ports
- Use `-p` flag to publish: `docker run -p 80:80`
- Use `-P` to publish all exposed ports to random host ports

#### VOLUME - Mount Points

Creates a mount point for external volumes.

```dockerfile
# Single volume
VOLUME /data

# Multiple volumes
VOLUME ["/data", "/logs"]

# With path
VOLUME /var/lib/mysql
```

**Characteristics:**
- Data persists beyond container lifecycle
- Can be shared between containers
- Better performance than bind mounts on Docker Desktop

#### USER - Set User

Sets the user (and optionally group) for subsequent instructions.

```dockerfile
# By name
USER appuser

# By UID
USER 1000

# User and group
USER appuser:appgroup

# UID and GID
USER 1000:1000

# Create user first
RUN useradd -m -u 1000 appuser
USER appuser
```

**Security Best Practice:**
- Always run as non-root user
- Create user in Dockerfile
- Use numeric UID for better portability

#### ARG - Build Arguments

Defines build-time variables.

```dockerfile
# Define argument
ARG VERSION=1.0

# Use in FROM
ARG BASE_IMAGE=ubuntu:22.04
FROM $BASE_IMAGE

# Use in RUN
ARG PYTHON_VERSION=3.11
RUN apt-get install -y python${PYTHON_VERSION}

# With default value
ARG BUILD_DATE=unknown
LABEL build_date=$BUILD_DATE
```

**Usage:**
```bash
# Pass at build time
docker build --build-arg VERSION=2.0 .
docker build --build-arg PYTHON_VERSION=3.10 .
```

**ARG vs ENV:**
- ARG: Available only during build
- ENV: Available during build and runtime
- ARG values not persisted in final image

#### LABEL - Metadata

Adds metadata to image.

```dockerfile
# Single label
LABEL version="1.0"

# Multiple labels
LABEL maintainer="dev@example.com" \
      description="My application" \
      version="1.0"

# Using variables
ARG VERSION=1.0
LABEL version=$VERSION

# Standard labels
LABEL org.opencontainers.image.title="My App" \
      org.opencontainers.image.version="1.0" \
      org.opencontainers.image.authors="dev@example.com"
```

#### HEALTHCHECK - Container Health

Defines how to test if container is healthy.

```dockerfile
# HTTP health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# Custom script
HEALTHCHECK CMD /app/healthcheck.sh

# Disable inherited healthcheck
HEALTHCHECK NONE
```

**Options:**
- `--interval`: Time between checks (default: 30s)
- `--timeout`: Max time for check (default: 30s)
- `--start-period`: Grace period (default: 0s)
- `--retries`: Consecutive failures needed (default: 3)

#### SHELL - Default Shell

Changes the default shell for shell form of RUN, CMD, ENTRYPOINT.

```dockerfile
# Use bash instead of sh
SHELL ["/bin/bash", "-c"]

# Windows example
SHELL ["powershell", "-command"]

# With options
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
```

#### ONBUILD - Trigger Instructions

Adds trigger instruction executed when image is used as base.

```dockerfile
# In base image
ONBUILD COPY . /app
ONBUILD RUN npm install

# When someone uses this as base:
FROM mybase
# ONBUILD instructions execute here automatically
```

**Use Cases:**
- Creating base images for teams
- Enforcing standards
- Automating common tasks

#### STOPSIGNAL - Stop Signal

Sets the signal to stop container.

```dockerfile
# Use SIGTERM (default)
STOPSIGNAL SIGTERM

# Use SIGINT
STOPSIGNAL SIGINT

# Numeric value
STOPSIGNAL 15
```

---

## 3. Building Images

### 3.1 Build Context

The build context is the set of files sent to Docker daemon for building.

```
project/
├── Dockerfile
├── .dockerignore
├── app.py
├── requirements.txt
├── static/
│   └── style.css
└── tests/
    └── test_app.py
```

**Build Command:**
```bash
# Build from current directory
docker build .

# Build with tag
docker build -t myapp:1.0 .

# Build with multiple tags
docker build -t myapp:1.0 -t myapp:latest .

# Build from different directory
docker build -t myapp /path/to/context

# Build from URL
docker build -t myapp https://github.com/user/repo.git

# Build from stdin
docker build -t myapp - < Dockerfile

# Build with specific Dockerfile
docker build -f Dockerfile.prod -t myapp:prod .
```

### 3.2 .dockerignore File

Excludes files from build context.

```
# .dockerignore

# Version control
.git
.gitignore
.gitattributes

# Dependencies
node_modules
vendor
__pycache__
*.pyc

# Build artifacts
dist
build
*.o
*.so

# IDE
.vscode
.idea
*.swp

# Documentation
README.md
docs/

# Tests
tests/
*.test.js

# Environment files
.env
.env.local
*.key
*.pem

# Logs
*.log
logs/

# OS files
.DS_Store
Thumbs.db

# Temporary files
tmp/
temp/
*.tmp

# Allow specific files
!important.log
```

**Benefits:**
- Faster builds (smaller context)
- Smaller images (if using COPY . .)
- Better security (exclude secrets)
- Cleaner builds

### 3.3 Build Cache

Docker caches layers to speed up builds.

**Cache Behavior:**

```dockerfile
FROM ubuntu:22.04                    # Layer 1: Cached
RUN apt-get update                   # Layer 2: Cached
RUN apt-get install -y python3       # Layer 3: Cached
COPY requirements.txt .              # Layer 4: Cached (file unchanged)
RUN pip install -r requirements.txt  # Layer 5: Cached
COPY app.py .                        # Layer 6: REBUILT (file changed)
CMD ["python3", "app.py"]            # Layer 7: REBUILT (subsequent layer)
```

**Cache Invalidation:**
- File content changes
- Instruction changes
- Parent layer changes
- Build arguments change

**Cache Control:**

```bash
# Disable cache
docker build --no-cache -t myapp .

# Pull latest base image
docker build --pull -t myapp .

# Use cache from another image
docker build --cache-from myapp:latest -t myapp:new .
```

### 3.4 Build Arguments

Pass variables at build time.

```dockerfile
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

ARG APP_ENV=production
ENV APP_ENV=${APP_ENV}

ARG BUILD_DATE
ARG VERSION
LABEL build_date=${BUILD_DATE} \
      version=${VERSION}
```

```bash
# Build with arguments
docker build \
  --build-arg PYTHON_VERSION=3.10 \
  --build-arg APP_ENV=development \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VERSION=1.0.0 \
  -t myapp:dev .
```

### 3.5 BuildKit

Modern build engine with advanced features.

**Enable BuildKit:**
```bash
# Environment variable
export DOCKER_BUILDKIT=1
docker build .

# Or inline
DOCKER_BUILDKIT=1 docker build .

# In daemon.json
{
  "features": {
    "buildkit": true
  }
}
```

**BuildKit Features:**

1. **Parallel builds**
2. **Build cache import/export**
3. **Secrets mounting**
4. **SSH agent forwarding**
5. **Better output**

**BuildKit Syntax:**

```dockerfile
# syntax=docker/dockerfile:1.4

FROM ubuntu:22.04

# Mount secret
RUN --mount=type=secret,id=mysecret \
    cat /run/secrets/mysecret

# Mount SSH
RUN --mount=type=ssh \
    git clone git@github.com:user/repo.git

# Mount cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Bind mount
RUN --mount=type=bind,source=.,target=/src \
    cp /src/config.json /app/
```

```bash
# Build with secret
docker build --secret id=mysecret,src=./secret.txt .

# Build with SSH
docker build --ssh default .
```

---

## 4. Multi-Stage Builds

Multi-stage builds create smaller, more secure images by separating build and runtime environments.

### 4.1 Basic Multi-Stage Build

```dockerfile
# Build stage
FROM golang:1.20 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o myapp

# Runtime stage
FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/myapp .
CMD ["./myapp"]
```

**Benefits:**
- Build stage: 800 MB (with Go compiler)
- Runtime stage: 10 MB (only binary)
- 98% size reduction!

### 4.2 Advanced Multi-Stage Patterns

**Multiple Build Stages:**

```dockerfile
# Dependencies stage
FROM node:18 AS dependencies
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Build stage
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime stage
FROM node:18-alpine
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package.json ./
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

**Testing Stage:**

```dockerfile
# Base stage
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Test stage
FROM base AS test
COPY requirements-test.txt .
RUN pip install -r requirements-test.txt
COPY . .
RUN pytest

# Production stage
FROM base AS production
COPY . .
CMD ["python", "app.py"]
```

```bash
# Build and run tests
docker build --target test -t myapp:test .

# Build production
docker build --target production -t myapp:prod .
```

**Copy from External Image:**

```dockerfile
FROM alpine:latest

# Copy from another image
COPY --from=nginx:latest /etc/nginx/nginx.conf /etc/nginx/
COPY --from=busybox:latest /bin/busybox /usr/local/bin/

# Copy from specific version
COPY --from=node:18 /usr/local/bin/node /usr/local/bin/
```

---

## 5. Image Optimization

### 5.1 Minimize Image Size

**Choose Minimal Base Images:**

```dockerfile
# Large: 1.1 GB
FROM ubuntu:22.04

# Medium: 200 MB
FROM python:3.11-slim

# Small: 50 MB
FROM python:3.11-alpine

# Minimal: 5 MB (for static binaries)
FROM scratch
```

**Size Comparison:**

| Base Image | Size | Use Case |
|------------|------|----------|
| ubuntu:22.04 | ~80 MB | Full-featured, debugging |
| debian:bullseye-slim | ~80 MB | Debian minimal |
| alpine:latest | ~5 MB | Minimal, security-focused |
| scratch | 0 MB | Static binaries only |
| distroless | ~20 MB | No shell, minimal attack surface |

**Combine RUN Commands:**

```dockerfile
# Bad: 3 layers
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2

# Good: 1 layer
RUN apt-get update && \
    apt-get install -y \
        package1 \
        package2 && \
    rm -rf /var/lib/apt/lists/*
```

**Remove Unnecessary Files:**

```dockerfile
# Install and cleanup in same layer
RUN apt-get update && \
    apt-get install -y build-essential && \
    # ... build steps ... && \
    apt-get purge -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* \
           /tmp/* \
           /var/tmp/*
```

### 5.2 Layer Optimization

**Order Layers by Change Frequency:**

```dockerfile
# Least frequently changed
FROM python:3.11-slim

# System dependencies (rarely change)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        && rm -rf /var/lib/apt/lists/*

# Application dependencies (change occasionally)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code (changes frequently)
COPY . .

# Metadata (changes with each build)
ARG BUILD_DATE
LABEL build_date=$BUILD_DATE
```

**Use .dockerignore:**

```
# Exclude large unnecessary files
node_modules
.git
*.log
tests
docs
.env
```

### 5.3 Multi-Stage Build Optimization

```dockerfile
# Build stage with all tools
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build && \
    npm prune --production

# Production stage with only runtime
FROM node:18-alpine
WORKDIR /app
# Copy only production dependencies
COPY --from=builder /app/node_modules ./node_modules
# Copy only built artifacts
COPY --from=builder /app/dist ./dist
COPY package.json ./
USER node
CMD ["node", "dist/index.js"]
```

### 5.4 Caching Strategies

**Leverage Build Cache:**

```dockerfile
# Dependencies change less frequently than code
COPY package.json package-lock.json ./
RUN npm ci

# Code changes frequently
COPY . .
RUN npm run build
```

**Use BuildKit Cache Mounts:**

```dockerfile
# syntax=docker/dockerfile:1.4

FROM python:3.11-slim

# Cache pip downloads
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Cache apt packages
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y package
```

### 5.5 Security Optimization

**Use Specific Versions:**

```dockerfile
# Bad: unpredictable
FROM python:latest

# Good: specific version
FROM python:3.11.5-slim-bullseye
```

**Run as Non-Root:**

```dockerfile
FROM python:3.11-slim

# Create user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to user
USER appuser

WORKDIR /app
COPY --chown=appuser:appuser . .

CMD ["python", "app.py"]
```

**Use Distroless Images:**

```dockerfile
# Build stage
FROM golang:1.20 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o myapp

# Runtime stage with distroless
FROM gcr.io/distroless/static-debian11
COPY --from=builder /app/myapp /
USER nonroot:nonroot
CMD ["/myapp"]
```

**Scan for Vulnerabilities:**

```bash
# Using Docker Scout
docker scout cves myapp:latest

# Using Trivy
trivy image myapp:latest

# Using Snyk
snyk container test myapp:latest
```

---

## 6. Best Practices

### 6.1 Dockerfile Best Practices

**1. Use Official Base Images**

```dockerfile
# Preferred
FROM python:3.11-slim

# Avoid
FROM random-user/python-image
```

**2. Pin Versions**

```dockerfile
# Good
FROM python:3.11.5-slim-bullseye
RUN pip install flask==2.3.0

# Bad
FROM python:latest
RUN pip install flask
```

**3. Minimize Layers**

```dockerfile
# Bad: 4 layers
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2
RUN rm -rf /var/lib/apt/lists/*

# Good: 1 layer
RUN apt-get update && \
    apt-get install -y package1 package2 && \
    rm -rf /var/lib/apt/lists/*
```

**4. Use Multi-Stage Builds**

```dockerfile
FROM golang:1.20 AS builder
# Build steps...

FROM alpine:latest
COPY --from=builder /app/binary /app/
```

**5. Don't Install Unnecessary Packages**

```dockerfile
# Install only what's needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        package1 \
        package2 && \
    rm -rf /var/lib/apt/lists/*
```

**6. Use .dockerignore**

```
.git
node_modules
*.log
.env
```

**7. Sort Multi-Line Arguments**

```dockerfile
RUN apt-get update && apt-get install -y \
    package-a \
    package-b \
    package-c \
    && rm -rf /var/lib/apt/lists/*
```

**8. Leverage Build Cache**

```dockerfile
# Copy dependency files first
COPY package.json package-lock.json ./
RUN npm ci

# Copy code later
COPY . .
```

**9. Use COPY Instead of ADD**

```dockerfile
# Preferred
COPY app.py /app/

# Only use ADD for tar extraction
ADD archive.tar.gz /app/
```

**10. Document Exposed Ports**

```dockerfile
EXPOSE 8080
```

### 6.2 Security Best Practices

**1. Run as Non-Root User**

```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

**2. Use Read-Only Root Filesystem**

```dockerfile
# In Dockerfile
VOLUME /tmp

# At runtime
docker run --read-only --tmpfs /tmp myapp
```

**3. Drop Capabilities**

```bash
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp
```

**4. Use Secrets Properly**

```dockerfile
# Bad: secrets in image
ENV API_KEY=secret123

# Good: use secrets at runtime
# docker run -e API_KEY=secret123 myapp

# Better: use Docker secrets
# docker secret create api_key api_key.txt
```

**5. Scan Images Regularly**

```bash
docker scan myapp:latest
```

**6. Sign Images**

```bash
# Enable content trust
export DOCKER_CONTENT_TRUST=1
docker push myapp:latest
```

### 6.3 Performance Best Practices

**1. Use Appropriate Base Images**

```dockerfile
# For Python
FROM python:3.11-slim  # Not python:3.11 (too large)

# For Node.js
FROM node:18-alpine    # Not node:18 (too large)

# For Go (static binary)
FROM scratch           # Smallest possible
```

**2. Optimize Layer Caching**

```dockerfile
# Dependencies first (cached)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Code last (changes frequently)
COPY . .
```

**3. Use BuildKit**

```bash
DOCKER_BUILDKIT=1 docker build .
```

**4. Parallel Builds**

```dockerfile
# syntax=docker/dockerfile:1.4

# BuildKit can parallelize independent stages
FROM base AS stage1
RUN task1

FROM base AS stage2
RUN task2

FROM base AS final
COPY --from=stage1 /output1 /
COPY --from=stage2 /output2 /
```

---

## 7. Image Management

### 7.1 Listing Images

```bash
# List all images
docker images

# List with digests
docker images --digests

# List specific repository
docker images nginx

# Filter images
docker images --filter "dangling=true"
docker images --filter "before=nginx:latest"
docker images --filter "since=nginx:1.20"

# Format output
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Show image IDs only
docker images -q
```

### 7.2 Inspecting Images

```bash
# Detailed information
docker inspect nginx:latest

# Specific field
docker inspect --format='{{.Architecture}}' nginx:latest

# Image layers
docker history nginx:latest

# Image size breakdown
docker history --no-trunc --format "{{.Size}}\t{{.CreatedBy}}" nginx:latest

# Image configuration
docker inspect --format='{{json .Config}}' nginx:latest | jq
```

### 7.3 Tagging Images

```bash
# Tag image
docker tag myapp:latest myapp:v1.0

# Tag for registry
docker tag myapp:latest myregistry.com/myapp:v1.0

# Multiple tags
docker tag myapp:latest myapp:stable
docker tag myapp:latest myapp:production
```

### 7.4 Removing Images

```bash
# Remove single image
docker rmi nginx:latest

# Remove by ID
docker rmi abc123

# Force remove
docker rmi -f nginx:latest

# Remove multiple images
docker rmi nginx:latest ubuntu:22.04

# Remove all unused images
docker image prune

# Remove all images
docker rmi $(docker images -q)

# Remove dangling images
docker image prune -a --filter "dangling=true"
```

### 7.5 Saving and Loading Images

```bash
# Save image to tar file
docker save nginx:latest > nginx.tar
docker save -o nginx.tar nginx:latest

# Save multiple images
docker save -o images.tar nginx:latest ubuntu:22.04

# Load image from tar
docker load < nginx.tar
docker load -i nginx.tar

# Export container filesystem
docker export container_name > container.tar

# Import filesystem as image
docker import container.tar myimage:latest
```

---

## 8. Registry Operations

### 8.1 Docker Hub

**Login:**
```bash
# Login to Docker Hub
docker login

# Login with credentials
docker login -u username -p password

# Logout
docker logout
```

**Push Images:**
```bash
# Tag for Docker Hub
docker tag myapp:latest username/myapp:latest

# Push to Docker Hub
docker push username/myapp:latest

# Push all tags
docker push username/myapp --all-tags
```

**Pull Images:**
```bash
# Pull latest
docker pull nginx

# Pull specific version
docker pull nginx:1.23

# Pull by digest
docker pull nginx@sha256:abc123...

# Pull from specific registry
docker pull myregistry.com/myapp:latest
```

### 8.2 Private Registry

**Run Local Registry:**
```bash
# Start registry
docker run -d -p 5000:5000 --name registry registry:2

# With persistent storage
docker run -d -p 5000:5000 \
  -v /mnt/registry:/var/lib/registry \
  --name registry \
  registry:2
```

**Use Private Registry:**
```bash
# Tag for private registry
docker tag myapp:latest localhost:5000/myapp:latest

# Push to private registry
docker push localhost:5000/myapp:latest

# Pull from private registry
docker pull localhost:5000/myapp:latest
```

**Secure Registry:**
```bash
# With TLS
docker run -d -p 5000:5000 \
  -v /certs:/certs \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
  registry:2

# With authentication
docker run -d -p 5000:5000 \
  -v /auth:/auth \
  -e REGISTRY_AUTH=htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_REALM="Registry Realm" \
  registry:2
```

### 8.3 Image Signing and Verification

**Content Trust:**
```bash
# Enable content trust
export DOCKER_CONTENT_TRUST=1

# Push signed image
docker push username/myapp:latest

# Pull and verify
docker pull username/myapp:latest

# Disable content trust
export DOCKER_CONTENT_TRUST=0
```

**Notary:**
```bash
# Initialize repository
notary init username/myapp

# Add signer
notary key rotate username/myapp snapshot -r

# List targets
notary list username/myapp
```

---

## 9. Summary

### Key Takeaways

1. **Images are layered** - Each instruction creates a new layer
2. **Order matters** - Place frequently changing instructions last
3. **Use multi-stage builds** - Separate build and runtime environments
4. **Minimize image size** - Use minimal base images, combine RUN commands
5. **Security first** - Run as non-root, scan for vulnerabilities, use specific versions
6. **Leverage caching** - Structure Dockerfile for optimal cache usage
7. **Use .dockerignore** - Exclude unnecessary files from build context
8. **Tag properly** - Use semantic versioning, not just `latest`

### Next Steps

- Practice writing Dockerfiles
- Experiment with multi-stage builds
- Learn Docker Compose for multi-container apps
- Explore container networking and storage
- Implement CI/CD with Docker
- Study container orchestration (Kubernetes)

---

**Document Version**: 1.0
**Last Updated**: 2026-03-26


