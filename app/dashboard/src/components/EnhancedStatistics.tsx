import { Box, BoxProps, Card, chakra, HStack, Text, Badge } from "@chakra-ui/react";
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";
import { FC, PropsWithChildren, ReactElement } from "react";
import { useTranslation } from "react-i18next";
import { useQuery } from "react-query";
import { fetch } from "service/http";
import { formatBytes, numberWithCommas } from "utils/formatByte";

const SecurityIcon = chakra(ShieldCheckIcon, {
  baseStyle: {
    w: 5,
    h: 5,
    position: "relative",
    zIndex: "2",
  },
});

const ThreatIcon = chakra(ExclamationTriangleIcon, {
  baseStyle: {
    w: 5,
    h: 5,
    position: "relative",
    zIndex: "2",
  },
});

const ConnectionIcon = chakra(ClockIcon, {
  baseStyle: {
    w: 5,
    h: 5,
    position: "relative",
    zIndex: "2",
  },
});

const PerformanceIcon = chakra(ChartBarIcon, {
  baseStyle: {
    w: 5,
    h: 5,
    position: "relative",
    zIndex: "2",
  },
});

interface EnhancedStatisticCardProps extends PropsWithChildren {
  title: string;
  content: ReactElement | string | number | null;
  icon: ReactElement;
  status?: "success" | "warning" | "error";
}

const EnhancedStatisticCard: FC<EnhancedStatisticCardProps> = ({
  title,
  content,
  icon,
  status = "success",
}) => {
  const statusColors = {
    success: "green.400",
    warning: "yellow.400",
    error: "red.400",
  };

  return (
    <Card
      p="6"
      bg="white"
      _dark={{
        bg: "gray.750",
      }}
      borderRadius="12px"
      border="1px solid"
      borderColor="light-border"
      _dark={{
        borderColor: "gray.600",
      }}
      position="relative"
      overflow="hidden"
      minH="120px"
    >
      <HStack>
        <Box
          p="2"
          borderRadius="8px"
          bg={statusColors[status]}
          color="white"
          position="relative"
          _after={{
            content: `""`,
            position: "absolute",
            top: "-5px",
            left: "-5px",
            bg: statusColors[status],
            display: "block",
            w: "calc(100% + 10px)",
            h: "calc(100% + 10px)",
            borderRadius: "8px",
            opacity: ".4",
            z: "1",
          }}
        >
          {icon}
        </Box>
        <Text
          color="gray.600"
          _dark={{
            color: "gray.300",
          }}
          fontWeight="medium"
          textTransform="capitalize"
          fontSize="sm"
        >
          {title}
        </Text>
      </HStack>
      <Box fontSize="2xl" fontWeight="semibold" mt="2">
        {content}
      </Box>
    </Card>
  );
};

export const EnhancedStatisticsQueryKey = "enhanced-statistics-query-key";

export const EnhancedStatistics: FC<BoxProps> = (props) => {
  const { data: enhancedData } = useQuery({
    queryKey: EnhancedStatisticsQueryKey,
    queryFn: () => fetch("/api/enhanced/stats"),
    refetchInterval: 10000,
    retry: false,
    onError: () => {
      // Enhanced stats not available, that's ok
    },
  });

  const { t } = useTranslation();

  // Default values if enhanced stats are not available
  const defaultStats = {
    blocked_threats: 0,
    active_connections: 0,
    fail2ban_bans: 0,
    performance_score: 95,
  };

  const stats = enhancedData || defaultStats;

  return (
    <Box {...props}>
      <Text fontSize="lg" fontWeight="semibold" mb="4" color="blue.500">
        🛡️ Enhanced Security & Performance
      </Text>
      <HStack
        justifyContent="space-between"
        gap={0}
        columnGap={{ lg: 4, md: 0 }}
        rowGap={{ lg: 0, base: 4 }}
        display="flex"
        flexDirection={{ lg: "row", base: "column" }}
      >
        <EnhancedStatisticCard
          title="Blocked Threats"
          content={
            <HStack alignItems="center">
              <Text>{numberWithCommas(stats.blocked_threats)}</Text>
              <Badge colorScheme="green" size="sm">
                Protected
              </Badge>
            </HStack>
          }
          icon={<SecurityIcon />}
          status="success"
        />
        <EnhancedStatisticCard
          title="Active Connections"
          content={numberWithCommas(stats.active_connections)}
          icon={<ConnectionIcon />}
          status="success"
        />
        <EnhancedStatisticCard
          title="Fail2ban Bans"
          content={numberWithCommas(stats.fail2ban_bans)}
          icon={<ThreatIcon />}
          status={stats.fail2ban_bans > 10 ? "warning" : "success"}
        />
        <EnhancedStatisticCard
          title="Performance"
          content={
            <HStack alignItems="center">
              <Text>{stats.performance_score}%</Text>
              <Badge 
                colorScheme={stats.performance_score > 90 ? "green" : stats.performance_score > 70 ? "yellow" : "red"}
                size="sm"
              >
                {stats.performance_score > 90 ? "Excellent" : stats.performance_score > 70 ? "Good" : "Poor"}
              </Badge>
            </HStack>
          }
          icon={<PerformanceIcon />}
          status={stats.performance_score > 90 ? "success" : stats.performance_score > 70 ? "warning" : "error"}
        />
      </HStack>
    </Box>
  );
};
