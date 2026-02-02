/**
 * wickit-js/shuffle - Frontend Service Discovery
 *
 * Auto-discover backend services by scanning port ranges and checking health endpoints.
 *
 * Usage:
 *   import { discoverService } from '@/path/to/wickit-js/shuffle';
 *
 *   const backend = await discoverService({
 *     serviceId: 'ralfie-api',
 *     portRange: [7770, 7779],
 *     timeout: 5000
 *   });
 *
 *   console.log(`Backend at: ${backend.url}`);
 */

export interface ServiceHealth {
  service: string;
  status: string;
  port: number;
  mdns?: string;
  uptime_seconds?: number;
  metadata?: Record<string, any>;
}

export interface DiscoveredService {
  url: string;
  port: number;
  health: ServiceHealth;
}

export interface DiscoverOptions {
  serviceId: string;
  portRange: [number, number];
  host?: string;
  timeout?: number;
  healthEndpoint?: string;
}

export class ServiceDiscoveryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ServiceDiscoveryError';
  }
}

/**
 * Discover a backend service by scanning ports and checking health endpoints.
 *
 * @param options - Discovery configuration
 * @returns Promise resolving to discovered service info
 * @throws ServiceDiscoveryError if service not found
 */
export async function discoverService(
  options: DiscoverOptions
): Promise<DiscoveredService> {
  const {
    serviceId,
    portRange,
    host = 'localhost',
    timeout = 5000,
    healthEndpoint = '/api/health'
  } = options;

  const [minPort, maxPort] = portRange;

  // Try each port in range
  for (let port = minPort; port <= maxPort; port++) {
    try {
      const url = `http://${host}:${port}`;
      const health = await checkHealth(url, healthEndpoint, timeout);

      // Check if this is the service we're looking for
      if (health.service === serviceId) {
        return {
          url,
          port,
          health
        };
      }
    } catch (error) {
      // Port not responding or wrong service, continue scanning
      continue;
    }
  }

  throw new ServiceDiscoveryError(
    `Service '${serviceId}' not found in port range ${minPort}-${maxPort}`
  );
}

/**
 * Check health endpoint of a service.
 *
 * @param baseUrl - Base URL of the service
 * @param endpoint - Health endpoint path
 * @param timeout - Request timeout in milliseconds
 * @returns Promise resolving to health info
 */
async function checkHealth(
  baseUrl: string,
  endpoint: string,
  timeout: number
): Promise<ServiceHealth> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${baseUrl}${endpoint}`, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    const health: ServiceHealth = await response.json();
    return health;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Discover service with retries and exponential backoff.
 * Useful during app startup when backend might not be ready yet.
 *
 * @param options - Discovery configuration
 * @param maxRetries - Maximum number of retry attempts
 * @param initialDelay - Initial delay between retries in ms
 * @returns Promise resolving to discovered service info
 */
export async function discoverServiceWithRetry(
  options: DiscoverOptions,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<DiscoveredService> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await discoverService(options);
    } catch (error) {
      lastError = error as Error;

      if (attempt < maxRetries - 1) {
        // Wait with exponential backoff
        const delay = initialDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw new ServiceDiscoveryError(
    `Failed to discover service after ${maxRetries} attempts: ${lastError?.message}`
  );
}

/**
 * Create a proxy configuration for Vite/webpack that auto-discovers the backend.
 *
 * @param options - Discovery configuration
 * @returns Promise resolving to proxy target URL
 */
export async function createAutoDiscoveryProxy(
  options: DiscoverOptions
): Promise<string> {
  const service = await discoverService(options);
  return service.url;
}
