// Chat shell component for RAG interface

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  Text,
  Card,
  CardBody,
  Flex,
  IconButton,
  useColorModeValue,
  Spinner,
} from '@chakra-ui/react';
import { Send, User, MessageCircle } from 'react-feather';
import { useRagAsk } from '../hooks/useRagAsk';

export interface ChatMessage {
  id: string;
  type: 'user' | 'system' | 'answer-draft' | 'answer-final';
  content: string;
  timestamp: Date;
  sources?: ChatSource[];
}

export interface ChatSource {
  type: 'weather' | 'location' | 'general';
  title: string;
  excerpt: string;
  url?: string;
}

interface ChatShellProps {
  placeholder?: string;
  onMessage?: (message: ChatMessage) => void;
}

export function ChatShell({ placeholder = "Ask about weather...", onMessage }: ChatShellProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const { ask, isLoading, streamingAnswer, isStreaming, clearStreaming, isEnabled } = useRagAsk();
  
  const bgColor = useColorModeValue('gray.50', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingAnswer]);

  // Focus input after sending
  useEffect(() => {
    if (!isLoading && !isStreaming) {
      inputRef.current?.focus();
    }
  }, [isLoading, isStreaming]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading || isStreaming) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    onMessage?.(userMessage);
    
    const query = inputValue.trim();
    setInputValue('');
    clearStreaming();

    try {
      // Start streaming response
      await ask(query, { streaming: true });
      
      // Add final answer when streaming completes
      const finalMessage: ChatMessage = {
        id: `answer-${Date.now()}`,
        type: 'answer-final',
        content: streamingAnswer,
        timestamp: new Date(),
        sources: [
          {
            type: 'weather',
            title: 'Current Weather Data',
            excerpt: 'Real-time weather information from multiple sources',
          },
          {
            type: 'location',
            title: 'Location Database', 
            excerpt: 'Geographic and demographic information',
          },
        ],
      };
      
      setMessages(prev => [...prev, finalMessage]);
      onMessage?.(finalMessage);
      
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        type: 'system',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
      onMessage?.(errorMessage);
    }
  };

  if (!isEnabled) {
    return (
      <Card>
        <CardBody>
          <Text color="gray.500" textAlign="center">
            RAG feature is not enabled. Set VITE_FEATURE_RAG=1 to enable.
          </Text>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card h="600px" display="flex" flexDirection="column">
      <CardBody p={0} display="flex" flexDirection="column" h="full">
        {/* Messages area */}
        <Box
          flex={1}
          overflowY="auto"
          p={4}
          bg={bgColor}
          borderBottom="1px"
          borderColor={borderColor}
        >
          <VStack spacing={4} align="stretch">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            
            {/* Streaming indicator */}
            {isStreaming && streamingAnswer && (
              <MessageBubble
                message={{
                  id: 'streaming',
                  type: 'answer-draft',
                  content: streamingAnswer,
                  timestamp: new Date(),
                }}
                isStreaming={true}
              />
            )}
            
            <div ref={messagesEndRef} />
          </VStack>
        </Box>

        {/* Input area */}
        <Box p={4}>
          <form onSubmit={handleSubmit}>
            <HStack spacing={2}>
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={placeholder}
                disabled={isLoading || isStreaming}
                autoComplete="off"
                onCompositionStart={() => setIsComposing(true)}
                onCompositionEnd={() => setIsComposing(false)}
              />
              <IconButton
                type="submit"
                icon={isLoading || isStreaming ? <Spinner size="sm" /> : <Send size={16} />}
                aria-label="Send message"
                colorScheme="blue"
                disabled={!inputValue.trim() || isLoading || isStreaming || isComposing}
              />
            </HStack>
          </form>
        </Box>
      </CardBody>
    </Card>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.type === 'user';
  const userBg = useColorModeValue('blue.500', 'blue.600');
  const botBg = useColorModeValue('white', 'gray.700');
  const systemBg = useColorModeValue('orange.100', 'orange.900');

  const getBgColor = () => {
    if (message.type === 'system') return systemBg;
    return isUser ? userBg : botBg;
  };

  const getTextColor = () => {
    if (message.type === 'system') return 'orange.800';
    return isUser ? 'white' : undefined;
  };

  return (
    <Flex justify={isUser ? 'flex-end' : 'flex-start'}>
      <HStack
        spacing={2}
        maxW="80%"
        align="flex-start"
        flexDirection={isUser ? 'row-reverse' : 'row'}
      >
        {/* Avatar */}
        <Box
          w={8}
          h={8}
          borderRadius="full"
          bg={isUser ? userBg : 'gray.300'}
          display="flex"
          alignItems="center"
          justifyContent="center"
          flexShrink={0}
        >
          {isUser ? <User size={16} color="white" /> : <MessageCircle size={16} />}
        </Box>

        {/* Message content */}
        <VStack spacing={1} align={isUser ? 'flex-end' : 'flex-start'}>
          <Box
            bg={getBgColor()}
            color={getTextColor()}
            p={3}
            borderRadius="lg"
            position="relative"
          >
            <Text whiteSpace="pre-wrap">{message.content}</Text>
            
            {/* Streaming indicator */}
            {isStreaming && (
              <Box
                position="absolute"
                bottom={2}
                right={2}
                aria-live="polite"
                aria-label="Assistant is typing"
              >
                <Spinner size="xs" />
              </Box>
            )}
          </Box>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <VStack spacing={1} align="flex-start" w="full">
              <Text fontSize="xs" color="gray.500" fontWeight="medium">
                Sources:
              </Text>
              {message.sources.map((source, index) => (
                <Text key={index} fontSize="xs" color="gray.500">
                  • {source.title}
                </Text>
              ))}
            </VStack>
          )}

          <Text fontSize="xs" color="gray.400">
            {message.timestamp.toLocaleTimeString()}
          </Text>
        </VStack>
      </HStack>
    </Flex>
  );
}