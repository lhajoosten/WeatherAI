/**
 * AuthLayout - Modern wrapper for authentication forms
 */

import React, { ReactNode } from 'react';
import {
  Box,
  Flex,
  VStack,
  Heading,
  Text,
  Container,
  useColorModeValue,
} from '@chakra-ui/react';
import { Cloud } from 'react-feather';

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle?: string;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({ children, title, subtitle }) => {
  const bgGradient = useColorModeValue(
    'linear(to-br, blue.50, indigo.100)',
    'linear(to-br, gray.900, blue.900)'
  );
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Flex
      minH="100vh"
      align="center"
      justify="center"
      bgGradient={bgGradient}
      p={{ base: 4, md: 8 }}
    >
      <Container maxW="md" w="full">
        <VStack spacing={8} align="stretch">
          {/* Header */}
          <VStack spacing={4} textAlign="center">
            <Box
              p={4}
              bg={useColorModeValue('white', 'gray.700')}
              borderRadius="2xl"
              shadow="lg"
              border="1px solid"
              borderColor={borderColor}
            >
              <Cloud size={32} color={useColorModeValue('#3182ce', '#63b3ed')} />
            </Box>
            <VStack spacing={2}>
              <Heading size="xl" color={useColorModeValue('gray.800', 'white')}>
                WeatherAI
              </Heading>
              <Text color={useColorModeValue('gray.600', 'gray.300')} fontSize="lg">
                Your intelligent weather companion
              </Text>
            </VStack>
          </VStack>

          {/* Auth Form */}
          <Box
            bg={cardBg}
            p={{ base: 6, md: 8 }}
            borderRadius="2xl"
            shadow="2xl"
            border="1px solid"
            borderColor={borderColor}
          >
            <VStack spacing={6} align="stretch">
              <VStack spacing={2} textAlign="center">
                <Heading size="lg" color={useColorModeValue('gray.800', 'white')}>
                  {title}
                </Heading>
                {subtitle && (
                  <Text color={useColorModeValue('gray.600', 'gray.300')}>
                    {subtitle}
                  </Text>
                )}
              </VStack>
              {children}
            </VStack>
          </Box>
        </VStack>
      </Container>
    </Flex>
  );
};