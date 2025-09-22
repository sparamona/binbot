import React, { useEffect, useRef } from 'react';
import type { Message } from '../types';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { RobotIcon } from './icons';
import { useApiStatus } from '../hooks/useApi';

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  onCameraClick: () => void;
  isLoading?: boolean;
  onVoiceStateChange?: (isListening: boolean) => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage, onCameraClick, isLoading = false, onVoiceStateChange }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isConnected } = useApiStatus();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <header className="flex items-center p-4 border-b border-slate-200">
        <RobotIcon className="w-6 h-6 mr-3" />
        <h1 className="text-lg font-semibold">BinBot</h1>
        <div className="ml-auto flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2 w-2">
              {isConnected ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </>
              ) : (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
              )}
            </span>
            <span className="text-sm text-slate-500">
              {isConnected === null ? 'Connecting...' : isConnected ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
      </header>
      <div className="flex-1 p-6 overflow-y-auto bg-slate-50/50">
        <div className="space-y-6">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isLoading && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
                <RobotIcon className="w-5 h-5 text-slate-600" />
              </div>
              <div className="flex flex-col items-start">
                <div className="max-w-md rounded-lg p-3 text-sm bg-slate-100 text-slate-800 rounded-tl-none">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      <ChatInput
        onSendMessage={onSendMessage}
        onCameraClick={onCameraClick}
        disabled={isLoading || !isConnected}
        onVoiceStateChange={onVoiceStateChange}
      />
    </div>
  );
};

export default ChatPanel;