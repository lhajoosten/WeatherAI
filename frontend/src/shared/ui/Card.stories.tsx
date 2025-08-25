import { Text, VStack, HStack, Badge } from '@chakra-ui/react';
import type { Meta, StoryObj } from '@storybook/react';

import { Card } from './Card';

const meta: Meta<typeof Card> = {
  title: 'Shared/UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['elevated', 'outlined', 'filled'],
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

const SampleContent = () => (
  <VStack align="start" spacing={3}>
    <HStack>
      <Text fontWeight="bold">Weather Card</Text>
      <Badge colorScheme="blue">Live</Badge>
    </HStack>
    <Text color="gray.600">
      This is a sample card showing how the Card component can be used with different content.
    </Text>
    <HStack spacing={4}>
      <Text fontSize="sm" color="gray.500">Temperature: 22°C</Text>
      <Text fontSize="sm" color="gray.500">Humidity: 65%</Text>
    </HStack>
  </VStack>
);

export const Default: Story = {
  args: {
    children: <SampleContent />,
  },
};

export const Variants: Story = {
  render: () => (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', width: '100%', maxWidth: '900px' }}>
      <Card variant="elevated">
        <VStack align="start">
          <Text fontWeight="bold">Elevated Card</Text>
          <Text color="gray.600">This card has a shadow elevation effect.</Text>
        </VStack>
      </Card>
      <Card variant="outlined">
        <VStack align="start">
          <Text fontWeight="bold">Outlined Card</Text>
          <Text color="gray.600">This card has a border outline.</Text>
        </VStack>
      </Card>
      <Card variant="filled">
        <VStack align="start">
          <Text fontWeight="bold">Filled Card</Text>
          <Text color="gray.600">This card has a filled background.</Text>
        </VStack>
      </Card>
    </div>
  ),
};

export const Interactive: Story = {
  args: {
    cursor: 'pointer',
    _hover: { transform: 'translateY(-2px)', shadow: 'lg' },
    transition: 'all 0.2s',
    children: (
      <VStack align="start" spacing={3}>
        <Text fontWeight="bold">Interactive Card</Text>
        <Text color="gray.600">
          This card demonstrates hover effects and interactive behavior.
          Try hovering over it!
        </Text>
        <Badge colorScheme="green">Hover me</Badge>
      </VStack>
    ),
  },
};