import { Button as ChakraButton, ButtonProps as ChakraButtonProps } from '@chakra-ui/react';
import React from 'react';

export interface ButtonProps extends ChakraButtonProps {
  variant?: 'solid' | 'outline' | 'ghost' | 'link';
  size?: 'xs' | 'sm' | 'md' | 'lg';
}

/**
 * Enhanced Button component with consistent styling and behavior
 */
export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'solid',
  size = 'md',
  ...props 
}) => {
  return (
    <ChakraButton
      variant={variant}
      size={size}
      {...props}
    >
      {children}
    </ChakraButton>
  );
};