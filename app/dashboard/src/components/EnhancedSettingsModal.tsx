import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  HStack,
  Text,
  VStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useColorMode,
} from "@chakra-ui/react";
import {
  ShieldCheckIcon,
  CogIcon,
} from "@heroicons/react/24/outline";
import { FC } from "react";
import { useTranslation } from "react-i18next";
import { useDashboard } from "contexts/DashboardContext";
import { EnhancedSettings } from "../pages/EnhancedSettings";
import { EnhancedMonitoring } from "./EnhancedMonitoring";

export const EnhancedSettingsModal: FC = () => {
  const { t } = useTranslation();
  const { colorMode } = useColorMode();
  
  // Get modal state from dashboard context
  const isEditingEnhanced = useDashboard((state) => state.isEditingEnhanced);
  const onEditingEnhanced = useDashboard((state) => state.onEditingEnhanced);

  const handleClose = () => {
    onEditingEnhanced(false);
  };

  return (
    <Modal 
      isOpen={isEditingEnhanced} 
      onClose={handleClose} 
      size="6xl"
      scrollBehavior="inside"
    >
      <ModalOverlay />
      <ModalContent maxH="90vh">
        <ModalHeader>
          <HStack>
            <ShieldCheckIcon width="24" height="24" />
            <Text>Enhanced Marzban Settings & Monitoring</Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody p="0">
          <Tabs variant="enclosed" colorScheme="blue" h="full">
            <TabList px="6" pt="4">
              <Tab>🛡️ Enhanced Settings</Tab>
              <Tab>📊 Service Monitoring</Tab>
            </TabList>

            <TabPanels h="full">
              {/* Enhanced Settings Tab */}
              <TabPanel p="0" h="full">
                <EnhancedSettings />
              </TabPanel>

              {/* Service Monitoring Tab */}
              <TabPanel p="6" h="full">
                <EnhancedMonitoring />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ModalBody>

        <ModalFooter>
          <HStack spacing="3">
            <Button variant="ghost" onClick={handleClose}>
              Close
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
