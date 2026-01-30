# wickit.shuffle - Dynamic Service Discovery & Tauri Integration

## Overview

The `wickit.shuffle` module provides dynamic service discovery and connection management for multi-tool architectures. It's specifically designed to solve port conflicts and enable secure communication between services, with special emphasis on Tauri desktop applications.

## Key Features

- Dynamic port assignment with conflict avoidance
- Service identity verification and security
- Health monitoring and automatic recovery
- Tauri desktop application integration
- mDNS service discovery support
- Secure connection establishment with verification tokens

## Architecture

The shuffle module consists of three main components:

1. **ServiceRegistry**: Manages service registration with automatic port discovery
2. **ServiceDiscovery**: Discovers services across port ranges with verification
3. **ServiceVerifier**: Verifies service identity for secure connections

## Tauri Integration

The module is specifically designed to solve common Tauri desktop app challenges:
- Dynamic port discovery (no more hardcoded 7777 assumptions)
- Service verification (ensure connecting to correct backend)
- Health monitoring (automatic recovery from backend restarts)
- Process management (subprocess management for Python backends)

## Usage Examples

### Basic Service Registration
```python
from wickit.shuffle import ServiceRegistry

# Register a service with automatic port assignment
registry = ServiceRegistry(
    service_id="my-api",
    port_range=(7770, 7779),
    project_context={"project": "my-app", "version": "1.0.0"}
)

service_info = registry.start()
print(f"Service running on port {service_info.port}")
```

### Service Discovery
```python
from wickit.shuffle import ServiceDiscovery

# Discover a specific service
discovery = ServiceDiscovery(port_range=(7770, 7779))
service_info = discovery.discover_service(
    expected_service_id="my-api",
    project_context={"project": "my-app"}
)

if service_info:
    print(f"Found service on port {service_info.port}")
```

## Documentation

For complete integration guide with Tauri applications, see [docs/SERVICE_DISCOVERY_TAURI_INTEGRATION.md](docs/SERVICE_DISCOVERY_TAURI_INTEGRATION.md)
