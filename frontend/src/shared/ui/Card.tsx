import { Box, useColorModeValue } from '@chakra-ui/react';
import React from 'react';

export interface CardProps extends Omit<React.ComponentProps<typeof Box>, 'variant'> {
  variant?: 'elevated' | 'outlined' | 'filled';
}

/**
 * Card component with elevation and theme-aware styling
 */
export const Card: React.FC<CardProps> = ({ 
  children, 
  variant = 'elevated',
  ...props 
}) => {
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const filledBg = useColorModeValue('gray.50', 'gray.700');
  
  let cardStyles;
  switch (variant) {
    case 'elevated':
      cardStyles = {
        bg,
        boxShadow: 'md',
        border: 'none',
      };
      break;
    case 'outlined':
      cardStyles = {
        bg,
        boxShadow: 'none',
        border: '1px solid',
        borderColor,
      };
      break;
    case 'filled':
      cardStyles = {
        bg: filledBg,
        boxShadow: 'none',
        border: 'none',
      };
      break;
    default:
      cardStyles = {
        bg,
        boxShadow: 'md',
        border: 'none',
      };
  }

  return (
    <Box
      borderRadius="md"
      p={4}
      {...cardStyles}
      {...props}
    >
      {children}
    </Box>
  );
};