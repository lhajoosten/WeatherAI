import { extendTheme } from '@chakra-ui/react';

import { tokens } from './tokens';

// Minimal base theme configuration
const theme = extendTheme({
  config: {
    initialColorMode: 'light',
    useSystemColorMode: false,
  },
  colors: {
    primary: tokens.colors.primary,
    gray: tokens.colors.gray,
  },
  fonts: {
    heading: tokens.fonts.heading,
    body: tokens.fonts.body,
  },
  fontSizes: tokens.fontSizes,
  space: tokens.space,
  radii: tokens.radii,
  styles: {
    global: (props: { colorMode: string }) => ({
      body: {
        bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
        color: props.colorMode === 'dark' ? 'gray.100' : 'gray.900',
      },
    }),
  },
  components: {
    Button: {
      defaultProps: {
        colorScheme: 'primary',
      },
    },
  },
});

export default theme;