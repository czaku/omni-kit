# Wickit Shuffle - Dynamic Service Discovery & Tauri Integration Guide

## Overview

The `wickit.shuffle` module provides dynamic service discovery and connection management for multi-tool architectures. It's specifically designed to solve port conflicts and enable secure communication between services, with special emphasis on Tauri desktop applications.

## Core Concepts

### ServiceRegistry
The `ServiceRegistry` automatically discovers available ports and registers services with identity verification:

```python
from wickit.shuffle import ServiceRegistry

# Create a service registry
registry = ServiceRegistry(
    service_id="my-api",
    port_range=(7770, 7779),
    project_context={"project": "my-project", "version": "1.0.0"},
    mdns_name="myapp.local"  # Optional mDNS discovery
)

# Start service with automatic port assignment
service_info = registry.start()

# Use in Flask app
@app.route('/api/health')
def health():
    return registry.health_response()
```

### ServiceDiscovery
The `ServiceDiscovery` finds and verifies services across port ranges:

```python
from wickit.shuffle import ServiceDiscovery

# Discover a specific service
discovery = ServiceDiscovery(port_range=(7770, 7779))
service_info = discovery.discover_service(
    expected_service_id="my-api",
    project_context={"project": "my-project"}
)

if service_info:
    print(f"Found service on port {service_info.port}")
```

### ServiceVerifier
The `ServiceVerifier` ensures discovered services are legitimate:

```python
from wickit.shuffle import ServiceVerifier

verifier = ServiceVerifier()
is_valid = verifier.verify_service_identity(expected_service, discovered_service)
```

## Tauri Integration Guide

### 1. Basic Tauri + Python Backend Setup

For Tauri applications that need to communicate with a Python backend, use the shuffle module to handle dynamic port assignment:

**Python Backend (api/server.py):**
```python
from wickit.shuffle import ServiceRegistry
import argparse

def main():
    parser = argparse.ArgumentParser(description='My API Server')
    parser.add_argument('--port', type=int, help='Preferred port (default: auto-discover)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    
    args = parser.parse_args()
    
    # Use shuffle for dynamic port assignment
    registry = ServiceRegistry(
        service_id="my-api",
        port_range=(7770, 7779),
        project_context={"project": "my-app", "version": "0.1.0"},
        mdns_name="myapp.local"
    )
    
    # Auto-discover port (or use preferred)
    port = registry.start(preferred_port=args.port)
    
    print(f"Starting server on port {port}")
    
    # Add health endpoint
    @app.route('/api/health')
    def health():
        return registry.health_response()
    
    # Start server
    app.run(host=args.host, port=port, debug=args.debug)

if __name__ == '__main__':
    main()
```

**Tauri Rust Code (src/lib.rs):**
```rust
use std::process::{Command, Child};
use std::sync::Mutex;
use std::net::TcpStream;
use std::time::{Duration, Instant};

pub struct FlaskState {
    pub process: Mutex<Option<Child>>,
    pub port: Mutex<Option<u16>>,  // Track actual port
}

/// Discover the actual port that the Python API server is running on
pub fn discover_api_port(timeout_secs: u64) -> Result<Option<u16>, String> {
    use std::process::Stdio;
    
    let project_root = std::env::current_dir()
        .map_err(|e| format!("Can't get current dir: {}", e))?
        .parent()
        .ok_or("Can't get parent directory")?
        .ok_or("Can't get project root")?
        .to_path_buf();

    let discover_script = project_root.join("lib").join("discover_api_port.py");

    if !discover_script.exists() {
        return Err(format!("Discovery script not found: {:?}", discover_script));
    }

    let start = Instant::now();
    let timeout = Duration::from_secs(timeout_secs);

    while start.elapsed() < timeout {
        // Run the discovery script to find the actual port
        let output = Command::new("python3")
            .arg(&discover_script)
            .current_dir(&project_root)
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .output()
            .map_err(|e| format!("Failed to run discovery script: {}", e))?;

        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let port_str = stdout.trim();
            
            if let Ok(port) = port_str.parse::<u16>() {
                if port > 0 {
                    println!("✅ Discovered API on port: {}", port);
                    return Ok(Some(port));
                }
            }
        }

        std::thread::sleep(Duration::from_millis(500)); // Wait before retrying
    }

    Ok(None) // Didn't find port within timeout
}

/// Start the Python backend as a subprocess
pub fn start_backend_server() -> Result<Child, String> {
    let project_root = std::env::current_dir()
        .map_err(|e| format!("Can't get current dir: {}", e))?
        .parent()
        .ok_or("Can't get parent directory")?
        .ok_or("Can't get project root")?
        .to_path_buf();

    let python = which::which("python3")
        .or_else(|_| which::which("python"))
        .map_err(|e| format!("Python not found: {}", e))?;

    // Start Python server with PYTHONPATH set to project root
    let child = Command::new(python)
        .arg("api/server.py")
        .current_dir(&project_root)
        .env("PYTHONPATH", &project_root)
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;

    println!("Backend server started (PID: {})", child.id());

    Ok(child)
}
```

### 2. Python Discovery Script

Create a discovery script that can be called from Rust to find the actual port:

**lib/discover_api_port.py:**
```python
#!/usr/bin/env python3
"""
Discover the actual port that the API server is running on.

This script uses the wickit.shuffle ServiceDiscovery to find the actual port
that the API server is running on.
"""

import sys
import os
import time
from typing import Optional

# Add the project root to the path so we can import wickit
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def discover_api_port() -> Optional[int]:
    """
    Discover the port that the API server is running on.
    
    Returns:
        Port number if found, None if not found
    """
    try:
        from wickit.shuffle import ServiceDiscovery
        
        # Look for the API service in the expected port range
        discovery = ServiceDiscovery((7770, 7779))
        service_info = discovery.discover_service(
            "my-api",  # Service ID from your registry
            {"project": "my-project"}  # Project context from your registry
        )
        
        if service_info:
            return service_info.port
        else:
            return None
            
    except ImportError:
        print("wickit.shuffle not available", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error discovering API port: {e}", file=sys.stderr)
        return None

def main():
    """Main entry point for the discovery utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Discover API port')
    parser.add_argument('--wait', type=int, default=15, help='Wait up to N seconds for server to start')
    
    args = parser.parse_args()
    
    # Wait for server to start
    start_time = time.time()
    while time.time() - start_time < args.wait:
        port = discover_api_port()
        if port:
            print(port)
            sys.exit(0)
        time.sleep(1)  # Wait 1 second before trying again
    
    print("0")  # Not found within timeout
    sys.exit(1)

if __name__ == "__main__":
    main()
```

### 3. Health Monitoring for Tauri Apps

For robust Tauri applications, implement health monitoring to handle backend restarts:

```python
from wickit.shuffle import HealthMonitor, ServiceInfo

def setup_health_monitoring(service_info: ServiceInfo, on_change_callback):
    """
    Set up health monitoring for a service.
    
    Args:
        service_info: ServiceInfo for the service to monitor
        on_change_callback: Function to call when service state changes
    """
    monitor = HealthMonitor(service_info, on_change_callback)
    monitor.start_monitoring()
    
    return monitor

# Example callback for handling service changes
def handle_service_change(change_event):
    if change_event.event_type == 'restart':
        print(f"Service restarted from port {change_event.old_service.port} to {change_event.new_service.port}")
        # Update frontend to use new port
    elif change_event.event_type == 'recovery':
        print(f"Service recovered on port {change_event.new_service.port}")
        # Update frontend to use recovered port
    elif change_event.event_type == 'disconnected':
        print("Service disconnected, attempting to reconnect...")
        # Implement reconnection logic
```

### 4. Complete Tauri Integration Example

Here's a complete example of how to integrate shuffle with a Tauri app:

**Tauri setup in lib.rs:**
```rust
use tauri::Manager;
use std::sync::Mutex;

mod backend {
    use std::process::Child;
    use std::sync::Mutex;
    
    pub struct BackendState {
        pub process: Mutex<Option<Child>>,
        pub port: Mutex<Option<u16>>,
    }
    
    // Include the functions from above examples
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // Start backend server
            match backend::start_backend_server() {
                Ok(child) => {
                    let backend_state = backend::BackendState {
                        process: Mutex::new(Some(child)),
                        port: Mutex::new(None),  // Will discover later
                    };
                    app.manage(backend_state);

                    // Discover which port the backend actually started on
                    match backend::discover_api_port(15) {  // Wait up to 15 seconds
                        Ok(Some(port)) => {
                            println!("✅ Backend discovered on port: {}", port);
                            
                            // Update the backend state with the actual port
                            if let Some(state) = app.try_state::<backend::BackendState>() {
                                *state.port.lock().unwrap() = Some(port);
                            }
                        }
                        Ok(None) => {
                            eprintln!("❌ Could not discover backend port within timeout");
                        }
                        Err(e) => {
                            eprintln!("❌ Error discovering backend port: {}", e);
                        }
                    }
                }
                Err(e) => {
                    eprintln!("❌ Failed to start backend: {}", e);
                    app.manage(backend::BackendState {
                        process: Mutex::new(None),
                        port: Mutex::new(None),
                    });
                }
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Best Practices

### 1. Port Range Selection
- Use non-standard port ranges (7770-7779) to avoid conflicts
- Keep ranges narrow to minimize scanning time
- Document your port ranges for team coordination

### 2. Service Identity Verification
- Always use project context for verification
- Include unique identifiers in service metadata
- Verify service identity before establishing connections

### 3. Error Handling
- Implement timeouts for discovery operations
- Provide fallback mechanisms when discovery fails
- Log discovery attempts for debugging

### 4. Security Considerations
- Use verification tokens to prevent unauthorized connections
- Validate service identity before trusting responses
- Implement rate limiting for health checks

## Common Patterns

### Pattern 1: Auto-Starting Backend with Discovery
```python
def start_and_discover_backend():
    # Start the backend service
    registry = ServiceRegistry(
        service_id="my-api",
        port_range=(7770, 7779),
        project_context={"project": "my-app"}
    )
    
    service_info = registry.start()
    
    # The service is now running on service_info.port
    return service_info
```

### Pattern 2: Frontend Connection with Dynamic Port
```javascript
// In your frontend, get the port from Tauri
// This would be called from your React/Vue/Svelte app
async function getBackendPort() {
    // This would be a Tauri command that returns the discovered port
    const port = await invoke('get_backend_port');
    return port;
}

async function makeApiCall(endpoint) {
    const port = await getBackendPort();
    const response = await fetch(`http://127.0.0.1:${port}${endpoint}`);
    return response.json();
}
```

## Troubleshooting

### Common Issues:
1. **Port Already in Use**: Increase the port range or check for other processes
2. **Service Not Found**: Verify service_id and project_context match
3. **Verification Failures**: Check that verification tokens match between services
4. **Timeout Errors**: Increase timeout values or check network connectivity

### Debugging Tips:
- Enable logging to see discovery attempts
- Check that health endpoints are accessible
- Verify that mDNS names are resolving correctly
- Confirm that services are registering properly

This module is designed to make multi-service architectures more robust by eliminating hardcoded port dependencies and providing secure, verified connections between services.