/**
 * User management pages.
 */

import { Box, Heading, Text, VStack } from '@chakra-ui/react';
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import { PreferencesForm } from '../components/PreferencesForm';
import { ProfileEdit } from '../components/ProfileEdit';
import { ProfileOverview } from '../components/ProfileOverview';
import { SecuritySettings } from '../components/SecuritySettings';

export const UserProfile: React.FC = () => (
  <Box p={6}>
    <VStack spacing={6} align="stretch">
      <Box>
        <Heading size="lg" mb={2}>Profile</Heading>
        <Text color="gray.600">Manage your personal information and preferences.</Text>
      </Box>
      <ProfileOverview />
    </VStack>
  </Box>
);

export const UserProfileEdit: React.FC = () => (
  <Box p={6}>
    <VStack spacing={6} align="stretch">
      <Box>
        <Heading size="lg" mb={2}>Edit Profile</Heading>
        <Text color="gray.600">Update your personal information.</Text>
      </Box>
      <ProfileEdit />
    </VStack>
  </Box>
);

export const UserSettings: React.FC = () => (
  <Box p={6}>
    <VStack spacing={6} align="stretch">
      <Box>
        <Heading size="lg" mb={2}>Preferences</Heading>
        <Text color="gray.600">Customize your WeatherAI experience.</Text>
      </Box>
      <PreferencesForm />
    </VStack>
  </Box>
);

export const UserSecurity: React.FC = () => (
  <Box p={6}>
    <VStack spacing={6} align="stretch">
      <Box>
        <Heading size="lg" mb={2}>Security</Heading>
        <Text color="gray.600">Manage your account security settings.</Text>
      </Box>
      <SecuritySettings />
    </VStack>
  </Box>
);

export const UserSessions: React.FC = () => (
  <Box p={6}>
    <VStack spacing={6} align="stretch">
      <Box>
        <Heading size="lg" mb={2}>Active Sessions</Heading>
        <Text color="gray.600">View and manage your active sessions.</Text>
      </Box>
      <Box p={4} bg="gray.50" borderRadius="md" border="1px solid" borderColor="gray.200">
        <Text color="gray.500" fontStyle="italic">
          Session management coming soon...
        </Text>
      </Box>
    </VStack>
  </Box>
);

export const UserApiTokens: React.FC = () => (
  <Box p={6}>
    <VStack spacing={6} align="stretch">
      <Box>
        <Heading size="lg" mb={2}>API Tokens</Heading>
        <Text color="gray.600">Manage your API access tokens.</Text>
      </Box>
      <Box p={4} bg="gray.50" borderRadius="md" border="1px solid" borderColor="gray.200">
        <Text color="gray.500" fontStyle="italic">
          API token management coming soon...
        </Text>
      </Box>
    </VStack>
  </Box>
);

/**
 * User management routing component.
 */
export const UserManagement: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/user/profile" replace />} />
      <Route path="/profile" element={<UserProfile />} />
      <Route path="/edit" element={<UserProfileEdit />} />
      <Route path="/settings" element={<UserSettings />} />
      <Route path="/security" element={<UserSecurity />} />
      <Route path="/sessions" element={<UserSessions />} />
      <Route path="/api-tokens" element={<UserApiTokens />} />
      <Route path="*" element={<Navigate to="/user/profile" replace />} />
    </Routes>
  );
};