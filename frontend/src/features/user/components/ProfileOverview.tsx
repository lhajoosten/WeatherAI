/**
 * ProfileOverview component displays user profile information.
 */

import {
  Box,
  VStack,
  HStack,
  Text,
  Avatar,
  Button,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Badge,
  Divider,
  Skeleton,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import React from 'react';
import { Edit2, Mail, Clock, Globe, Grid } from 'react-feather';
import { Link as RouterLink } from 'react-router-dom';

import { useUserMe } from '../hooks/useUser';

export const ProfileOverview: React.FC = () => {
  const { data: userData, isLoading, error } = useUserMe();

  if (isLoading) {
    return (
      <Card>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <HStack spacing={4}>
              <Skeleton height="80px" width="80px" borderRadius="full" />
              <VStack align="start" spacing={2} flex={1}>
                <Skeleton height="24px" width="200px" />
                <Skeleton height="16px" width="150px" />
              </VStack>
            </HStack>
            <Divider />
            <VStack spacing={3} align="stretch">
              <Skeleton height="20px" width="100%" />
              <Skeleton height="20px" width="80%" />
              <Skeleton height="20px" width="60%" />
            </VStack>
          </VStack>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        Failed to load profile information. Please try again.
      </Alert>
    );
  }

  const profile = userData?.profile;
  const displayName = profile?.display_name || 'Anonymous User';
  const avatarUrl = profile?.avatar_url;

  return (
    <Card>
      <CardHeader>
        <HStack justify="space-between">
          <Heading size="md">Profile Information</Heading>
          <Button
            as={RouterLink}
            to="/user/edit"
            leftIcon={<Edit2 size={16} />}
            colorScheme="blue"
            variant="outline"
            size="sm"
          >
            Edit Profile
          </Button>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={6} align="stretch">
          {/* Profile Header */}
          <HStack spacing={4}>
            <Avatar
              size="xl"
              name={displayName}
              src={avatarUrl}
              bg="blue.500"
            />
            <VStack align="start" spacing={1} flex={1}>
              <Heading size="lg">{displayName}</Heading>
              <HStack>
                <Mail size={16} />
                <Text color="gray.600">{userData?.email}</Text>
              </HStack>
              {profile?.bio && (
                <Text color="gray.500" mt={2}>
                  {profile.bio}
                </Text>
              )}
            </VStack>
          </HStack>

          <Divider />

          {/* Profile Details */}
          <VStack spacing={4} align="stretch">
            <Heading size="sm" color="gray.700">
              Details
            </Heading>

            <VStack spacing={3} align="stretch">
              <HStack justify="space-between">
                <HStack>
                  <Clock size={16} />
                  <Text>Timezone</Text>
                </HStack>
                <Text color="gray.600">
                  {profile?.time_zone || userData?.timezone || 'UTC'}
                </Text>
              </HStack>

              {profile?.locale && (
                <HStack justify="space-between">
                  <HStack>
                    <Globe size={16} />
                    <Text>Language</Text>
                  </HStack>
                  <Text color="gray.600">{profile.locale}</Text>
                </HStack>
              )}

              <HStack justify="space-between">
                <HStack>
                  <Grid size={16} />
                  <Text>Theme Preference</Text>
                </HStack>
                <Badge
                  colorScheme={
                    profile?.theme_preference === 'dark'
                      ? 'purple'
                      : profile?.theme_preference === 'light'
                      ? 'yellow'
                      : 'gray'
                  }
                  variant="subtle"
                >
                  {profile?.theme_preference || 'System'}
                </Badge>
              </HStack>

              <HStack justify="space-between">
                <Text>Member since</Text>
                <Text color="gray.600">
                  {new Date(userData?.created_at || '').toLocaleDateString()}
                </Text>
              </HStack>
            </VStack>
          </VStack>

          {/* Empty State */}
          {!profile?.display_name && !profile?.bio && (
            <Box p={4} bg="gray.50" borderRadius="md" textAlign="center">
              <Text color="gray.500" mb={3}>
                Your profile is incomplete. Add some personal information to get started!
              </Text>
              <Button
                as={RouterLink}
                to="/user/edit"
                colorScheme="blue"
                size="sm"
              >
                Complete Profile
              </Button>
            </Box>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};