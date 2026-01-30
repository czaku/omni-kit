"""
wickit.shuffle - Dynamic Service Discovery and Connection Management

Auto-discover available ports, register services with identity verification,
and enable secure frontend-backend communication for multi-tool architectures.

This module provides:
- Dynamic port assignment with conflict avoidance
- Service identity verification
- Health monitoring and recovery
- Secure connection establishment
- Tauri integration for desktop apps
"""

import socket
import json
import uuid
import os
import time
from typing import Optional, Tuple, Dict, Any, Callable, List
from datetime import datetime
from dataclasses import dataclass, asdict
import asyncio
import threading


class ShuffleError(Exception):
    """Base exception for shuffle errors"""
    pass


class NoAvailablePortError(ShuffleError):
    """Raised when no ports are available in the specified range"""
    pass


class ServiceNotFoundError(ShuffleError):
    """Raised when service cannot be found or verified"""
    pass


@dataclass
class ServiceInfo:
    """Information about a discovered service"""
    service_id: str
    port: int
    instance_id: str
    pid: int
    project_context: Dict[str, Any]
    verification_token: str
    start_time: datetime
    status: str = "healthy"


class ServiceRegistry:
    """
    Register and manage a service with automatic port discovery and verification.

    Example:
        registry = ServiceRegistry(
            service_id="ralfie-api",
            port_range=(7770, 7779),
            project_context={"project": "ralfiepretzel", "version": "0.12.2"}
        )

        service_info = registry.start()

        # In Flask:
        @app.route('/api/health')
        def health():
            return registry.health_response()
    """

    def __init__(
        self,
        service_id: str,
        port_range: Tuple[int, int],
        project_context: Optional[Dict[str, Any]] = None,
        mdns_name: Optional[str] = None
    ):
        """
        Initialize service registry.

        Args:
            service_id: Unique identifier for this service (e.g., "ralfie-api")
            port_range: Tuple of (min_port, max_port) to search for available port
            project_context: Additional context for service identification
            mdns_name: Optional mDNS name (e.g., "ralfie.local")
        """
        self.service_id = service_id
        self.port_range = port_range
        self.project_context = project_context or {}
        self.mdns_name = mdns_name
        self.service_info: Optional[ServiceInfo] = None
        self._zeroconf = None
        self._service_info = None

    def start(self, preferred_port: Optional[int] = None) -> ServiceInfo:
        """
        Find available port and register service with verification.

        Args:
            preferred_port: If specified, try this port first before scanning range

        Returns:
            ServiceInfo with complete service details
        """
        # Try preferred port first if specified
        if preferred_port and self._is_port_available(preferred_port):
            port = preferred_port
        else:
            port = self._find_available_port()

        # Generate unique identifiers
        instance_id = str(uuid.uuid4())
        verification_token = str(uuid.uuid4())
        
        self.service_info = ServiceInfo(
            service_id=self.service_id,
            port=port,
            instance_id=instance_id,
            pid=os.getpid(),
            project_context=self.project_context,
            verification_token=verification_token,
            start_time=datetime.now(),
            status="healthy"
        )

        # Register mDNS if name provided
        if self.mdns_name:
            self._register_mdns()

        return self.service_info

    def _find_available_port(self) -> int:
        """Find an available port within the specified range."""
        min_port, max_port = self.port_range

        for port in range(min_port, max_port + 1):
            if self._is_port_available(port):
                return port

        raise NoAvailablePortError(
            f"No available ports in range {min_port}-{max_port}"
        )

    def _is_port_available(self, port: int) -> bool:
        """Check if a specific port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return True
        except OSError:
            return False

    def _register_mdns(self):
        """Register mDNS service (requires zeroconf)"""
        try:
            from zeroconf import Zeroconf, ServiceInfo
            import socket as sock

            zeroconf = Zeroconf()

            # Get local IP
            hostname = sock.gethostname()
            local_ip = sock.gethostbyname(hostname)

            # Create service info
            service_type = "_http._tcp.local."
            service_name = f"{self.service_id}.{service_type}"

            info = ServiceInfo(
                service_type,
                service_name,
                addresses=[sock.inet_aton(local_ip)],
                port=self.service_info.port,
                properties={
                    'service_id': self.service_info.service_id,
                    'instance_id': self.service_info.instance_id,
                    'pid': str(self.service_info.pid),
                    'verification_token': self.service_info.verification_token,
                    **self.project_context
                },
                server=f"{self.mdns_name}."
            )

            zeroconf.register_service(info)

            self._zeroconf = zeroconf
            self._service_info = info

            print(f"🌐 mDNS service registered: http://{self.mdns_name}:{self.service_info.port}")

        except ImportError:
            print("⚠️  zeroconf not installed, skipping mDNS registration")

    def health_response(self) -> Dict[str, Any]:
        """
        Generate standardized health check response with verification info.

        Returns:
            Dict with service health and verification information
        """
        if not self.service_info:
            return {"error": "Service not started"}

        uptime_seconds = (datetime.now() - self.service_info.start_time).total_seconds()

        return {
            "service": self.service_info.service_id,
            "status": self.service_info.status,
            "port": self.service_info.port,
            "instance_id": self.service_info.instance_id,
            "pid": self.service_info.pid,
            "verification_token": self.service_info.verification_token,
            "project_context": self.service_info.project_context,
            "mdns": self.mdns_name,
            "uptime_seconds": uptime_seconds,
            "start_time": self.service_info.start_time.isoformat()
        }

    def stop(self):
        """Cleanup: unregister mDNS service"""
        if self._zeroconf and self._service_info:
            self._zeroconf.unregister_service(self._service_info)
            self._zeroconf.close()
            print(f"🌐 mDNS service unregistered: {self.mdns_name}")


class ServiceVerifier:
    """Verify service identity and security"""
    
    @staticmethod
    def verify_service_identity(
        expected_service: ServiceInfo,
        discovered_service: ServiceInfo
    ) -> bool:
        """
        Verify that discovered service matches expected service.
        
        Args:
            expected_service: ServiceInfo we expect to find
            discovered_service: ServiceInfo we discovered
            
        Returns:
            True if services match, False otherwise
        """
        checks = [
            expected_service.service_id == discovered_service.service_id,
            expected_service.instance_id == discovered_service.instance_id,
            expected_service.pid == discovered_service.pid,
            expected_service.verification_token == discovered_service.verification_token,
        ]
        
        return all(checks)


class ServiceDiscovery:
    """Discover services with identity verification"""
    
    def __init__(self, port_range: Tuple[int, int]):
        self.port_range = port_range
        self.client = __import__('urllib.request', fromlist=['urllib.request'])
        
    def discover_service(self, expected_service_id: str, project_context: Dict[str, Any]) -> Optional[ServiceInfo]:
        """
        Discover service by scanning port range and verifying identity.
        
        Args:
            expected_service_id: Expected service ID to find
            project_context: Expected project context
            
        Returns:
            ServiceInfo if found and verified, None otherwise
        """
        import urllib.request
        import urllib.error
        
        for port in range(self.port_range[0], self.port_range[1] + 1):
            try:
                # Try to reach health endpoint
                url = f"http://127.0.0.1:{port}/api/health"
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'wickit-shuffle-discovery')
                
                response = urllib.request.urlopen(request, timeout=2)
                data = json.loads(response.read().decode())
                
                # Check if service matches expected criteria
                if (data.get("service") == expected_service_id and 
                    data.get('status') == 'healthy'):
                    
                    # Create ServiceInfo from response
                    service_info = ServiceInfo(
                        service_id=data['service'],
                        port=data['port'],
                        instance_id=data['instance_id'],
                        pid=data['pid'],
                        project_context=data['project_context'],
                        verification_token=data['verification_token'],
                        start_time=datetime.fromisoformat(data['start_time']),
                        status=data['status']
                    )
                    
                    # Verify project context matches
                    if all(
                        project_context.get(key) == service_info.project_context.get(key)
                        for key in project_context.keys()
                    ):
                        return service_info
                        
            except (urllib.error.URLError, json.JSONDecodeError, KeyError):
                # Port not accessible or invalid response, continue to next port
                continue
                
        return None


class HealthMonitor:
    """Monitor service health and handle recovery"""
    
    def __init__(self, service_info: ServiceInfo, on_change: Callable[['ServiceChangeEvent'], None]):
        self.service_info = service_info
        self.on_change = on_change
        self.is_monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start monitoring service health in background thread"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring service health"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            
    def _monitor_loop(self):
        """Internal monitoring loop"""
        import urllib.request
        import urllib.error
        
        while self.is_monitoring:
            try:
                # Check service health
                url = f"http://127.0.0.1:{self.service_info.port}/api/health"
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'wickit-shuffle-monitor')
                
                response = urllib.request.urlopen(request, timeout=3)
                data = json.loads(response.read().decode())
                
                # Check if service is still the same instance
                if (data.get('instance_id') != self.service_info.instance_id or
                    data.get('pid') != self.service_info.pid):
                    # Service has restarted with new instance
                    self.on_change(ServiceChangeEvent(
                        event_type='restart',
                        old_service=self.service_info,
                        new_service=ServiceInfo(
                            service_id=data['service'],
                            port=data['port'],
                            instance_id=data['instance_id'],
                            pid=data['pid'],
                            project_context=data['project_context'],
                            verification_token=data['verification_token'],
                            start_time=datetime.fromisoformat(data['start_time']),
                            status=data['status']
                        )
                    ))
                    return
                    
            except (urllib.error.URLError, json.JSONDecodeError, KeyError):
                # Service is down, try to discover new instance
                self._handle_service_down()
                
            time.sleep(5)  # Check every 5 seconds
            
    def _handle_service_down(self):
        """Handle service going down"""
        # Try to discover new instance of the same service
        discovery = ServiceDiscovery((self.service_info.port - 10, self.service_info.port + 10))
        new_service = discovery.discover_service(
            self.service_info.service_id,
            self.service_info.project_context
        )
        
        if new_service:
            self.on_change(ServiceChangeEvent(
                event_type='recovery',
                old_service=self.service_info,
                new_service=new_service
            ))
        else:
            self.on_change(ServiceChangeEvent(
                event_type='disconnected',
                old_service=self.service_info,
                new_service=None
            ))


@dataclass
class ServiceChangeEvent:
    """Event representing a change in service connection"""
    event_type: str  # 'restart', 'recovery', 'disconnected'
    old_service: ServiceInfo
    new_service: Optional[ServiceInfo]


# Convenience function for simple use cases
def quick_start(
    service_id: str,
    port_range: Tuple[int, int],
    project_context: Optional[Dict[str, Any]] = None,
    mdns_name: Optional[str] = None
) -> ServiceInfo:
    """
    Quick helper to start a service with verification.

    Args:
        service_id: Service identifier
        port_range: Port range to search
        project_context: Additional context for verification
        mdns_name: Optional mDNS name

    Returns:
        ServiceInfo with complete service details
    """
    registry = ServiceRegistry(service_id, port_range, project_context, mdns_name)
    return registry.start()

