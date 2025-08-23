import React, { ReactNode } from 'react';
import {
  Box,
  Flex,
  HStack,
  VStack,
  Heading,
  Text,
  Button,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  useColorMode,
  useColorModeValue,
  Select,
  Divider
} from '@chakra-ui/react';
import { Link, useLocation as useRouterLocation } from 'react-router-dom';
import { Sun, Moon, MapPin, BarChart3, User, LogOut } from 'react-feather';
import { useAuth } from '../contexts/AuthContext';
import { useLocation } from '../context/LocationContext';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const { selectedLocation, setSelectedLocation, locations } = useLocation();
  const { colorMode, toggleColorMode } = useColorMode();
  const routerLocation = useRouterLocation();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const activeBg = useColorModeValue('blue.50', 'blue.900');
  const activeColor = useColorModeValue('blue.600', 'blue.200');
  
  const isActive = (path: string) => routerLocation.pathname === path;

  const NavLink: React.FC<{ to: string; icon: any; children: ReactNode }> = ({ to, icon: Icon, children }) => (
    <Button
      as={Link}
      to={to}
      leftIcon={<Icon size={18} />}
      variant={isActive(to) ? "solid" : "ghost"}
      colorScheme={isActive(to) ? "blue" : "gray"}
      justifyContent="flex-start"
      width="full"
      size="md"
    >
      {children}
    </Button>
  );

  return (
    <Flex h="100vh">
      {/* Sidebar */}
      <Box
        w="280px"
        bg={bgColor}
        borderRight="1px solid"
        borderColor={borderColor}
        p={6}
        overflowY="auto"
      >
        <VStack spacing={6} align="stretch">
          {/* Logo */}
          <VStack spacing={2} align="start">
            <Heading size="lg" color="blue.500">WeatherAI</Heading>
            <Text fontSize="sm" color="gray.500">Analytics Platform</Text>
          </VStack>

          <Divider />

          {/* Location selector */}
          <Box>
            <Text fontSize="sm" fontWeight="semibold" mb={2} color="gray.500">
              Current Location
            </Text>
            <Select
              placeholder="Select location"
              value={selectedLocation?.id || ''}
              onChange={(e) => {
                const locationId = parseInt(e.target.value);
                const location = locations.find(l => l.id === locationId);
                setSelectedLocation(location || null);
              }}
              size="sm"
            >
              {locations.map(location => (
                <option key={location.id} value={location.id}>
                  {location.name}
                </option>
              ))}
            </Select>
          </Box>

          <Divider />

          {/* Navigation */}
          <VStack spacing={2} align="stretch">
            <Text fontSize="sm" fontWeight="semibold" color="gray.500" mb={2}>
              Navigation
            </Text>
            
            <NavLink to="/locations" icon={MapPin}>
              Locations
            </NavLink>
            
            <NavLink to="/analytics" icon={BarChart3}>
              Analytics
            </NavLink>
          </VStack>

          {/* Spacer */}
          <Box flex={1} />

          <Divider />

          {/* User menu and settings */}
          <VStack spacing={3} align="stretch">
            {/* Theme toggle */}
            <Button
              onClick={toggleColorMode}
              leftIcon={colorMode === 'light' ? <Moon size={18} /> : <Sun size={18} />}
              variant="ghost"
              size="sm"
              justifyContent="flex-start"
            >
              {colorMode === 'light' ? 'Dark Mode' : 'Light Mode'}
            </Button>

            {/* User menu */}
            <Menu>
              <MenuButton
                as={Button}
                leftIcon={<User size={18} />}
                variant="ghost"
                size="sm"
                justifyContent="flex-start"
                textAlign="left"
              >
                <Box>
                  <Text fontSize="sm" fontWeight="medium">{user?.email}</Text>
                  <Text fontSize="xs" color="gray.500">Account</Text>
                </Box>
              </MenuButton>
              <MenuList>
                <MenuItem icon={<LogOut size={16} />} onClick={logout}>
                  Logout
                </MenuItem>
              </MenuList>
            </Menu>
          </VStack>
        </VStack>
      </Box>

      {/* Main content */}
      <Box flex={1} overflowY="auto">
        {children}
      </Box>
    </Flex>
  );
};

export default Layout;