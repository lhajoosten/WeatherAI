import React from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  useColorModeValue,
  Badge,
  Icon,
} from '@chakra-ui/react';
import { MessageCircle, Upload, Info } from 'react-feather';
import RagQueryInterface from '../components/RagQueryInterface';
import RagIngestInterface from '../components/RagIngestInterface';

const RagPage: React.FC = () => {
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBgColor = useColorModeValue('white', 'gray.800');
  
  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        {/* Header */}
        <Box textAlign="center">
          <Heading size="xl" mb={2} color="blue.500">
            RAG Knowledge Base
          </Heading>
          <Text color="gray.500" fontSize="lg">
            Intelligent document search and AI-powered Q&A system
          </Text>
        </Box>

        {/* Info Banner */}
        <Box
          bg={useColorModeValue('blue.50', 'blue.900')}
          borderRadius="lg"
          p={4}
          border="1px solid"
          borderColor={useColorModeValue('blue.200', 'blue.700')}
        >
          <HStack spacing={3}>
            <Icon as={Info} color="blue.500" />
            <VStack align="start" spacing={1}>
              <Text fontSize="sm" fontWeight="semibold" color="blue.600">
                Retrieval-Augmented Generation (RAG)
              </Text>
              <Text fontSize="sm" color="gray.600">
                Query documents using natural language and get AI-powered answers backed by your knowledge base.
                Ingest weather reports, research papers, or any text documents to make them searchable.
              </Text>
            </VStack>
          </HStack>
        </Box>

        {/* Main Interface */}
        <Box
          bg={cardBgColor}
          borderRadius="lg"
          shadow="sm"
          overflow="hidden"
        >
          <Tabs isFitted variant="enclosed" colorScheme="blue">
            <TabList>
              <Tab>
                <HStack spacing={2}>
                  <Icon as={MessageCircle} size={16} />
                  <Text>Ask Questions</Text>
                  <Badge colorScheme="blue" variant="subtle" size="sm">
                    Query
                  </Badge>
                </HStack>
              </Tab>
              <Tab>
                <HStack spacing={2}>
                  <Icon as={Upload} size={16} />
                  <Text>Add Documents</Text>
                  <Badge colorScheme="green" variant="subtle" size="sm">
                    Ingest
                  </Badge>
                </HStack>
              </Tab>
            </TabList>

            <TabPanels>
              <TabPanel p={6}>
                <RagQueryInterface />
              </TabPanel>

              <TabPanel p={6}>
                <RagIngestInterface />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </Box>

        {/* Footer Info */}
        <Box
          bg={useColorModeValue('gray.100', 'gray.800')}
          borderRadius="lg"
          p={4}
        >
          <VStack spacing={2} align="start">
            <Text fontSize="sm" fontWeight="semibold" color="gray.600">
              How it works
            </Text>
            <HStack spacing={6} fontSize="sm" color="gray.500" wrap="wrap">
              <Text>1. Ingest documents into the knowledge base</Text>
              <Text>2. Documents are processed and embedded</Text>
              <Text>3. Ask questions in natural language</Text>
              <Text>4. Get AI answers with source citations</Text>
            </HStack>
          </VStack>
        </Box>
      </VStack>
    </Box>
  );
};

export default RagPage;