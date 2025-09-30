import { useState, useRef, useCallback } from 'react';

export function useTextToSpeech(options: { onStart?: () => void; onEnd?: () => void; onError?: (error: string) => void } = {}) {
  const { onStart, onEnd, onError } = options;
  const [isSpeaking, setIsSpeaking] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsSpeaking(false);
    if (onEnd) onEnd();
  }, [onEnd]);

  const speak = useCallback(async (text: string) => {
    if (!text.trim()) return;

    stopSpeaking();

    try {
      const response = await fetch('/api/tts/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice: 'alloy', model: 'tts-1' })
      });

      if (!response.ok) throw new Error('TTS API error');

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audioRef.current = audio;

      audio.onplay = () => {
        setIsSpeaking(true);
        console.log('TTS playback started');
        if (onStart) onStart();
      };

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        setIsSpeaking(false);
        audioRef.current = null;
        console.log('TTS playback ended');
        if (onEnd) onEnd();
      };

      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        setIsSpeaking(false);
        audioRef.current = null;
        if (onError) onError('Audio playback failed');
      };

      await audio.play();

    } catch (error) {
      setIsSpeaking(false);
      if (onError) onError(error instanceof Error ? error.message : 'TTS failed');
    }
  }, [stopSpeaking]);

  return {
    isSpeaking,
    speak,
    stopSpeaking
  };
}
