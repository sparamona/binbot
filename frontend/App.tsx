import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import InventoryPanel from './components/InventoryPanel';
import CameraModal from './components/CameraModal';
import ImageModal from './components/ImageModal';
import ErrorDisplay from './components/ErrorDisplay';
import { useChat, useInventory } from './hooks/useApi';
import { useTextToSpeech } from './hooks/useTextToSpeech';
import type { Message, InventoryItem } from './types';

const App: React.FC = () => {
  // Initialize inventory hook first
  const [currentBinState, setCurrentBinState] = useState<string>('');
  const { items: inventoryItems, isLoading: inventoryLoading, lastUpdated, reload: reloadInventory } = useInventory(currentBinState);

  // Voice input tracking state
  const [isVoiceInputActive, setIsVoiceInputActive] = useState(false);
  const [wasLastMessageVoice, setWasLastMessageVoice] = useState(false);
  const lastBotMessageRef = useRef<string>('');
  const micActivationTimeRef = useRef<number>(0);

  // Text-to-speech functionality
  const tts = useTextToSpeech({
    onStart: () => console.log('TTS started'),
    onEnd: () => console.log('TTS ended'),
    onError: (error) => console.error('TTS error:', error)
  });

  // Use real API hooks with inventory update callback
  const { messages, isLoading, currentBin, sendMessage, uploadImage } = useChat(() => {
    // Trigger inventory reload when chat updates
    reloadInventory();
  });

  // Update local bin state when chat hook updates currentBin
  useEffect(() => {
    if (currentBin !== currentBinState) {
      setCurrentBinState(currentBin);
    }
  }, [currentBin, currentBinState]);

  // Track when microphone is activated to avoid reading old messages
  useEffect(() => {
    if (isVoiceInputActive) {
      micActivationTimeRef.current = Date.now();
    }
  }, [isVoiceInputActive]);

  // Auto-speak bot responses only for NEW messages after microphone activation
  useEffect(() => {
    if (messages.length > 0 && isVoiceInputActive) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.sender === 'bot' &&
          lastMessage.text !== lastBotMessageRef.current) {

        // Only speak if this message arrived after microphone was activated
        // Use message ID as a proxy for message timestamp (higher ID = newer message)
        const messageTime = lastMessage.id;
        if (messageTime > micActivationTimeRef.current) {
          // Speak the bot response
          tts.speak(lastMessage.text);
          lastBotMessageRef.current = lastMessage.text;
        }
      }
    }
  }, [messages, isVoiceInputActive, tts]);

  // UI state
  const [activeTab, setActiveTab] = useState<'chat' | 'inventory'>('chat');
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const handleSendMessage = async (text: string, isVoiceInput: boolean = false, forceMicrophoneActive?: boolean) => {
    if (!text.trim()) return;

    // Track if this message was from voice input
    setWasLastMessageVoice(isVoiceInput);

    // Use forceMicrophoneActive if provided, otherwise fall back to isVoiceInputActive
    const microphoneActive = forceMicrophoneActive !== undefined ? forceMicrophoneActive : isVoiceInputActive;
    console.log('🎤 DEBUG: handleSendMessage - isVoiceInput:', isVoiceInput, 'forceMicrophoneActive:', forceMicrophoneActive, 'microphoneActive:', microphoneActive);
    // Use real API to send message with format based on microphone state
    await sendMessage(text, microphoneActive);

    // Reload inventory after any chat response
    reloadInventory();

    // // Switch to inventory tab if user asks to see a bin
    // if (text.toLowerCase().includes('bin')) {
    //   setActiveTab('inventory');
    // }
  };

  const toggleCamera = () => {
    setIsCameraOpen(!isCameraOpen);
  };

  const handleImageCapture = async (file: File) => {
    try {
      setError(null);

      // Upload image and get analysis - use microphone state for format selection
      const response = await uploadImage(file, isVoiceInputActive);

      if (response.success) {
        // Reload inventory to show any new items
        reloadInventory();

        // Switch to inventory tab to show results
        setActiveTab('inventory');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload image');
    }
  };

  const handleImageSelect = (url: string) => {
    setSelectedImage(url);
  };

  const handleCloseImageModal = () => {
    setSelectedImage(null);
  };

  const currentBinInfo = {
    name: currentBin ? `BIN ${currentBin.toUpperCase()}` : 'No bin selected',
    lastUpdated: lastUpdated || 'Never'
  };
  
  const TabButton: React.FC<{
    label: string;
    isActive: boolean;
    onClick: () => void;
  }> = ({ label, isActive, onClick }) => (
    <button
      onClick={onClick}
      className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${
        isActive
          ? 'bg-white border-b-2 border-slate-900 text-slate-900'
          : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="flex h-screen bg-white text-slate-800 font-sans">
      <Sidebar />
      <main className="flex flex-1 flex-col md:flex-row overflow-hidden relative">
        {error && <ErrorDisplay message={error} onClose={() => setError(null)} />}
        
        {/* Mobile Tab Navigation */}
        <div className="md:hidden flex border-b border-slate-200 bg-slate-50">
          <TabButton label="Chat" isActive={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
          <TabButton label="Inventory" isActive={activeTab === 'inventory'} onClick={() => setActiveTab('inventory')} />
        </div>
        
        {/* Panels */}
        <div className={`flex-col h-full ${activeTab === 'chat' ? 'flex' : 'hidden'} md:flex md:w-3/5 md:border-r md:border-slate-200`}>
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            onCameraClick={toggleCamera}
            isLoading={isLoading}
            onVoiceStateChange={setIsVoiceInputActive}
            isTTSSpeaking={tts.isSpeaking}
            onTTSStop={tts.stopSpeaking}
          />
        </div>

        <div className={`flex-col h-full ${activeTab === 'inventory' ? 'flex' : 'hidden'} md:flex md:w-2/5`}>
          <InventoryPanel bin={currentBinInfo} items={inventoryItems} onImageSelect={handleImageSelect} />
        </div>

      </main>
      {isCameraOpen && <CameraModal onClose={toggleCamera} onImageCapture={handleImageCapture} />}
      {selectedImage && <ImageModal imageUrl={selectedImage} onClose={handleCloseImageModal} />}
    </div>
  );
};

export default App;