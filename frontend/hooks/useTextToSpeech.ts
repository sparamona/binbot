/**
 * React hook for text-to-speech using OpenAI TTS API
 * Provides high-quality voice synthesis for bot responses
 */

import { useState, useRef, useCallback } from 'react';

interface TextToSpeechOptions {
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
  voice?: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer';
  model?: 'tts-1' | 'tts-1-hd';
}

interface TextToSpeechState {
  isSpeaking: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useTextToSpeech(options: TextToSpeechOptions = {}) {
  const {
    onStart,
    onEnd,
    onError,
    voice = 'alloy',
    model = 'tts-1'
  } = options;

  const [state, setState] = useState<TextToSpeechState>({
    isSpeaking: false,
    isLoading: false,
    error: null
  });

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Stop any current speech
  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }

    setState(prev => ({ ...prev, isSpeaking: false, isLoading: false }));
    
    if (onEnd) {
      onEnd();
    }
  }, [onEnd]);

  // Speak text using OpenAI TTS
  const speak = useCallback(async (text: string) => {
    if (!text.trim()) {
      return;
    }

    // Stop any current speech
    stopSpeaking();

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      // Create abort controller for this request
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      // Call our TTS API endpoint
      const response = await fetch('/api/tts/speak', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          voice,
          model
        }),
        signal: abortController.signal
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `TTS API error: ${response.status}`);
      }

      // Get audio blob
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create and configure audio element
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      // Set up event handlers
      audio.onloadstart = () => {
        setState(prev => ({ ...prev, isLoading: false, isSpeaking: true }));
        if (onStart) {
          onStart();
        }
      };

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        setState(prev => ({ ...prev, isSpeaking: false }));
        audioRef.current = null;
        if (onEnd) {
          onEnd();
        }
      };

      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        const errorMessage = 'Audio playback failed';
        setState(prev => ({ ...prev, isSpeaking: false, isLoading: false, error: errorMessage }));
        audioRef.current = null;
        if (onError) {
          onError(errorMessage);
        }
      };

      // Start playing
      await audio.play();

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        // Request was aborted, ignore
        return;
      }

      const errorMessage = error instanceof Error ? error.message : 'TTS generation failed';
      setState(prev => ({ ...prev, isLoading: false, isSpeaking: false, error: errorMessage }));
      
      if (onError) {
        onError(errorMessage);
      }
    }
  }, [voice, model, onStart, onEnd, onError, stopSpeaking]);

  // Cancel any ongoing speech or loading
  const cancel = useCallback(() => {
    stopSpeaking();
  }, [stopSpeaking]);

  return {
    ...state,
    speak,
    cancel,
    stopSpeaking
  };
}
