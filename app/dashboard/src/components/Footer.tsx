import { BoxProps, HStack, Link, Text } from "@chakra-ui/react";
import { ORGANIZATION_URL, REPO_URL } from "constants/Project";
import { useDashboard } from "contexts/DashboardContext";
import { FC } from "react";

export const Footer: FC<BoxProps> = (props) => {
  const { version } = useDashboard();
  return (
    <HStack w="full" py="0" position="relative" {...props}>
      <Text
        display="inline-block"
        flexGrow={1}
        textAlign="center"
        color="gray.500"
        fontSize="xs"
      >
        <Link color="blue.400" href={REPO_URL}>
          Enhanced Marzban
        </Link>
        {version ? ` (v${version}), ` : ", "}
        Enhanced with ⚡ by{" "}
        <Link color="blue.400" href="https://github.com/Kavis1/enhanced-marzban">
          Kavis1
        </Link>
        {" | Based on "}
        <Link color="blue.400" href={ORGANIZATION_URL}>
          Gozargah Marzban
        </Link>
      </Text>
    </HStack>
  );
};
