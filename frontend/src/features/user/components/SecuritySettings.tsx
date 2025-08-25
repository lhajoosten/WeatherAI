/**
 * SecuritySettings component for managing account security.
 */

import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Badge,
  Alert,
  AlertIcon,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react';
import React from 'react';
import { Shield, Key, Smartphone, AlertTriangle } from 'react-feather';

export const SecuritySettings: React.FC = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <VStack spacing={6} align="stretch">
      {/* Password Section */}
      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <HStack>
            <Key size={20} />
            <Heading size="md">Password</Heading>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontWeight="medium">Password</Text>
                <Text fontSize="sm" color="gray.500">
                  Last updated 3 months ago
                </Text>
              </VStack>
              <Button variant="outline" size="sm" isDisabled>
                Change Password
              </Button>
            </HStack>
            <Alert status="info" borderRadius="md">
              <AlertIcon />
              Password reset functionality coming soon.
            </Alert>
          </VStack>
        </CardBody>
      </Card>

      {/* Two-Factor Authentication */}
      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <HStack>
            <Smartphone size={20} />
            <Heading size="md">Two-Factor Authentication</Heading>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <HStack>
                  <Text fontWeight="medium">2FA Status</Text>
                  <Badge colorScheme="red" variant="subtle">
                    Disabled
                  </Badge>
                </HStack>
                <Text fontSize="sm" color="gray.500">
                  Add an extra layer of security to your account
                </Text>
              </VStack>
              <Button variant="outline" size="sm" isDisabled>
                Enable 2FA
              </Button>
            </HStack>
            
            <Alert status="warning" borderRadius="md">
              <AlertIcon />
              Two-factor authentication is not yet configured. Enable it to secure your account.
            </Alert>
            
            <Box p={4} bg="gray.50" borderRadius="md" border="1px solid" borderColor="gray.200">
              <Text fontSize="sm" color="gray.600">
                <strong>What is 2FA?</strong><br />
                Two-factor authentication adds an extra security step when signing in. 
                Even if someone knows your password, they won't be able to access your account without your phone.
              </Text>
            </Box>
          </VStack>
        </CardBody>
      </Card>

      {/* Security Recommendations */}
      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <HStack>
            <Shield size={20} />
            <Heading size="md">Security Recommendations</Heading>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Box p={4} borderRadius="md" border="1px solid" borderColor="yellow.200" bg="yellow.50">
              <HStack spacing={3} mb={2}>
                <AlertTriangle size={16} color="orange" />
                <Text fontWeight="medium" color="orange.700">
                  Action Recommended
                </Text>
              </HStack>
              <VStack spacing={2} align="start">
                <Text fontSize="sm" color="gray.700">
                  • Enable two-factor authentication for better security
                </Text>
                <Text fontSize="sm" color="gray.700">
                  • Consider updating your password if it's been a while
                </Text>
                <Text fontSize="sm" color="gray.700">
                  • Review your active sessions regularly
                </Text>
              </VStack>
            </Box>

            <Divider />

            <VStack spacing={3} align="stretch">
              <Heading size="sm" color="gray.700">
                Security Tips
              </Heading>
              <VStack spacing={2} align="start" fontSize="sm" color="gray.600">
                <Text>• Use a unique password that you don't use elsewhere</Text>
                <Text>• Keep your password private and secure</Text>
                <Text>• Log out of shared or public devices</Text>
                <Text>• Be cautious of phishing attempts</Text>
              </VStack>
            </VStack>
          </VStack>
        </CardBody>
      </Card>

      {/* Account Actions */}
      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md" color="red.600">Danger Zone</Heading>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Alert status="error" borderRadius="md">
              <AlertIcon />
              These actions are permanent and cannot be undone.
            </Alert>
            
            <Box p={4} borderRadius="md" border="1px solid" borderColor="red.200" bg="red.50">
              <VStack spacing={3} align="stretch">
                <HStack justify="space-between">
                  <VStack align="start" spacing={1}>
                    <Text fontWeight="medium" color="red.700">
                      Delete Account
                    </Text>
                    <Text fontSize="sm" color="red.600">
                      Permanently delete your account and all data
                    </Text>
                  </VStack>
                  <Button colorScheme="red" variant="outline" size="sm" isDisabled>
                    Delete Account
                  </Button>
                </HStack>
                <Text fontSize="xs" color="red.500">
                  Account deletion functionality coming soon.
                </Text>
              </VStack>
            </Box>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );
};