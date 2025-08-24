/**
 * AvatarUploader component for handling avatar uploads
 */

import React, { useRef } from 'react';
import {
  VStack,
  Avatar,
  Button,
  Text,
  Alert,
  AlertIcon,
  useColorModeValue,
} from '@chakra-ui/react';
import { Camera } from 'react-feather';

interface AvatarUploaderProps {
  currentAvatar?: string;
  displayName?: string;
  onUpload: (file: File) => void;
  isLoading?: boolean;
  error?: string;
}

export const AvatarUploader: React.FC<AvatarUploaderProps> = ({
  currentAvatar,
  displayName,
  onUpload,
  isLoading = false,
  error,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        return;
      }
      
      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        return;
      }
      
      onUpload(file);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <VStack spacing={4}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />

      {/* Avatar Preview */}
      <Avatar
        size="2xl"
        name={displayName || 'User'}
        src={currentAvatar}
        bg="blue.500"
        border="4px solid"
        borderColor={useColorModeValue('white', 'gray.700')}
        shadow="lg"
      />

      {/* Upload Button */}
      <Button
        leftIcon={<Camera size={16} />}
        onClick={triggerFileSelect}
        isLoading={isLoading}
        loadingText="Uploading..."
        variant="outline"
        size="sm"
        colorScheme="blue"
      >
        Change Avatar
      </Button>

      {/* Helper Text */}
      <Text fontSize="xs" color="gray.500" textAlign="center" maxW="200px">
        Upload a photo up to 5MB. JPG, PNG, or GIF formats accepted.
      </Text>

      {/* Error Message */}
      {error && (
        <Alert status="error" borderRadius="md" size="sm">
          <AlertIcon />
          {error}
        </Alert>
      )}
    </VStack>
  );
};