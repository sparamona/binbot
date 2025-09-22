/**
 * React hooks for API state management
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, type ChatResponse, type ImageUploadResponse } from '../services/api';
import type { InventoryItem } from '../types';

/**
 * Hook for managing chat functionality
 */
export function useChat(onInventoryUpdate?: () => void) {
  const [messages, setMessages] = useState<Array<{
    id: number;
    text: string;
    sender: 'bot' | 'user';
    timestamp: string;
  }>>([
    {
      id: 1,
      text: 'Welcome to **BinBot**! 🤖\n\nI can help you manage your inventory:\n- Add items to bins\n- Search for items\n- Check bin contents\n- Upload images for analysis\n\nTry saying: `"add hammer to bin A"` or `"what\'s in bin B"`',
      sender: 'bot',
      timestamp: new Date().toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit'
      })
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentBin, setCurrentBin] = useState<string>('');

  const sendMessage = useCallback(async (text: string, isMicrophoneActive: boolean = false) => {
    if (!text.trim() || isLoading) return;

    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      text,
      sender: 'user' as const,
      timestamp: new Date().toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit'
      })
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Use TTS format if microphone is active, otherwise use MD format
      const format = isMicrophoneActive ? 'TTS' : 'MD';
      const response = await apiClient.sendChatMessage(text, format);
      
      // Add bot response
      const botMessage = {
        id: Date.now() + 1,
        text: response.response,
        sender: 'bot' as const,
        timestamp: new Date().toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit' 
        })
      };
      setMessages(prev => [...prev, botMessage]);

      // Update current bin if provided
      if (response.current_bin !== undefined) {
        setCurrentBin(response.current_bin);
      }

      // Trigger inventory update after any chat response
      if (onInventoryUpdate) {
        onInventoryUpdate();
      }

    } catch (error) {
      console.error('Chat error:', error);
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot' as const,
        timestamp: new Date().toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit' 
        })
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  const uploadImage = useCallback(async (file: File, isMicrophoneActive: boolean = false) => {
    if (isLoading) return;

    setIsLoading(true);

    try {
      // Use TTS format if microphone is active, otherwise use MD format
      const format = isMicrophoneActive ? 'TTS' : 'MD';
      const response = await apiClient.uploadImage(file, format);
      
      // Add image upload message
      const imageMessage = {
        id: Date.now(),
        text: `📷 Uploaded: ${file.name}`,
        sender: 'user' as const,
        timestamp: new Date().toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit' 
        })
      };
      setMessages(prev => [...prev, imageMessage]);

      // Use the conversational response from the API
      const botResponseText = response.response || 'Image analysis completed.';

      const botMessage = {
        id: Date.now() + 1,
        text: botResponseText,
        sender: 'bot' as const,
        timestamp: new Date().toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit'
        })
      };
      setMessages(prev => [...prev, botMessage]);

      // Update current bin if provided
      if (response.current_bin !== undefined) {
        setCurrentBin(response.current_bin);
      }

      // Trigger inventory update after any image upload response
      if (onInventoryUpdate) {
        onInventoryUpdate();
      }

      return response;

    } catch (error) {
      console.error('Image upload error:', error);
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, image upload failed. Please try again.',
        sender: 'bot' as const,
        timestamp: new Date().toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit' 
        })
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  return {
    messages,
    isLoading,
    currentBin,
    sendMessage,
    uploadImage
  };
}

/**
 * Hook for managing inventory/bin contents
 */
export function useInventory(binId: string) {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const loadBinContents = useCallback(async () => {
    if (!binId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.getBinContents(binId);

      // Transform API items to React component format
      const transformedItems = response.items.map(item => ({
        id: item.id,
        name: item.name,
        description: item.description,
        createdAt: item.created_at, // Map created_at to createdAt
        thumbnailUrl: item.image_id ? `/api/images/${item.image_id}` : undefined // Map image_id to thumbnailUrl
      }));

      setItems(transformedItems);
      setLastUpdated(new Date().toLocaleString());
    } catch (error) {
      console.error('Failed to load bin contents:', error);
      setError(error instanceof Error ? error.message : 'Failed to load bin contents');
    } finally {
      setIsLoading(false);
    }
  }, [binId]);

  // Load contents when binId changes
  useEffect(() => {
    loadBinContents();
  }, [loadBinContents]);

  return {
    items,
    isLoading,
    error,
    lastUpdated,
    reload: loadBinContents
  };
}

/**
 * Hook for managing API connection status
 */
export function useApiStatus() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const checkConnection = useCallback(async () => {
    try {
      const isHealthy = await apiClient.healthCheck();
      setIsConnected(isHealthy);
      
      if (isHealthy) {
        const currentSessionId = apiClient.getCurrentSessionId();
        setSessionId(currentSessionId);
      }
    } catch {
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    checkConnection();
    
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, [checkConnection]);

  return {
    isConnected,
    sessionId,
    checkConnection
  };
}
