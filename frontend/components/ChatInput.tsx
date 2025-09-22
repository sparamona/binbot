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
  isTTSEnabled?: boolean;
  onTTSToggle?: () => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, onCameraClick, disabled = false, isTTSSpeaking = false, onTTSStop, isTTSEnabled = false, onTTSToggle }) => {
  const [text, setText] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Voice input functionality
  const voiceInput = useVoiceInput({
    onResult: (transcript) => {
      // Update input field with live transcript
      setText(transcript);
    },
    onFinalResult: (finalTranscript) => {
      // Auto-submit when user pauses speaking
      if (finalTranscript.trim()) {
        console.log('🎤 DEBUG: onFinalResult - voice input, isTTSEnabled:', isTTSEnabled);
        // Voice input - let TTS toggle decide format (no forceTTSFormat parameter)
        onSendMessage(finalTranscript.trim(), true); // Mark as voice input, format decided by TTS toggle
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
    <>
      {/* Floating microphone button - mobile only */}
      <div className="md:hidden fixed bottom-20 right-4 z-50">
        <Button
          type="button"
          variant="ghost"
          className={`p-3 rounded-full shadow-lg ${voiceInput.isListening ? 'bg-red-500 text-white' : 'bg-white text-slate-600 border border-slate-200'}`}
          aria-label={voiceInput.isListening ? "Release to stop recording" : "Hold to talk"}
          onMouseDown={voiceInput.startListening}
          onMouseUp={voiceInput.stopListening}
          onMouseLeave={voiceInput.stopListening}
          onTouchStart={voiceInput.startListening}
          onTouchEnd={voiceInput.stopListening}
          disabled={disabled || !voiceInput.isSupported}
          title={
            !voiceInput.isSupported ? "Voice input not supported in this browser" :
            "Hold to talk, release to send"
          }
        >
          <MicIcon className="w-6 h-6" />
        </Button>
      </div>

      {/* Floating TTS stop button during speech - mobile only */}
      {isTTSSpeaking && (
        <div className="md:hidden fixed bottom-36 right-4 z-50">
          <Button
            type="button"
            variant="ghost"
            className="p-3 rounded-full shadow-lg bg-blue-500 text-white"
            aria-label="Stop speech playback"
            onClick={onTTSStop}
            title="Click to stop speech playback"
          >
            <StopIcon className="w-6 h-6" />
          </Button>
        </div>
      )}

      <div className="p-4 bg-white border-t border-slate-200">
        <form onSubmit={handleSubmit} className="relative">
          {/* Desktop microphone button - left side */}
          <div className="hidden md:flex absolute inset-y-0 left-0 items-center pl-2 space-x-1">
            <Button
              type="button"
              variant="ghost"
              className={`p-1 ${voiceInput.isListening ? 'bg-red-100 text-red-600' : ''}`}
              aria-label={voiceInput.isListening ? "Release to stop recording" : "Hold to talk"}
              onMouseDown={voiceInput.startListening}
              onMouseUp={voiceInput.stopListening}
              onMouseLeave={voiceInput.stopListening}
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

            {/* Desktop TTS stop button */}
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
            className={`w-full py-2 pr-32 bg-slate-100 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-slate-400 focus:border-transparent transition disabled:opacity-50 disabled:cursor-not-allowed ${
              // Adjust left padding based on screen size
              'pl-4 md:pl-20'
            }`}
          />

          <div className="absolute inset-y-0 right-0 flex items-center pr-2 space-x-1">
            {/* TTS Toggle - always visible */}
            {onTTSToggle && (
              <Button
                type="button"
                variant="ghost"
                className={`p-2 ${isTTSEnabled ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-600'}`}
                onClick={onTTSToggle}
                title={isTTSEnabled ? "Turn off voice responses" : "Turn on voice responses"}
                aria-label={isTTSEnabled ? "Turn off voice responses" : "Turn on voice responses"}
              >
                🔊
              </Button>
            )}

            <Button type="button" variant="ghost" className="p-2" aria-label="Use camera" onClick={onCameraClick} disabled={disabled}>
              <CameraIcon className="w-5 h-5 text-slate-500" />
            </Button>
            <Button type="submit" variant="ghost" className="p-2" aria-label="Send message" disabled={disabled || !text.trim()}>
              <SendIcon className="w-5 h-5 text-slate-500" />
            </Button>
          </div>
        </form>
      </div>
    </>
  );
};

export default ChatInput;