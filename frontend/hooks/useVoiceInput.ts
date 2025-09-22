/**
 * React hook for voice input using browser SpeechRecognition API
 * Provides continuous listening with automatic submission after pauses
 */

import { useState, useRef, useCallback } from 'react';

interface VoiceInputOptions {
  onResult?: (transcript: string) => void;
  onFinalResult?: (finalTranscript: string) => void;
  onError?: (error: string) => void;
  language?: string;
}

interface VoiceInputState {
  isSupported: boolean;
  isListening: boolean;
  isMicrophoneActive: boolean;  // Tracks if mic button is "on" (user intent)
  hasPermission: boolean;
  currentTranscript: string;
  error: string | null;
}

export function useVoiceInput(options: VoiceInputOptions = {}) {
  const {
    onResult,
    onFinalResult,
    onError,
    language = 'en-US'
  } = options;

  const [state, setState] = useState<VoiceInputState>({
    isSupported: checkVoiceSupport(),
    isListening: false,
    isMicrophoneActive: false,
    hasPermission: false,
    currentTranscript: '',
    error: null
  });

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const finalTranscriptRef = useRef<string>('');

  // Check if browser supports speech recognition
  function checkVoiceSupport(): boolean {
    const hasMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    const hasSpeechRecognition = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
    return hasMediaDevices && hasSpeechRecognition;
  }

  // Request microphone permission
  const requestPermission = useCallback(async (): Promise<void> => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setState(prev => ({ ...prev, hasPermission: true, error: null }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Permission denied';
      setState(prev => ({ ...prev, hasPermission: false, error: errorMessage }));
      throw new Error(errorMessage);
    }
  }, []);

  // Initialize speech recognition
  const initializeSpeechRecognition = useCallback(() => {
    if (!state.isSupported) {
      throw new Error('Speech recognition is not supported');
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = language;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      // Update current transcript
      const currentTranscript = interimTranscript;
      setState(prev => ({ ...prev, currentTranscript, error: null }));

      // Update final transcript
      if (finalTranscript) {
        finalTranscriptRef.current += finalTranscript;
      }

      // Call result callback with combined transcript
      const combinedTranscript = finalTranscriptRef.current + currentTranscript;
      if (onResult && combinedTranscript.trim()) {
        onResult(combinedTranscript);
      }

      // Call final result callback when we have final text
      if (finalTranscript && onFinalResult) {
        const fullFinalTranscript = finalTranscriptRef.current.trim();
        if (fullFinalTranscript) {
          onFinalResult(fullFinalTranscript);
          finalTranscriptRef.current = ''; // Reset after sending
        }
      }
    };

    recognition.onerror = (event) => {
      const errorMessage = `Speech recognition error: ${event.error}`;
      setState(prev => ({ ...prev, error: errorMessage, isListening: false }));
      if (onError) {
        onError(event.error);
      }
    };

    recognition.onend = () => {
      setState(prev => ({ ...prev, isListening: false }));
    };

    recognitionRef.current = recognition;
    return recognition;
  }, [state.isSupported, language, onResult, onFinalResult, onError]);

  // Start listening
  const startListening = useCallback(async () => {
    try {
      if (!state.hasPermission) {
        await requestPermission();
      }

      if (!recognitionRef.current) {
        initializeSpeechRecognition();
      }

      if (recognitionRef.current) {
        setState(prev => ({ ...prev, isListening: true, error: null, currentTranscript: '' }));
        finalTranscriptRef.current = '';
        recognitionRef.current.start();
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to start listening';
      setState(prev => ({ ...prev, error: errorMessage, isListening: false }));
      if (onError) {
        onError(errorMessage);
      }
    }
  }, [state.hasPermission, requestPermission, initializeSpeechRecognition, onError]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current && state.isListening) {
      recognitionRef.current.stop();
      setState(prev => ({ ...prev, isListening: false }));
    }
  }, [state.isListening]);

  // Toggle listening
  const toggleListening = useCallback(() => {
    if (state.isMicrophoneActive) {
      // Turn off microphone
      setState(prev => ({ ...prev, isMicrophoneActive: false }));
      stopListening();
    } else {
      // Turn on microphone
      setState(prev => ({ ...prev, isMicrophoneActive: true }));
      startListening();
    }
  }, [state.isMicrophoneActive, startListening, stopListening]);

  // Reset transcript
  const resetTranscript = useCallback(() => {
    finalTranscriptRef.current = '';
    setState(prev => ({ ...prev, currentTranscript: '' }));
  }, []);

  return {
    ...state,
    startListening,
    stopListening,
    toggleListening,
    resetTranscript
  };
}
