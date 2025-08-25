import { HStack, VStack, Text } from '@chakra-ui/react';
import type { Meta, StoryObj } from '@storybook/react';

import { ToggleThemeButton } from './ToggleThemeButton';

const meta: Meta<typeof ToggleThemeButton> = {
  title: 'Shared/UI/ToggleThemeButton',
  component: ToggleThemeButton,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
    variant: {
      control: 'select',
      options: ['ghost', 'outline', 'solid'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const Sizes: Story = {
  render: () => (
    <VStack spacing={4}>
      <Text fontWeight="bold">Different Sizes</Text>
      <HStack spacing={4}>
        <VStack>
          <Text fontSize="sm">Small</Text>
          <ToggleThemeButton size="sm" />
        </VStack>
        <VStack>
          <Text fontSize="sm">Medium</Text>
          <ToggleThemeButton size="md" />
        </VStack>
        <VStack>
          <Text fontSize="sm">Large</Text>
          <ToggleThemeButton size="lg" />
        </VStack>
      </HStack>
    </VStack>
  ),
};

export const Variants: Story = {
  render: () => (
    <VStack spacing={4}>
      <Text fontWeight="bold">Different Variants</Text>
      <HStack spacing={4}>
        <VStack>
          <Text fontSize="sm">Ghost</Text>
          <ToggleThemeButton variant="ghost" />
        </VStack>
        <VStack>
          <Text fontSize="sm">Outline</Text>
          <ToggleThemeButton variant="outline" />
        </VStack>
        <VStack>
          <Text fontSize="sm">Solid</Text>
          <ToggleThemeButton variant="solid" />
        </VStack>
      </HStack>
    </VStack>
  ),
};