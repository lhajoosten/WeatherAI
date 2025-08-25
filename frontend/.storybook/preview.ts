import type { Preview } from '@storybook/react-vite';
import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import { withThemeByClassName } from '@storybook/addon-themes';
import React from 'react';

// Import our theme and i18n
import theme from '../src/shared/theme';
import { I18nProvider } from '../src/shared/i18n';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: 'light',
      values: [
        {
          name: 'light',
          value: '#ffffff',
        },
        {
          name: 'dark',
          value: '#1a202c',
        },
      ],
    },
    viewport: {
      viewports: {
        mobile: {
          name: 'Mobile',
          styles: {
            width: '375px',
            height: '667px',
          },
        },
        tablet: {
          name: 'Tablet',
          styles: {
            width: '768px',
            height: '1024px',
          },
        },
        desktop: {
          name: 'Desktop',
          styles: {
            width: '1200px',
            height: '800px',
          },
        },
      },
    },
  },
  decorators: [
    // Chakra UI provider
    (Story) => (
      <>
        <ColorModeScript initialColorMode={theme.config.initialColorMode} />
        <ChakraProvider theme={theme}>
          <I18nProvider>
            <Story />
          </I18nProvider>
        </ChakraProvider>
      </>
    ),
    // Theme switcher decorator
    withThemeByClassName({
      themes: {
        light: 'light',
        dark: 'dark',
      },
      defaultTheme: 'light',
    }),
  ],
};

export default preview;