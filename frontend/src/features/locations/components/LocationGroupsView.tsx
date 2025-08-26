import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Card,
  CardBody,
  Badge,
  useColorModeValue,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  useToast,
  SimpleGrid,
  IconButton,
  Tooltip,
  Wrap,
  WrapItem,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  Checkbox,
  CheckboxGroup,
  Stack
} from '@chakra-ui/react';
import { Folder, Plus, Trash2, Users, Edit } from 'react-feather';
import { LocationGroup, LocationGroupCreate, Location } from '@/shared/types/api';
import { useLocation } from '../context/LocationContext';
import { useBulkDiff } from '@/shared/hooks/useBulkDiff';
import { httpClient } from '@/shared/api';

const LocationGroupsView: React.FC = () => {
  const { locations } = useLocation();
  const [groups, setGroups] = useState<LocationGroup[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Create group modal
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure();
  const [newGroup, setNewGroup] = useState<LocationGroupCreate>({ name: '', description: '' });
  
  // Bulk edit modal
  const { isOpen: isBulkEditOpen, onOpen: onBulkEditOpen, onClose: onBulkEditClose } = useDisclosure();
  const [editingGroup, setEditingGroup] = useState<LocationGroup | null>(null);
  const [selectedLocationIds, setSelectedLocationIds] = useState<number[]>([]);
  
  // Delete confirmation
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  const [groupToDelete, setGroupToDelete] = useState<LocationGroup | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBgColor = useColorModeValue('white', 'gray.800');
  const toast = useToast();

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      setLoading(true);
      const response = await api.get<LocationGroup[]>('/v1/location-groups');
      setGroups(response.data);
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.data?.detail || 'Failed to fetch location groups',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroup.name.trim()) {
      toast({
        title: "Validation Error",
        description: "Group name is required",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      const response = await api.post<LocationGroup>('/v1/location-groups', newGroup);
      setGroups([...groups, response.data]);
      setNewGroup({ name: '', description: '' });
      onCreateClose();
      toast({
        title: "Group created",
        description: `"${response.data.name}" group created successfully`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (err: any) {
      toast({
        title: "Creation failed",
        description: err.data?.detail || 'Failed to create group',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDeleteGroup = async () => {
    if (!groupToDelete) return;

    try {
      await api.delete(`/v1/location-groups/${groupToDelete.id}`);
      setGroups(groups.filter(g => g.id !== groupToDelete.id));
      onDeleteClose();
      setGroupToDelete(null);
      toast({
        title: "Group deleted",
        description: `"${groupToDelete.name}" group deleted successfully`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (err: any) {
      toast({
        title: "Delete failed",
        description: err.data?.detail || 'Failed to delete group',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleAddLocationToGroup = async (groupId: number, locationId: number) => {
    try {
      await api.post(`/v1/location-groups/${groupId}/locations`, { location_id: locationId });
      // Refresh groups to show updated membership
      await fetchGroups();
      toast({
        title: "Location added",
        description: "Location added to group successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (err: any) {
      toast({
        title: "Add failed",
        description: err.data?.detail || 'Failed to add location to group',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleRemoveLocationFromGroup = async (groupId: number, locationId: number) => {
    try {
      await api.delete(`/v1/location-groups/${groupId}/locations/${locationId}`);
      // Update local state
      setGroups(groups.map(group => 
        group.id === groupId 
          ? { ...group, members: group.members.filter(loc => loc.id !== locationId) }
          : group
      ));
      toast({
        title: "Location removed",
        description: "Location removed from group successfully",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (err: any) {
      toast({
        title: "Remove failed",
        description: err.data?.detail || 'Failed to remove location from group',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const confirmDeleteGroup = (group: LocationGroup) => {
    setGroupToDelete(group);
    onDeleteOpen();
  };

  const openBulkEditModal = (group: LocationGroup) => {
    setEditingGroup(group);
    setSelectedLocationIds(group.member_location_ids || []);
    onBulkEditOpen();
  };

  const handleBulkSave = async () => {
    if (!editingGroup) return;

    const originalIds = editingGroup.member_location_ids || [];
    const { add, remove } = useBulkDiff(originalIds, selectedLocationIds);

    try {
      await api.post(`/v1/location-groups/${editingGroup.id}/members/bulk`, {
        add,
        remove
      });

      // Refresh groups to show updated membership
      await fetchGroups();
      onBulkEditClose();
      setEditingGroup(null);

      toast({
        title: "Members updated",
        description: `Group "${editingGroup.name}" membership updated successfully`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (err: any) {
      toast({
        title: "Update failed",
        description: err.data?.detail || 'Failed to update group membership',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const getAvailableLocationsForGroup = (group: LocationGroup): Location[] => {
    const memberIds = new Set(group.members.map(m => m.id));
    return locations.filter(loc => !memberIds.has(loc.id));
  };

  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        {/* Header */}
        <HStack justify="space-between" align="center">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Location Groups</Heading>
            <Text color="gray.500">Organize your locations into custom groups</Text>
          </VStack>
          
          <Button
            leftIcon={<Plus size={16} />}
            onClick={onCreateOpen}
            colorScheme="blue"
            isLoading={loading}
          >
            Create Group
          </Button>
        </HStack>

        {/* Groups Grid */}
        {groups.length === 0 ? (
          <Card>
            <CardBody textAlign="center" py={12}>
              <Folder size={48} style={{ margin: '0 auto 16px' }} color="gray" />
              <Text fontSize="lg" color="gray.500" mb={2}>
                No groups created yet
              </Text>
              <Text color="gray.400">
                Create your first group to organize your weather locations!
              </Text>
            </CardBody>
          </Card>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
            {groups.map((group) => (
              <Card key={group.id} bg={cardBgColor} _hover={{ shadow: "md" }} transition="all 0.2s">
                <CardBody>
                  <VStack align="stretch" spacing={4}>
                    {/* Group Header */}
                    <HStack justify="space-between" align="start">
                      <VStack align="start" spacing={1}>
                        <HStack>
                          <Folder size={20} color="blue" />
                          <Heading size="md">{group.name}</Heading>
                        </HStack>
                        {group.description && (
                          <Text fontSize="sm" color="gray.500" noOfLines={2}>
                            {group.description}
                          </Text>
                        )}
                      </VStack>
                      
                      <HStack>
                        <Tooltip label="Edit members">
                          <IconButton
                            icon={<Edit size={14} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="blue"
                            onClick={() => openBulkEditModal(group)}
                            aria-label="Edit members"
                          />
                        </Tooltip>
                        <Tooltip label="Delete group">
                          <IconButton
                            icon={<Trash2 size={14} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => confirmDeleteGroup(group)}
                            aria-label="Delete group"
                          />
                        </Tooltip>
                      </HStack>
                    </HStack>

                    {/* Group Stats */}
                    <HStack spacing={4}>
                      <HStack spacing={1}>
                        <Users size={16} />
                        <Text fontSize="sm" color="gray.500">
                          {group.members.length} locations
                        </Text>
                      </HStack>
                      <Badge colorScheme="blue" variant="subtle">
                        {new Date(group.created_at).toLocaleDateString()}
                      </Badge>
                    </HStack>

                    {/* Group Members */}
                    {group.members.length > 0 && (
                      <VStack align="stretch" spacing={2}>
                        <Text fontSize="sm" fontWeight="semibold" color="gray.600">
                          Locations:
                        </Text>
                        <Wrap spacing={1}>
                          {group.members.map((location) => (
                            <WrapItem key={location.id}>
                              <Badge
                                colorScheme="green"
                                variant="outline"
                                cursor="pointer"
                                onClick={() => handleRemoveLocationFromGroup(group.id, location.id)}
                                _hover={{ bg: "red.50", borderColor: "red.300" }}
                                title="Click to remove from group"
                              >
                                {location.name} ×
                              </Badge>
                            </WrapItem>
                          ))}
                        </Wrap>
                      </VStack>
                    )}

                    {/* Add Locations */}
                    {getAvailableLocationsForGroup(group).length > 0 && (
                      <VStack align="stretch" spacing={2}>
                        <Text fontSize="sm" fontWeight="semibold" color="gray.600">
                          Add locations:
                        </Text>
                        <Wrap spacing={1}>
                          {getAvailableLocationsForGroup(group).map((location) => (
                            <WrapItem key={location.id}>
                              <Badge
                                colorScheme="gray"
                                variant="outline"
                                cursor="pointer"
                                onClick={() => handleAddLocationToGroup(group.id, location.id)}
                                _hover={{ bg: "blue.50", borderColor: "blue.300" }}
                                title="Click to add to group"
                              >
                                + {location.name}
                              </Badge>
                            </WrapItem>
                          ))}
                        </Wrap>
                      </VStack>
                    )}
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        )}

        {/* Create Group Modal */}
        <Modal isOpen={isCreateOpen} onClose={onCreateClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Create New Group</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4}>
                <FormControl isRequired>
                  <FormLabel>Group Name</FormLabel>
                  <Input
                    value={newGroup.name}
                    onChange={(e) => setNewGroup({ ...newGroup, name: e.target.value })}
                    placeholder="e.g., East Coast, Office Locations, Vacation Spots"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Description (Optional)</FormLabel>
                  <Textarea
                    value={newGroup.description}
                    onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })}
                    placeholder="Brief description of this group..."
                    size="sm"
                    resize="vertical"
                  />
                </FormControl>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onCreateClose}>
                Cancel
              </Button>
              <Button colorScheme="blue" onClick={handleCreateGroup}>
                Create Group
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Bulk Edit Members Modal */}
        <Modal isOpen={isBulkEditOpen} onClose={onBulkEditClose} size="lg">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Edit Members - {editingGroup?.name}</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4} align="stretch">
                <Text fontSize="sm" color="gray.600">
                  Select locations to include in this group:
                </Text>
                <Box maxHeight="400px" overflowY="auto" border="1px" borderColor="gray.200" borderRadius="md" p={4}>
                  <CheckboxGroup 
                    value={selectedLocationIds.map(String)} 
                    onChange={(values) => setSelectedLocationIds(values.map(Number))}
                  >
                    <Stack spacing={2}>
                      {locations.map((location) => (
                        <Checkbox key={location.id} value={String(location.id)}>
                          <HStack spacing={2}>
                            <Text>{location.name}</Text>
                            <Text fontSize="xs" color="gray.500">
                              {location.lat.toFixed(2)}°, {location.lon.toFixed(2)}°
                            </Text>
                          </HStack>
                        </Checkbox>
                      ))}
                    </Stack>
                  </CheckboxGroup>
                </Box>
                <Text fontSize="xs" color="gray.500">
                  {selectedLocationIds.length} of {locations.length} locations selected
                </Text>
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onBulkEditClose}>
                Cancel
              </Button>
              <Button colorScheme="blue" onClick={handleBulkSave}>
                Save Changes
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Delete Confirmation Dialog */}
        <AlertDialog
          isOpen={isDeleteOpen}
          leastDestructiveRef={cancelRef}
          onClose={onDeleteClose}
        >
          <AlertDialogOverlay>
            <AlertDialogContent>
              <AlertDialogHeader fontSize="lg" fontWeight="bold">
                Delete Group
              </AlertDialogHeader>

              <AlertDialogBody>
                Are you sure you want to delete "{groupToDelete?.name}"? This action cannot be undone.
                The locations in this group will not be deleted, only the group itself.
              </AlertDialogBody>

              <AlertDialogFooter>
                <Button ref={cancelRef} onClick={onDeleteClose}>
                  Cancel
                </Button>
                <Button colorScheme="red" onClick={handleDeleteGroup} ml={3}>
                  Delete
                </Button>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialogOverlay>
        </AlertDialog>
      </VStack>
    </Box>
  );
};

export default LocationGroupsView;