import React, { useEffect, useRef, useState } from 'react';

import CameraModal from './components/CameraModal';
import ChatPanel from './components/ChatPanel';
import ErrorDisplay from './components/ErrorDisplay';
import ImageModal from './components/ImageModal';
import InventoryPanel from './components/InventoryPanel';
import { useChat, useInventory } from './hooks/useApi';
import { useTextToSpeech } from './hooks/useTextToSpeech';

const App: React.FC = () => {
  // Initialize inventory hook first
  const [currentBinState, setCurrentBinState] = useState<string>('');
  const { items: inventoryItems, isLoading: inventoryLoading, lastUpdated, reload: reloadInventory } = useInventory(currentBinState);

  // TTS toggle state
  const [isTTSEnabled, setIsTTSEnabled] = useState(false);
  const lastSpokenMessageRef = useRef<string>('');

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

  // Stop speaking when TTS is disabled
  useEffect(() => {
    if (!isTTSEnabled) {
      tts.stopSpeaking();
    }
  }, [isTTSEnabled]);

  // Auto-speak bot responses when TTS is enabled (only when new messages arrive)
  useEffect(() => {
    if (messages.length > 0 && isTTSEnabled) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.sender === 'bot' && lastMessage.text !== lastSpokenMessageRef.current) {
        console.log('🔊 Auto-speaking new bot response:', lastMessage.text.substring(0, 50) + '...');
        tts.speak(lastMessage.text);
        lastSpokenMessageRef.current = lastMessage.text;
      }
    }
  }, [messages]);

  // UI state
  const [activeTab, setActiveTab] = useState<'chat' | 'inventory'>('chat');
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const handleSendMessage = async (text: string, isVoiceInput: boolean = false, forceTTSFormat?: boolean) => {
    if (!text.trim()) return;

    // Use TTS format if explicitly requested or if TTS toggle is enabled
    const useTTSFormat = forceTTSFormat !== undefined ? forceTTSFormat : isTTSEnabled;
    console.log('🎤 DEBUG: handleSendMessage - isVoiceInput:', isVoiceInput, 'forceTTSFormat:', forceTTSFormat, 'isTTSEnabled:', isTTSEnabled, 'useTTSFormat:', useTTSFormat);

    // Send message with format based on TTS toggle
    await sendMessage(text, useTTSFormat);

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

      // Upload image and get analysis - use TTS toggle for format selection
      const response = await uploadImage(file, isTTSEnabled);

      if (response.success) {
        // Reload inventory to show any new items
        reloadInventory();

        // Don't auto-switch to inventory tab - let user stay on current tab
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
    <div className="flex flex-col h-[100dvh] bg-white text-slate-800 font-sans">
      {error && <ErrorDisplay message={error} onClose={() => setError(null)} />}

      {/* Mobile Tab Navigation - Always visible */}
      <div className="md:hidden flex border-b border-slate-200 bg-slate-50 flex-shrink-0">
        <TabButton label="Chat" isActive={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
        <TabButton label="Inventory" isActive={activeTab === 'inventory'} onClick={() => setActiveTab('inventory')} />
      </div>

      {/* Main content area - scrollable */}
      <main className="flex flex-1 md:flex-row overflow-hidden min-h-0">
        {/* Panels */}
        <div className={`flex-col h-full w-full ${activeTab === 'chat' ? 'flex' : 'hidden'} md:flex md:w-3/5 md:border-r md:border-slate-200`}>
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            onCameraClick={toggleCamera}
            isLoading={isLoading}
            isTTSSpeaking={tts.isSpeaking}
            onTTSStop={tts.stopSpeaking}
            isTTSEnabled={isTTSEnabled}
            onTTSToggle={() => setIsTTSEnabled(!isTTSEnabled)}
          />
        </div>

        <div className={`flex-col h-full w-full ${activeTab === 'inventory' ? 'flex' : 'hidden'} md:flex md:w-2/5`}>
          <InventoryPanel bin={currentBinInfo} items={inventoryItems} onImageSelect={handleImageSelect} />
        </div>
      </main>

      {isCameraOpen && <CameraModal onClose={toggleCamera} onImageCapture={handleImageCapture} />}
      {selectedImage && <ImageModal imageUrl={selectedImage} onClose={handleCloseImageModal} />}
    </div>
  );
};

export default App;