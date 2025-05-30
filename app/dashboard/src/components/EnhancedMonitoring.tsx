import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardHeader,
  CardBody,
  Badge,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Button,
  useColorMode,
  Spinner,
} from "@chakra-ui/react";
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ChartBarIcon,
  EyeIcon,
  NoSymbolIcon,
} from "@heroicons/react/24/outline";
import { FC, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { formatBytes } from "utils/formatByte";

interface ServiceStatus {
  name: string;
  enabled: boolean;
  running: boolean;
  initialized: boolean;
  status: string;
  error?: string;
}

interface EnhancedMetrics {
  timestamp: string;
  services: {
    [key: string]: {
      status: string;
      metrics: any;
      last_activity?: string;
    };
  };
}

const ServiceStatusCard: FC<{
  service: ServiceStatus;
  metrics?: any;
}> = ({ service, metrics }) => {
  const { colorMode } = useColorMode();
  
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "running":
      case "active":
        return "green";
      case "stopped":
      case "inactive":
        return "red";
      case "starting":
      case "initializing":
        return "yellow";
      default:
        return "gray";
    }
  };

  const getServiceIcon = (name: string) => {
    switch (name) {
      case "two_factor_auth":
        return <ShieldCheckIcon width="20" height="20" />;
      case "fail2ban_logger":
        return <ExclamationTriangleIcon width="20" height="20" />;
      case "connection_tracker":
        return <ClockIcon width="20" height="20" />;
      case "dns_manager":
        return <EyeIcon width="20" height="20" />;
      case "adblock_manager":
        return <NoSymbolIcon width="20" height="20" />;
      default:
        return <ChartBarIcon width="20" height="20" />;
    }
  };

  return (
    <Card
      bg="white"
      _dark={{ bg: "gray.750" }}
      borderRadius="12px"
      border="1px solid"
      borderColor="light-border"
      _dark={{ borderColor: "gray.600" }}
    >
      <CardHeader pb="2">
        <HStack justify="space-between">
          <HStack>
            <Box
              p="2"
              borderRadius="8px"
              bg={`${getStatusColor(service.status)}.400`}
              color="white"
            >
              {getServiceIcon(service.name)}
            </Box>
            <VStack align="start" spacing="0">
              <Text fontWeight="semibold" fontSize="md">
                {service.name.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
              </Text>
              <HStack spacing="2">
                <Badge colorScheme={getStatusColor(service.status)} size="sm">
                  {service.status}
                </Badge>
                {service.enabled && (
                  <Badge colorScheme="blue" size="sm">
                    Enabled
                  </Badge>
                )}
              </HStack>
            </VStack>
          </HStack>
          <VStack align="end" spacing="1">
            <Text fontSize="xs" color="gray.500">
              {service.running ? "Running" : "Stopped"}
            </Text>
            {service.initialized && (
              <Text fontSize="xs" color="green.500">
                Initialized
              </Text>
            )}
          </VStack>
        </HStack>
      </CardHeader>
      
      {metrics && (
        <CardBody pt="0">
          <VStack spacing="2" align="stretch">
            {metrics.blocked_requests && (
              <HStack justify="space-between">
                <Text fontSize="sm">Blocked Requests:</Text>
                <Text fontSize="sm" fontWeight="medium">
                  {metrics.blocked_requests}
                </Text>
              </HStack>
            )}
            {metrics.active_connections && (
              <HStack justify="space-between">
                <Text fontSize="sm">Active Connections:</Text>
                <Text fontSize="sm" fontWeight="medium">
                  {metrics.active_connections}
                </Text>
              </HStack>
            )}
            {metrics.memory_usage && (
              <VStack spacing="1" align="stretch">
                <HStack justify="space-between">
                  <Text fontSize="sm">Memory Usage:</Text>
                  <Text fontSize="sm" fontWeight="medium">
                    {formatBytes(metrics.memory_usage)}
                  </Text>
                </HStack>
                <Progress
                  value={metrics.memory_percentage || 0}
                  size="sm"
                  colorScheme={metrics.memory_percentage > 80 ? "red" : "green"}
                />
              </VStack>
            )}
            {metrics.last_activity && (
              <HStack justify="space-between">
                <Text fontSize="sm">Last Activity:</Text>
                <Text fontSize="sm" color="gray.500">
                  {new Date(metrics.last_activity).toLocaleTimeString()}
                </Text>
              </HStack>
            )}
          </VStack>
        </CardBody>
      )}
      
      {service.error && (
        <CardBody pt="0">
          <Text fontSize="sm" color="red.500">
            Error: {service.error}
          </Text>
        </CardBody>
      )}
    </Card>
  );
};

export const EnhancedMonitoring: FC = () => {
  const { t } = useTranslation();
  const [refreshInterval, setRefreshInterval] = useState(5000);

  // Fetch service status
  const { data: statusData, isLoading: statusLoading } = useQuery({
    queryKey: "enhanced-status",
    queryFn: () => fetch("/api/enhanced/status"),
    refetchInterval: refreshInterval,
  });

  // Fetch service metrics
  const { data: metricsData, isLoading: metricsLoading } = useQuery({
    queryKey: "enhanced-metrics",
    queryFn: () => fetch("/api/enhanced/metrics"),
    refetchInterval: refreshInterval,
  });

  // Fetch health check
  const { data: healthData } = useQuery({
    queryKey: "enhanced-health",
    queryFn: () => fetch("/api/enhanced/health"),
    refetchInterval: refreshInterval * 2, // Less frequent health checks
  });

  if (statusLoading) {
    return (
      <Box p="6" textAlign="center">
        <Spinner size="lg" />
        <Text mt="4">Loading Enhanced Services Status...</Text>
      </Box>
    );
  }

  const services = statusData?.services || {};
  const metrics = metricsData?.services || {};

  return (
    <VStack spacing="6" align="stretch">
      <Box>
        <HStack justify="space-between" align="center" mb="4">
          <VStack align="start" spacing="0">
            <Text fontSize="2xl" fontWeight="bold">
              📊 Enhanced Services Monitoring
            </Text>
            <Text color="gray.600" _dark={{ color: "gray.400" }}>
              Real-time status and metrics for all Enhanced features
            </Text>
          </VStack>
          <VStack align="end" spacing="1">
            <HStack>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setRefreshInterval(refreshInterval === 5000 ? 1000 : 5000)}
              >
                {refreshInterval === 5000 ? "Fast Refresh" : "Normal Refresh"}
              </Button>
            </HStack>
            <Text fontSize="xs" color="gray.500">
              Refreshing every {refreshInterval / 1000}s
            </Text>
          </VStack>
        </HStack>

        {/* Overall Status */}
        {statusData && (
          <Card mb="6" bg="blue.50" _dark={{ bg: "blue.900" }} borderColor="blue.200" _dark={{ borderColor: "blue.700" }}>
            <CardBody>
              <HStack justify="space-between">
                <VStack align="start" spacing="1">
                  <Text fontWeight="semibold">System Overview</Text>
                  <HStack>
                    <Badge colorScheme="blue">
                      {statusData.running_services}/{statusData.total_services} Services Running
                    </Badge>
                    {statusData.manager_initialized && (
                      <Badge colorScheme="green">Manager Initialized</Badge>
                    )}
                  </HStack>
                </VStack>
                <VStack align="end" spacing="1">
                  <Text fontSize="sm" color="gray.600" _dark={{ color: "gray.400" }}>
                    Last Check: {new Date(statusData.last_check).toLocaleTimeString()}
                  </Text>
                  {healthData && (
                    <Badge colorScheme={healthData.overall_health === "healthy" ? "green" : "red"}>
                      {healthData.overall_health}
                    </Badge>
                  )}
                </VStack>
              </HStack>
            </CardBody>
          </Card>
        )}
      </Box>

      {/* Services Grid */}
      <Box>
        <Text fontSize="lg" fontWeight="semibold" mb="4">
          Service Status
        </Text>
        <VStack spacing="4" align="stretch">
          {Object.entries(services).map(([serviceName, serviceData]) => (
            <ServiceStatusCard
              key={serviceName}
              service={serviceData as ServiceStatus}
              metrics={metrics[serviceName]?.metrics}
            />
          ))}
        </VStack>
      </Box>

      {/* Health Issues */}
      {healthData?.issues && healthData.issues.length > 0 && (
        <Box>
          <Text fontSize="lg" fontWeight="semibold" mb="4" color="red.500">
            ⚠️ Health Issues
          </Text>
          <Card borderColor="red.200" _dark={{ borderColor: "red.700" }}>
            <CardBody>
              <VStack spacing="2" align="stretch">
                {healthData.issues.map((issue: string, index: number) => (
                  <Text key={index} fontSize="sm" color="red.600" _dark={{ color: "red.400" }}>
                    • {issue}
                  </Text>
                ))}
              </VStack>
            </CardBody>
          </Card>
        </Box>
      )}

      {/* Recent Activity Table */}
      {metricsData && (
        <Box>
          <Text fontSize="lg" fontWeight="semibold" mb="4">
            Recent Activity
          </Text>
          <Card>
            <CardBody>
              <Table size="sm">
                <Thead>
                  <Tr>
                    <Th>Service</Th>
                    <Th>Status</Th>
                    <Th>Last Activity</Th>
                    <Th>Metrics</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {Object.entries(metrics).map(([serviceName, serviceMetrics]: [string, any]) => (
                    <Tr key={serviceName}>
                      <Td>{serviceName.replace(/_/g, " ")}</Td>
                      <Td>
                        <Badge colorScheme={serviceMetrics.status === "active" ? "green" : "red"}>
                          {serviceMetrics.status}
                        </Badge>
                      </Td>
                      <Td>
                        {serviceMetrics.last_activity
                          ? new Date(serviceMetrics.last_activity).toLocaleString()
                          : "N/A"}
                      </Td>
                      <Td>
                        <Text fontSize="xs">
                          {serviceMetrics.metrics?.blocked_requests && `Blocked: ${serviceMetrics.metrics.blocked_requests}`}
                          {serviceMetrics.metrics?.active_connections && ` | Active: ${serviceMetrics.metrics.active_connections}`}
                        </Text>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </CardBody>
          </Card>
        </Box>
      )}
    </VStack>
  );
};
