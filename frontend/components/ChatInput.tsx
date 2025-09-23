import React, { useState, useRef, useEffect, useCallback } from 'react';
import Button from './Button';
import { SendIcon, CameraIcon, MicIcon } from './icons';
import { useContinuousSpeech } from '../hooks/useContinuousSpeech';

interface ChatInputProps {
  onSendMessage: (text: string, isVoiceInput?: boolean, forceTTSFormat?: boolean) => void;
  onCameraClick: () => void;
  disabled?: boolean;
  isTTSSpeaking?: boolean;
  onTTSStop?: () => void;
  isTTSEnabled?: boolean;
  onTTSToggle?: () => void;
  onListeningChange?: (isListening: boolean) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onCameraClick, disabled = false, isTTSSpeaking = false, onTTSStop, isTTSEnabled = false, onTTSToggle, onListeningChange }) => {
  const [text, setText] = useState('');
  const [isSpeechRecognitionEnabled, setIsSpeechRecognitionEnabled] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Speech recognition that populates the input field when enabled
  const handleTranscriptUpdate = useCallback((transcript: string) => {
    console.log('📝 ChatInput received transcript update:', transcript);
    setText(transcript);
  }, []);

  // Disable speech recognition while TTS is speaking to prevent interference
  const speechRecognitionActive = isSpeechRecognitionEnabled && !isTTSSpeaking;
  const { isListening } = useContinuousSpeech(handleTranscriptUpdate, speechRecognitionActive);

  // Notify parent component when listening state changes
  useEffect(() => {
    if (onListeningChange) {
      onListeningChange(isListening);
    }
  }, [isListening, onListeningChange]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled || !text.trim()) return;
    // Manual text input - let App component decide format based on TTS toggle
    onSendMessage(text, false); // false = not voice input, format decided by TTS toggle
    setText('');

    // Refocus the input after sending message (unless speech recognition is active)
    if (!isSpeechRecognitionEnabled) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  };

  // Auto-focus on mount and when disabled state changes (unless speech recognition is active)
  useEffect(() => {
    if (!disabled && !isSpeechRecognitionEnabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled, isSpeechRecognitionEnabled]);

  // For PTT, we don't need to track microphone state - always use TTS format for voice input
  // Remove the voice state change notification since PTT handles format directly

  return (
    <div className="p-4 bg-white border-t">
      <form onSubmit={handleSubmit}>
        {/* Desktop: single row, Mobile: two rows */}
        <div className="flex flex-col md:flex-row md:items-center space-y-2 md:space-y-0 md:space-x-2">

          {/* Button row - full width on mobile */}
          <div className="flex space-x-2 md:contents">
            {/* Mic button */}
            <Button
              type="button"
              variant={isSpeechRecognitionEnabled ? "primary" : "secondary"}
              onClick={() => setIsSpeechRecognitionEnabled(!isSpeechRecognitionEnabled)}
              className="flex-1 md:flex-none"
            >
              <MicIcon className="w-5 h-5" />
            </Button>

            {/* Speaker button */}
            <Button
              type="button"
              variant={isTTSEnabled ? "primary" : "secondary"}
              onClick={onTTSToggle}
              className="flex-1 md:flex-none"
            >
              <span className="w-5 h-5" >🔊</span>
            </Button>

            {/* Photo button */}
            <Button
              type="button"
              variant="secondary"
              onClick={onCameraClick}
              disabled={disabled}
              className="flex-1 md:flex-none"
            >
              <CameraIcon className="w-5 h-5" />
            </Button>
          </div>

          {/* Input row - full width on mobile */}
          <div className="flex space-x-2 flex-1">
            {/* Text input */}
            <input
              ref={inputRef}
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={
                disabled ? "Connecting..." :
                "Type or speak your message..."
              }
              disabled={disabled}
              className="flex-1 py-2 px-4 border rounded-lg focus:outline-none focus:ring-2 transition"
            />

            {/* Send button */}
            <Button type="submit" variant="secondary" disabled={disabled || !text.trim()}>
              <SendIcon className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;
