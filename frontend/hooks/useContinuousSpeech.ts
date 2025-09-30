import { useEffect, useRef, useState } from 'react';

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export function useContinuousSpeech(onTranscriptUpdate: (text: string) => void, enabled: boolean) {
  const recognitionRef = useRef<any>(null);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    console.log('🎤 DEBUG: useContinuousSpeech - enabled:', enabled);
    if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
      console.log('🎤 Speech recognition not supported in this browser');
      return;
    }

    if (!enabled) {
      // Stop recognition if disabled
      if (recognitionRef.current) {
        // console.log('🎤 Stopping speech recognition (disabled)');
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
      setIsListening(false);
      return;
    }

    // console.log('🎤 Starting speech recognition...');
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
      // console.log('🎤 Speech recognition started');
      setIsListening(true);
    };

    recognition.onend = () => {
      // console.log('🎤 Speech recognition ended');
      // Only restart if still enabled
      if (enabled) {
        setTimeout(() => {
          if (recognitionRef.current && enabled) {
            // console.log('🎤 Restarting speech recognition...');
            recognitionRef.current.start();
          }
        }, 500);
      } else {
          setIsListening(false);
      }
    };

    recognition.onerror = (event: any) => {
      console.log('🎤 Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onresult = (event: any) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        transcript += result[0].transcript;
      }
      console.log('🎤 Transcript:', transcript);
      onTranscriptUpdate(transcript);
    };


    if (!recognitionRef?.current && enabled) {
      recognition.start();
      recognitionRef.current = recognition;
    }

    return () => {
      // console.log('🎤 Cleaning up speech recognition...');
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
    };
  }, [enabled]);

  return { isListening };
}
