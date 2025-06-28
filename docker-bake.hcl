// Docker Buildx Bake config / optimized multi-arch builds

variable "TORERO_VERSION" {
  default = "1.3.1"
}

variable "PYTHON_VERSION" {
  default = "3.13.0"
}

variable "REGISTRY" {
  default = "ghcr.io"
}

variable "IMAGE_NAME" {
  default = "torerodev/torero-container"
}

// platforms we support
variable "PLATFORMS" {
  default = ["linux/amd64", "linux/arm64"]
}

// only build amd64 for PRs
variable "PR_BUILD" {
  default = false
}

// main build target
target "default" {
  dockerfile = "Containerfile"
  platforms = PR_BUILD ? ["linux/amd64"] : PLATFORMS
  
  tags = [
    "${REGISTRY}/${IMAGE_NAME}:${TORERO_VERSION}",
    "${REGISTRY}/${IMAGE_NAME}:latest"
  ]
  
  args = {
    TORERO_VERSION = TORERO_VERSION
    PYTHON_VERSION = PYTHON_VERSION
  }
  
  cache-from = [
    "type=gha,scope=buildx-${TORERO_VERSION}"
  ]
  
  cache-to = [
    "type=gha,mode=max,scope=buildx-${TORERO_VERSION}"
  ]
}

// development build (single platform, with cache mount)
target "dev" {
  inherits = ["default"]
  platforms = ["linux/amd64"]
  
  tags = [
    "torero-dev:latest"
  ]
  
  cache-from = [
    "type=local,src=/tmp/.buildx-cache"
  ]
  
  cache-to = [
    "type=local,dest=/tmp/.buildx-cache"
  ]
}

// PR validation build
target "pr" {
  inherits = ["default"]
  platforms = ["linux/amd64"]
  
  tags = [
    "torero-pr:${TORERO_VERSION}"
  ]
}

// release build with all platforms
target "release" {
  inherits = ["default"]
  platforms = PLATFORMS
  
  labels = {
    "org.opencontainers.image.source" = "https://github.com/torerodev/torero-container"
    "org.opencontainers.image.version" = TORERO_VERSION
    "org.opencontainers.image.vendor" = "torerodev"
  }
}

// group for building all targets
group "all" {
  targets = ["release"]
}