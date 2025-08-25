import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import React, { ReactNode } from 'react';

import theme from '@/shared/theme';

interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * Enhanced theme provider with Chakra UI and theme persistence
 */
export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  return (
    <>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <ChakraProvider theme={theme}>
        {children}
      </ChakraProvider>
    </>
  );
};