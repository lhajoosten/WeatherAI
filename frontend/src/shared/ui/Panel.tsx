import React from 'react';
import { VStack, StackProps } from '@chakra-ui/react';

export interface PanelProps extends StackProps {
  // Additional panel-specific props can be added here in the future
}

/**
 * Panel component for grouping content with consistent spacing
 */
export const Panel: React.FC<PanelProps> = ({ 
  children, 
  spacing = 4,
  ...props 
}) => {
  return (
    <VStack
      spacing={spacing}
      align="stretch"
      {...props}
    >
      {children}
    </VStack>
  );
};