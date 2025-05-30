import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  Select,
  Switch,
  Badge,
  Card,
  CardHeader,
  CardBody,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  useToast,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Textarea,
  Alert,
  AlertIcon,
} from "@chakra-ui/react";
import {
  ClockIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  NoSymbolIcon,
  GlobeAltIcon,
} from "@heroicons/react/24/outline";
import { FC, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQueryClient } from "react-query";
import { fetch } from "service/http";

interface EnhancedUserSettings {
  username: string;
  connection_limit?: number;
  dns_override_enabled?: boolean;
  custom_dns_servers?: string[];
  adblock_enabled?: boolean;
  fail2ban_monitoring?: boolean;
  traffic_analysis?: boolean;
  custom_rules?: string;
}

interface EnhancedUserControlsProps {
  username: string;
  currentSettings?: EnhancedUserSettings;
  onUpdate?: (settings: EnhancedUserSettings) => void;
}

export const EnhancedUserControls: FC<EnhancedUserControlsProps> = ({
  username,
  currentSettings,
  onUpdate,
}) => {
  const { t } = useTranslation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const [settings, setSettings] = useState<EnhancedUserSettings>({
    username,
    connection_limit: currentSettings?.connection_limit || 5,
    dns_override_enabled: currentSettings?.dns_override_enabled || false,
    custom_dns_servers: currentSettings?.custom_dns_servers || ["1.1.1.1", "8.8.8.8"],
    adblock_enabled: currentSettings?.adblock_enabled || true,
    fail2ban_monitoring: currentSettings?.fail2ban_monitoring || true,
    traffic_analysis: currentSettings?.traffic_analysis || true,
    custom_rules: currentSettings?.custom_rules || "",
  });

  // Update user enhanced settings
  const updateSettingsMutation = useMutation({
    mutationFn: (newSettings: EnhancedUserSettings) =>
      fetch(`/api/enhanced/users/${username}/settings`, {
        method: "POST",
        body: JSON.stringify(newSettings),
      }),
    onSuccess: () => {
      toast({
        title: "Settings Updated",
        description: `Enhanced settings for ${username} have been updated successfully.`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      onUpdate?.(settings);
      onClose();
      queryClient.invalidateQueries(["user", username]);
    },
    onError: () => {
      toast({
        title: "Update Failed",
        description: "Failed to update enhanced settings. Please try again.",
        status: "error",
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const handleSave = () => {
    updateSettingsMutation.mutate(settings);
  };

  const handleReset = () => {
    setSettings({
      username,
      connection_limit: 5,
      dns_override_enabled: false,
      custom_dns_servers: ["1.1.1.1", "8.8.8.8"],
      adblock_enabled: true,
      fail2ban_monitoring: true,
      traffic_analysis: true,
      custom_rules: "",
    });
  };

  return (
    <>
      <Button
        size="sm"
        colorScheme="purple"
        variant="outline"
        leftIcon={<ShieldCheckIcon width="16" height="16" />}
        onClick={onOpen}
      >
        Enhanced Settings
      </Button>

      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            <HStack>
              <ShieldCheckIcon width="24" height="24" />
              <Text>Enhanced Settings for {username}</Text>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            <VStack spacing="6" align="stretch">
              <Alert status="info" borderRadius="md">
                <AlertIcon />
                Configure Enhanced features for this specific user. These settings override global defaults.
              </Alert>

              {/* Connection Limiting */}
              <Card>
                <CardHeader pb="2">
                  <HStack>
                    <ClockIcon width="20" height="20" />
                    <Text fontWeight="semibold">Connection Limiting</Text>
                  </HStack>
                </CardHeader>
                <CardBody pt="0">
                  <FormControl>
                    <FormLabel fontSize="sm">Maximum Simultaneous Connections</FormLabel>
                    <NumberInput
                      value={settings.connection_limit}
                      onChange={(_, value) => setSettings({ ...settings, connection_limit: value })}
                      min={1}
                      max={50}
                      size="sm"
                    >
                      <NumberInputField />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>
                    <Text fontSize="xs" color="gray.500" mt="1">
                      Limit the number of simultaneous connections for this user
                    </Text>
                  </FormControl>
                </CardBody>
              </Card>

              {/* DNS Override */}
              <Card>
                <CardHeader pb="2">
                  <HStack justify="space-between">
                    <HStack>
                      <GlobeAltIcon width="20" height="20" />
                      <Text fontWeight="semibold">DNS Override</Text>
                    </HStack>
                    <Switch
                      isChecked={settings.dns_override_enabled}
                      onChange={(e) => setSettings({ ...settings, dns_override_enabled: e.target.checked })}
                      colorScheme="blue"
                    />
                  </HStack>
                </CardHeader>
                {settings.dns_override_enabled && (
                  <CardBody pt="0">
                    <FormControl>
                      <FormLabel fontSize="sm">Custom DNS Servers</FormLabel>
                      <Input
                        size="sm"
                        value={settings.custom_dns_servers?.join(", ")}
                        onChange={(e) => setSettings({
                          ...settings,
                          custom_dns_servers: e.target.value.split(",").map(s => s.trim())
                        })}
                        placeholder="1.1.1.1, 8.8.8.8, 9.9.9.9"
                      />
                      <Text fontSize="xs" color="gray.500" mt="1">
                        Comma-separated list of DNS servers for this user
                      </Text>
                    </FormControl>
                  </CardBody>
                )}
              </Card>

              {/* Ad-blocking */}
              <Card>
                <CardHeader pb="2">
                  <HStack justify="space-between">
                    <HStack>
                      <NoSymbolIcon width="20" height="20" />
                      <Text fontWeight="semibold">Ad-blocking</Text>
                    </HStack>
                    <Switch
                      isChecked={settings.adblock_enabled}
                      onChange={(e) => setSettings({ ...settings, adblock_enabled: e.target.checked })}
                      colorScheme="green"
                    />
                  </HStack>
                </CardHeader>
                <CardBody pt="0">
                  <Text fontSize="sm" color="gray.600">
                    {settings.adblock_enabled 
                      ? "Ad-blocking is enabled for this user"
                      : "Ad-blocking is disabled for this user"
                    }
                  </Text>
                </CardBody>
              </Card>

              {/* Security Monitoring */}
              <Card>
                <CardHeader pb="2">
                  <HStack>
                    <ExclamationTriangleIcon width="20" height="20" />
                    <Text fontWeight="semibold">Security Monitoring</Text>
                  </HStack>
                </CardHeader>
                <CardBody pt="0">
                  <VStack spacing="3" align="stretch">
                    <HStack justify="space-between">
                      <Text fontSize="sm">Fail2ban Monitoring</Text>
                      <Switch
                        isChecked={settings.fail2ban_monitoring}
                        onChange={(e) => setSettings({ ...settings, fail2ban_monitoring: e.target.checked })}
                        colorScheme="red"
                        size="sm"
                      />
                    </HStack>
                    <HStack justify="space-between">
                      <Text fontSize="sm">Traffic Analysis</Text>
                      <Switch
                        isChecked={settings.traffic_analysis}
                        onChange={(e) => setSettings({ ...settings, traffic_analysis: e.target.checked })}
                        colorScheme="orange"
                        size="sm"
                      />
                    </HStack>
                  </VStack>
                </CardBody>
              </Card>

              {/* Custom Rules */}
              <Card>
                <CardHeader pb="2">
                  <Text fontWeight="semibold">Custom Rules</Text>
                </CardHeader>
                <CardBody pt="0">
                  <FormControl>
                    <FormLabel fontSize="sm">Custom Configuration Rules</FormLabel>
                    <Textarea
                      size="sm"
                      value={settings.custom_rules}
                      onChange={(e) => setSettings({ ...settings, custom_rules: e.target.value })}
                      placeholder="Enter custom rules or configuration for this user..."
                      rows={4}
                    />
                    <Text fontSize="xs" color="gray.500" mt="1">
                      Advanced: Custom rules in JSON format for specific user configurations
                    </Text>
                  </FormControl>
                </CardBody>
              </Card>

              {/* Current Status */}
              <Card bg="gray.50" _dark={{ bg: "gray.800" }}>
                <CardHeader pb="2">
                  <Text fontWeight="semibold">Current Enhanced Status</Text>
                </CardHeader>
                <CardBody pt="0">
                  <HStack wrap="wrap" spacing="2">
                    <Badge colorScheme={settings.connection_limit && settings.connection_limit > 0 ? "green" : "gray"}>
                      Connection Limit: {settings.connection_limit || "Unlimited"}
                    </Badge>
                    <Badge colorScheme={settings.dns_override_enabled ? "blue" : "gray"}>
                      DNS Override: {settings.dns_override_enabled ? "Enabled" : "Disabled"}
                    </Badge>
                    <Badge colorScheme={settings.adblock_enabled ? "green" : "gray"}>
                      Ad-blocking: {settings.adblock_enabled ? "Enabled" : "Disabled"}
                    </Badge>
                    <Badge colorScheme={settings.fail2ban_monitoring ? "red" : "gray"}>
                      Fail2ban: {settings.fail2ban_monitoring ? "Monitoring" : "Disabled"}
                    </Badge>
                    <Badge colorScheme={settings.traffic_analysis ? "orange" : "gray"}>
                      Traffic Analysis: {settings.traffic_analysis ? "Enabled" : "Disabled"}
                    </Badge>
                  </HStack>
                </CardBody>
              </Card>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <HStack spacing="3">
              <Button variant="outline" onClick={handleReset} size="sm">
                Reset to Defaults
              </Button>
              <Button variant="ghost" onClick={onClose} size="sm">
                Cancel
              </Button>
              <Button
                colorScheme="blue"
                onClick={handleSave}
                isLoading={updateSettingsMutation.isLoading}
                size="sm"
              >
                Save Settings
              </Button>
            </HStack>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};
