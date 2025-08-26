/**
 * Modern LoginComponent with improved UX
 */

import React, { useState } from 'react';
import {
  VStack,
  HStack,
  FormControl,
  FormLabel,
  FormErrorMessage,
  Input,
  InputGroup,
  InputRightElement,
  Button,
  Text,
  Link,
  Alert,
  AlertIcon,
  Checkbox,
  useColorModeValue,
} from '@chakra-ui/react';
import { Eye, EyeOff, Mail, Lock } from 'react-feather';
import { useAuth } from '../contexts/AuthContext';

interface LoginComponentProps {
  onSwitchToRegister: () => void;
}

export const LoginComponent: React.FC<LoginComponentProps> = ({ onSwitchToRegister }) => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState('');

  const inputBg = useColorModeValue('gray.50', 'gray.700');
  const inputBorder = useColorModeValue('gray.200', 'gray.600');
  const inputFocusBorder = useColorModeValue('blue.500', 'blue.300');

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
    setServerError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    setServerError('');

    try {
      await login({ 
        email: formData.email, 
        password: formData.password 
      });
    } catch (err: any) {
      setServerError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <VStack spacing={6} align="stretch">
        {/* Server Error */}
        {serverError && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            {serverError}
          </Alert>
        )}

        {/* Email Field */}
        <FormControl isInvalid={!!errors.email}>
          <FormLabel>Email Address</FormLabel>
          <InputGroup>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="Enter your email"
              bg={inputBg}
              border="1px solid"
              borderColor={inputBorder}
              _hover={{ borderColor: inputFocusBorder }}
              _focus={{ 
                borderColor: inputFocusBorder,
                boxShadow: `0 0 0 1px ${inputFocusBorder}`,
                bg: useColorModeValue('white', 'gray.600')
              }}
              pl={12}
            />
            <InputRightElement pointerEvents="none" left={4}>
              <Mail size={18} color={useColorModeValue('#718096', '#a0aec0')} />
            </InputRightElement>
          </InputGroup>
          <FormErrorMessage>{errors.email}</FormErrorMessage>
        </FormControl>

        {/* Password Field */}
        <FormControl isInvalid={!!errors.password}>
          <FormLabel>Password</FormLabel>
          <InputGroup>
            <Input
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              placeholder="Enter your password"
              bg={inputBg}
              border="1px solid"
              borderColor={inputBorder}
              _hover={{ borderColor: inputFocusBorder }}
              _focus={{ 
                borderColor: inputFocusBorder,
                boxShadow: `0 0 0 1px ${inputFocusBorder}`,
                bg: useColorModeValue('white', 'gray.600')
              }}
              pl={12}
            />
            <InputRightElement 
              left={4} 
              pointerEvents="none"
            >
              <Lock size={18} color={useColorModeValue('#718096', '#a0aec0')} />
            </InputRightElement>
            <InputRightElement
              cursor="pointer"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? (
                <EyeOff size={18} color={useColorModeValue('#718096', '#a0aec0')} />
              ) : (
                <Eye size={18} color={useColorModeValue('#718096', '#a0aec0')} />
              )}
            </InputRightElement>
          </InputGroup>
          <FormErrorMessage>{errors.password}</FormErrorMessage>
        </FormControl>

        {/* Remember Me & Forgot Password */}
        <HStack justify="space-between">
          <Checkbox
            isChecked={formData.rememberMe}
            onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
            colorScheme="blue"
          >
            <Text fontSize="sm">Remember me</Text>
          </Checkbox>
          <Link 
            fontSize="sm" 
            color="blue.500" 
            _hover={{ color: 'blue.600' }}
          >
            Forgot password?
          </Link>
        </HStack>

        {/* Login Button */}
        <Button
          type="submit"
          colorScheme="blue"
          size="lg"
          isLoading={isLoading}
          loadingText="Signing in..."
          w="full"
          h={12}
          fontSize="md"
          fontWeight="semibold"
        >
          Sign In
        </Button>

        {/* Switch to Register */}
        <Text textAlign="center" color={useColorModeValue('gray.600', 'gray.400')}>
          Don't have an account?{' '}
          <Link
            color="blue.500"
            fontWeight="semibold"
            onClick={onSwitchToRegister}
            _hover={{ color: 'blue.600', textDecoration: 'underline' }}
          >
            Create one now
          </Link>
        </Text>
      </VStack>
    </form>
  );
};