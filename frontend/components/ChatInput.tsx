import React, { useState, useRef, useEffect } from 'react';
import Button from './Button';
import { SendIcon, CameraIcon, MicIcon, StopIcon } from './icons';
import { useVoiceInput } from '../hooks/useVoiceInput';

interface ChatInputProps {
  onSendMessage: (text: string, isVoiceInput?: boolean, forceTTSFormat?: boolean) => void;
  onCameraClick: () => void;
  disabled?: boolean;
  isTTSSpeaking?: boolean;
  onTTSStop?: () => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onCameraClick, disabled = false, isTTSSpeaking = false, onTTSStop }) => {
  const [text, setText] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Voice input functionality
  const voiceInput = useVoiceInput({
    onResult: (transcript) => {
      // Update input field with live transcript
      setText(transcript);
    },
    onFinalResult: (finalTranscript, isMicrophoneActive) => {
      // Auto-submit when user pauses speaking
      if (finalTranscript.trim()) {
        console.log('🎤 DEBUG: onFinalResult - about to send message, isMicrophoneActive:', isMicrophoneActive);
        // Pass the microphone state directly to bypass timing issues
        onSendMessage(finalTranscript.trim(), true, isMicrophoneActive); // Mark as voice input with mic state
        setText('');
        // Refocus input after voice submission
        setTimeout(() => {
          inputRef.current?.focus();
        }, 0);
      }
    },
    onError: (error) => {
      console.error('Voice input error:', error);
      // Could show error toast here if needed
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled || !text.trim()) return;
    // Manual text input - let App component decide format based on TTS toggle
    onSendMessage(text, false); // false = not voice input, format decided by TTS toggle
    setText('');

    // Refocus the input after sending message
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  };

  // Auto-focus on mount and when disabled state changes
  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  // For PTT, we don't need to track microphone state - always use TTS format for voice input
  // Remove the voice state change notification since PTT handles format directly

  return (
    <div className="p-4 bg-white border-t border-slate-200">
      <form onSubmit={handleSubmit} className="relative">
        <div className="absolute inset-y-0 left-0 flex items-center pl-2 space-x-1">
          {/* Microphone button - Push to Talk */}
          <Button
            type="button"
            variant="ghost"
            className={`p-1 ${voiceInput.isListening ? 'bg-red-100 text-red-600' : ''}`}
            aria-label={voiceInput.isListening ? "Release to stop recording" : "Hold to talk"}
            onMouseDown={voiceInput.startListening}
            onMouseUp={voiceInput.stopListening}
            onMouseLeave={voiceInput.stopListening} // Stop if mouse leaves button
            onTouchStart={voiceInput.startListening}
            onTouchEnd={voiceInput.stopListening}
            disabled={disabled || !voiceInput.isSupported}
            title={
              !voiceInput.isSupported ? "Voice input not supported in this browser" :
              "Hold to talk, release to send"
            }
          >
            <MicIcon className={`w-5 h-5 ${voiceInput.isListening ? 'text-red-600' : 'text-slate-500'}`} />
          </Button>

          {/* Stop button - only visible during TTS */}
          {isTTSSpeaking && (
            <Button
              type="button"
              variant="ghost"
              className="p-1 bg-blue-100 text-blue-600"
              aria-label="Stop speech playback"
              onClick={onTTSStop}
              title="Click to stop speech playback"
            >
              <StopIcon className="w-5 h-5 text-blue-600" />
            </Button>
          )}
        </div>
        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={
            disabled ? "Connecting..." :
            voiceInput.isListening ? "🎤 Listening... speak now" :
            "Type your message or ask about inventory..."
          }
          disabled={disabled}
          className="w-full py-2 pl-20 pr-24 bg-slate-100 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 focus:border-transparent transition disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <div className="absolute inset-y-0 right-0 flex items-center pr-2 space-x-1">
          <Button type="button" variant="ghost" className="p-2" aria-label="Use camera" onClick={onCameraClick} disabled={disabled}>
            <CameraIcon className="w-5 h-5 text-slate-500" />
          </Button>
          <Button type="submit" variant="ghost" className="p-2" aria-label="Send message" disabled={disabled || !text.trim()}>
            <SendIcon className="w-5 h-5 text-slate-500" />
          </Button>
        </div>
      </form>
    </div>
  );
};

export default ChatInput;