/**
 * Modern RegisterComponent with improved UX and validation
 */

import React, { useState } from 'react';
import {
  VStack,
  HStack,
  FormControl,
  FormLabel,
  FormErrorMessage,
  FormHelperText,
  Input,
  InputGroup,
  InputRightElement,
  Button,
  Text,
  Link,
  Alert,
  AlertIcon,
  Progress,
  Select,
  useColorModeValue,
} from '@chakra-ui/react';
import { Eye, EyeOff, Mail, Lock, Clock } from 'react-feather';
import { useAuth } from '../contexts/AuthContext';

interface RegisterComponentProps {
  onSwitchToLogin: () => void;
}

interface PasswordStrength {
  score: number;
  label: string;
  color: string;
}

export const RegisterComponent: React.FC<RegisterComponentProps> = ({ onSwitchToLogin }) => {
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [serverError, setServerError] = useState('');

  const inputBg = useColorModeValue('gray.50', 'gray.700');
  const inputBorder = useColorModeValue('gray.200', 'gray.600');
  const inputFocusBorder = useColorModeValue('blue.500', 'blue.300');

  // Calculate password strength
  const getPasswordStrength = (password: string): PasswordStrength => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z\d]/.test(password)) score++;

    const strengthMap = {
      0: { label: 'Very Weak', color: 'red' },
      1: { label: 'Weak', color: 'orange' },
      2: { label: 'Fair', color: 'yellow' },
      3: { label: 'Good', color: 'blue' },
      4: { label: 'Strong', color: 'green' },
    };

    return { score, ...strengthMap[score as keyof typeof strengthMap] };
  };

  const passwordStrength = getPasswordStrength(formData.password);

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
    } else if (passwordStrength.score < 2) {
      newErrors.password = 'Password is too weak. Try adding numbers, symbols, or mixing cases.';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    // Timezone validation
    if (!formData.timezone) {
      newErrors.timezone = 'Please select a timezone';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: string, value: string) => {
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
      await register({ 
        email: formData.email, 
        password: formData.password,
        timezone: formData.timezone 
      });
    } catch (err: any) {
      setServerError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const commonTimezones = [
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Australia/Sydney',
    'UTC'
  ];

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
              placeholder="Create a strong password"
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
          
          {/* Password Strength Indicator */}
          {formData.password && (
            <VStack spacing={2} mt={2} align="stretch">
              <HStack justify="space-between">
                <Text fontSize="xs" color="gray.500">Password Strength:</Text>
                <Text fontSize="xs" color={`${passwordStrength.color}.500`} fontWeight="medium">
                  {passwordStrength.label}
                </Text>
              </HStack>
              <Progress 
                value={(passwordStrength.score / 4) * 100} 
                colorScheme={passwordStrength.color}
                size="sm"
                borderRadius="md"
              />
            </VStack>
          )}
          
          <FormErrorMessage>{errors.password}</FormErrorMessage>
          <FormHelperText>
            Use 8+ characters with a mix of letters, numbers & symbols
          </FormHelperText>
        </FormControl>

        {/* Confirm Password Field */}
        <FormControl isInvalid={!!errors.confirmPassword}>
          <FormLabel>Confirm Password</FormLabel>
          <InputGroup>
            <Input
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
              placeholder="Confirm your password"
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
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              {showConfirmPassword ? (
                <EyeOff size={18} color={useColorModeValue('#718096', '#a0aec0')} />
              ) : (
                <Eye size={18} color={useColorModeValue('#718096', '#a0aec0')} />
              )}
            </InputRightElement>
          </InputGroup>
          <FormErrorMessage>{errors.confirmPassword}</FormErrorMessage>
        </FormControl>

        {/* Timezone Field */}
        <FormControl isInvalid={!!errors.timezone}>
          <FormLabel>
            <HStack>
              <Clock size={16} />
              <Text>Timezone</Text>
            </HStack>
          </FormLabel>
          <Select
            value={formData.timezone}
            onChange={(e) => handleInputChange('timezone', e.target.value)}
            bg={inputBg}
            border="1px solid"
            borderColor={inputBorder}
            _hover={{ borderColor: inputFocusBorder }}
            _focus={{ 
              borderColor: inputFocusBorder,
              boxShadow: `0 0 0 1px ${inputFocusBorder}`,
            }}
          >
            {commonTimezones.map(tz => (
              <option key={tz} value={tz}>
                {tz.replace(/_/g, ' ')}
              </option>
            ))}
          </Select>
          <FormErrorMessage>{errors.timezone}</FormErrorMessage>
          <FormHelperText>
            Your timezone for personalized weather updates
          </FormHelperText>
        </FormControl>

        {/* Register Button */}
        <Button
          type="submit"
          colorScheme="blue"
          size="lg"
          isLoading={isLoading}
          loadingText="Creating account..."
          w="full"
          h={12}
          fontSize="md"
          fontWeight="semibold"
        >
          Create Account
        </Button>

        {/* Switch to Login */}
        <Text textAlign="center" color={useColorModeValue('gray.600', 'gray.400')}>
          Already have an account?{' '}
          <Link
            color="blue.500"
            fontWeight="semibold"
            onClick={onSwitchToLogin}
            _hover={{ color: 'blue.600', textDecoration: 'underline' }}
          >
            Sign in here
          </Link>
        </Text>
      </VStack>
    </form>
  );
};