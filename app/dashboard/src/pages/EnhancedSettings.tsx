import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardHeader,
  CardBody,
  Switch,
  Button,
  Input,
  Select,
  Textarea,
  Badge,
  Alert,
  AlertIcon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useToast,
  useColorMode,
} from "@chakra-ui/react";
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  GlobeAltIcon,
  NoSymbolIcon,
  ChartBarIcon,
  CogIcon,
} from "@heroicons/react/24/outline";
import { FC, useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { fetch } from "service/http";

interface EnhancedConfig {
  two_factor_auth: {
    enabled: boolean;
    description: string;
  };
  fail2ban_integration: {
    enabled: boolean;
    log_path: string;
    max_violations: number;
    description: string;
  };
  connection_limiting: {
    enabled: boolean;
    default_max_connections: number;
    description: string;
  };
  dns_override: {
    enabled: boolean;
    dns_servers: string[];
    description: string;
  };
  ad_blocking: {
    enabled: boolean;
    update_interval: number;
    description: string;
  };
}

const EnhancedSettingsCard: FC<{
  title: string;
  description: string;
  icon: React.ReactElement;
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  children?: React.ReactNode;
  status?: "success" | "warning" | "error";
}> = ({ title, description, icon, enabled, onToggle, children, status = "success" }) => {
  const { colorMode } = useColorMode();
  
  const statusColors = {
    success: "green.400",
    warning: "yellow.400",
    error: "red.400",
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
              bg={enabled ? statusColors[status] : "gray.400"}
              color="white"
            >
              {icon}
            </Box>
            <VStack align="start" spacing="0">
              <Text fontWeight="semibold" fontSize="lg">
                {title}
              </Text>
              <Text fontSize="sm" color="gray.500" _dark={{ color: "gray.400" }}>
                {description}
              </Text>
            </VStack>
          </HStack>
          <VStack align="end" spacing="1">
            <Switch
              isChecked={enabled}
              onChange={(e) => onToggle(e.target.checked)}
              colorScheme={status === "success" ? "green" : status === "warning" ? "yellow" : "red"}
              size="lg"
            />
            <Badge
              colorScheme={enabled ? (status === "success" ? "green" : status === "warning" ? "yellow" : "red") : "gray"}
              size="sm"
            >
              {enabled ? "Active" : "Disabled"}
            </Badge>
          </VStack>
        </HStack>
      </CardHeader>
      {enabled && children && (
        <CardBody pt="0">
          {children}
        </CardBody>
      )}
    </Card>
  );
};

export const EnhancedSettings: FC = () => {
  const { t } = useTranslation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<EnhancedConfig | null>(null);

  // Fetch enhanced configuration
  const { data: configData, isLoading } = useQuery({
    queryKey: "enhanced-config",
    queryFn: () => fetch("/api/enhanced/config"),
    onSuccess: (data) => {
      setConfig(data.enhanced_features);
    },
  });

  // Update configuration mutation
  const updateConfigMutation = useMutation({
    mutationFn: (newConfig: Partial<EnhancedConfig>) =>
      fetch("/api/enhanced/config", {
        method: "POST",
        body: JSON.stringify(newConfig),
      }),
    onSuccess: () => {
      toast({
        title: "Configuration Updated",
        description: "Enhanced features configuration has been updated successfully.",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      queryClient.invalidateQueries("enhanced-config");
    },
    onError: () => {
      toast({
        title: "Update Failed",
        description: "Failed to update configuration. Please try again.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const handleToggleFeature = (feature: keyof EnhancedConfig, enabled: boolean) => {
    if (!config) return;
    
    const updatedConfig = {
      ...config,
      [feature]: {
        ...config[feature],
        enabled,
      },
    };
    
    setConfig(updatedConfig);
    updateConfigMutation.mutate({ [feature]: updatedConfig[feature] });
  };

  const handleUpdateFeatureConfig = (feature: keyof EnhancedConfig, updates: any) => {
    if (!config) return;
    
    const updatedConfig = {
      ...config,
      [feature]: {
        ...config[feature],
        ...updates,
      },
    };
    
    setConfig(updatedConfig);
    updateConfigMutation.mutate({ [feature]: updatedConfig[feature] });
  };

  if (isLoading || !config) {
    return (
      <Box p="6">
        <Text>Loading Enhanced Settings...</Text>
      </Box>
    );
  }

  return (
    <VStack spacing="6" p="6" align="stretch">
      <Box>
        <Text fontSize="2xl" fontWeight="bold" mb="2">
          🛡️ Enhanced Security & Features
        </Text>
        <Text color="gray.600" _dark={{ color: "gray.400" }}>
          Configure advanced security features and monitoring capabilities
        </Text>
      </Box>

      <Alert status="info" borderRadius="md">
        <AlertIcon />
        Enhanced features provide additional security, monitoring, and control capabilities.
        Enable only the features you need for your deployment.
      </Alert>

      <Tabs variant="enclosed" colorScheme="blue">
        <TabList>
          <Tab>🔐 Security</Tab>
          <Tab>📊 Monitoring</Tab>
          <Tab>🌐 Network</Tab>
          <Tab>⚙️ System</Tab>
        </TabList>

        <TabPanels>
          {/* Security Tab */}
          <TabPanel>
            <VStack spacing="4" align="stretch">
              <EnhancedSettingsCard
                title="Two-Factor Authentication"
                description="Enhanced security for admin accounts with TOTP"
                icon={<ShieldCheckIcon width="20" height="20" />}
                enabled={config.two_factor_auth.enabled}
                onToggle={(enabled) => handleToggleFeature("two_factor_auth", enabled)}
                status="success"
              >
                <VStack spacing="3" align="stretch">
                  <Text fontSize="sm" fontWeight="medium">2FA Configuration</Text>
                  <HStack>
                    <Button size="sm" colorScheme="blue">
                      Generate QR Code
                    </Button>
                    <Button size="sm" variant="outline">
                      Reset Secret
                    </Button>
                  </HStack>
                </VStack>
              </EnhancedSettingsCard>

              <EnhancedSettingsCard
                title="Fail2ban Integration"
                description="Automatic traffic monitoring and user suspension"
                icon={<ExclamationTriangleIcon width="20" height="20" />}
                enabled={config.fail2ban_integration.enabled}
                onToggle={(enabled) => handleToggleFeature("fail2ban_integration", enabled)}
                status="warning"
              >
                <VStack spacing="3" align="stretch">
                  <HStack>
                    <Text fontSize="sm" fontWeight="medium" minW="120px">Max Violations:</Text>
                    <Input
                      size="sm"
                      type="number"
                      value={config.fail2ban_integration.max_violations}
                      onChange={(e) => handleUpdateFeatureConfig("fail2ban_integration", {
                        max_violations: parseInt(e.target.value) || 3
                      })}
                      maxW="100px"
                    />
                  </HStack>
                  <HStack>
                    <Text fontSize="sm" fontWeight="medium" minW="120px">Log Path:</Text>
                    <Input
                      size="sm"
                      value={config.fail2ban_integration.log_path}
                      onChange={(e) => handleUpdateFeatureConfig("fail2ban_integration", {
                        log_path: e.target.value
                      })}
                    />
                  </HStack>
                </VStack>
              </EnhancedSettingsCard>
            </VStack>
          </TabPanel>

          {/* Monitoring Tab */}
          <TabPanel>
            <VStack spacing="4" align="stretch">
              <EnhancedSettingsCard
                title="Connection Limiting"
                description="Limit simultaneous connections per user"
                icon={<ClockIcon width="20" height="20" />}
                enabled={config.connection_limiting.enabled}
                onToggle={(enabled) => handleToggleFeature("connection_limiting", enabled)}
                status="success"
              >
                <HStack>
                  <Text fontSize="sm" fontWeight="medium" minW="150px">Default Max Connections:</Text>
                  <Input
                    size="sm"
                    type="number"
                    value={config.connection_limiting.default_max_connections}
                    onChange={(e) => handleUpdateFeatureConfig("connection_limiting", {
                      default_max_connections: parseInt(e.target.value) || 5
                    })}
                    maxW="100px"
                  />
                </HStack>
              </EnhancedSettingsCard>
            </VStack>
          </TabPanel>

          {/* Network Tab */}
          <TabPanel>
            <VStack spacing="4" align="stretch">
              <EnhancedSettingsCard
                title="DNS Override"
                description="Custom DNS rules and domain redirection"
                icon={<GlobeAltIcon width="20" height="20" />}
                enabled={config.dns_override.enabled}
                onToggle={(enabled) => handleToggleFeature("dns_override", enabled)}
                status="success"
              >
                <VStack spacing="3" align="stretch">
                  <Text fontSize="sm" fontWeight="medium">DNS Servers (comma-separated):</Text>
                  <Input
                    size="sm"
                    value={config.dns_override.dns_servers.join(", ")}
                    onChange={(e) => handleUpdateFeatureConfig("dns_override", {
                      dns_servers: e.target.value.split(",").map(s => s.trim())
                    })}
                    placeholder="1.1.1.1, 8.8.8.8"
                  />
                </VStack>
              </EnhancedSettingsCard>

              <EnhancedSettingsCard
                title="Ad-blocking"
                description="Block advertisements and tracking domains"
                icon={<NoSymbolIcon width="20" height="20" />}
                enabled={config.ad_blocking.enabled}
                onToggle={(enabled) => handleToggleFeature("ad_blocking", enabled)}
                status="success"
              >
                <HStack>
                  <Text fontSize="sm" fontWeight="medium" minW="120px">Update Interval (hours):</Text>
                  <Input
                    size="sm"
                    type="number"
                    value={config.ad_blocking.update_interval / 3600}
                    onChange={(e) => handleUpdateFeatureConfig("ad_blocking", {
                      update_interval: (parseInt(e.target.value) || 24) * 3600
                    })}
                    maxW="100px"
                  />
                </HStack>
              </EnhancedSettingsCard>
            </VStack>
          </TabPanel>

          {/* System Tab */}
          <TabPanel>
            <VStack spacing="4" align="stretch">
              <Card>
                <CardHeader>
                  <HStack>
                    <ChartBarIcon width="20" height="20" />
                    <Text fontWeight="semibold">System Actions</Text>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <VStack spacing="3" align="stretch">
                    <HStack>
                      <Button colorScheme="blue" size="sm">
                        Restart Enhanced Services
                      </Button>
                      <Button variant="outline" size="sm">
                        View Service Status
                      </Button>
                    </HStack>
                    <HStack>
                      <Button colorScheme="green" size="sm">
                        Initialize Services
                      </Button>
                      <Button colorScheme="red" variant="outline" size="sm">
                        Cleanup Services
                      </Button>
                    </HStack>
                  </VStack>
                </CardBody>
              </Card>
            </VStack>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </VStack>
  );
};
