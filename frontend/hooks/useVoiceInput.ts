/**
 * React hook for voice input using browser SpeechRecognition API
 * Provides continuous listening with automatic submission after pauses
 */

import { useState, useRef, useCallback } from 'react';

interface VoiceInputOptions {
  onResult?: (transcript: string) => void;
  onFinalResult?: (finalTranscript: string, isMicrophoneActive: boolean) => void;
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
  const isMicrophoneActiveRef = useRef<boolean>(false); // Track current microphone state
  const submitTimeoutRef = useRef<NodeJS.Timeout | null>(null); // Debounce timer

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
        const result = event.results[i];
        const transcript = result[0].transcript;
        const confidence = result[0].confidence;

        console.log('🎤 DEBUG: Result -', 'isFinal:', result.isFinal, 'confidence:', confidence, 'text:', transcript);

        if (result.isFinal) {
          // Check confidence if available (mobile Chrome), otherwise accept all final results
          const hasGoodConfidence = confidence === undefined || confidence > 0.1;
          if (hasGoodConfidence) {
            finalTranscript += transcript;
            console.log('🎤 DEBUG: Accepted final result with confidence:', confidence);
          } else {
            console.log('🎤 DEBUG: Rejected low confidence result:', confidence);
          }
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

      // Submit immediately if we have high-confidence final results
      if (finalTranscript && onFinalResult) {
        // Clear any existing timeout
        if (submitTimeoutRef.current) {
          clearTimeout(submitTimeoutRef.current);
        }

        // Submit after a short delay to allow for additional results
        submitTimeoutRef.current = setTimeout(() => {
          const fullFinalTranscript = finalTranscriptRef.current.trim();
          if (fullFinalTranscript) {
            console.log('🎤 DEBUG: Submitting high-confidence result:', fullFinalTranscript);
            onFinalResult(fullFinalTranscript, isMicrophoneActiveRef.current);
            finalTranscriptRef.current = ''; // Reset after sending
          }
        }, 500); // Short delay to batch multiple final results
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
      console.log('🎤 DEBUG: Speech recognition ended, current isMicrophoneActive:', state.isMicrophoneActive);
      setState(prev => ({ ...prev, isListening: false }));

      // Submit accumulated transcript when speech recognition ends (natural pause)
      if (onFinalResult && finalTranscriptRef.current.trim()) {
        const fullFinalTranscript = finalTranscriptRef.current.trim();
        console.log('🎤 DEBUG: Submitting on speech end:', fullFinalTranscript);
        onFinalResult(fullFinalTranscript, isMicrophoneActiveRef.current);
        finalTranscriptRef.current = ''; // Reset after sending
      }
    };

    recognitionRef.current = recognition;
    return recognition;
  }, [state.isSupported, language, onResult, onFinalResult, onError]);

  // Start listening
  const startListening = useCallback(async () => {
    console.log('🎤 DEBUG: startListening called, current isMicrophoneActive:', state.isMicrophoneActive);
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
        console.log('🎤 DEBUG: Speech recognition started');
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
    // Clear any pending submission timeout
    if (submitTimeoutRef.current) {
      clearTimeout(submitTimeoutRef.current);
      submitTimeoutRef.current = null;
    }
  }, [state.isListening]);

  // Toggle listening
  const toggleListening = useCallback(() => {
    console.log('🎤 DEBUG: toggleListening called, current isMicrophoneActive:', state.isMicrophoneActive);
    if (state.isMicrophoneActive) {
      // Turn off microphone
      console.log('🎤 DEBUG: Turning OFF microphone');
      isMicrophoneActiveRef.current = false;
      setState(prev => ({ ...prev, isMicrophoneActive: false }));
      stopListening();
    } else {
      // Turn on microphone
      console.log('🎤 DEBUG: Turning ON microphone');
      isMicrophoneActiveRef.current = true;
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
