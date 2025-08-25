import React from 'react';
import { IconButton, useColorMode, Tooltip } from '@chakra-ui/react';
import { Moon, Sun } from 'react-feather';

import { useT } from '@/shared/i18n';

export interface ToggleThemeButtonProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'ghost' | 'outline' | 'solid';
}

/**
 * ToggleThemeButton component for switching between light and dark themes
 */
export const ToggleThemeButton: React.FC<ToggleThemeButtonProps> = ({ 
  size = 'md',
  variant = 'ghost'
}) => {
  const { colorMode, toggleColorMode } = useColorMode();
  const t = useT();

  const isDark = colorMode === 'dark';
  const icon = isDark ? <Sun size={20} /> : <Moon size={20} />;
  const label = isDark ? t('ui.lightMode') : t('ui.darkMode');

  return (
    <Tooltip label={label} placement="bottom">
      <IconButton
        aria-label={t('ui.toggleTheme')}
        icon={icon}
        onClick={toggleColorMode}
        size={size}
        variant={variant}
      />
    </Tooltip>
  );
};