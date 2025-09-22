
import React from 'react';
import { marked } from 'marked';
import type { Message } from '../types';
import { RobotIcon, UserIcon } from './icons';

interface MessageBubbleProps {
  message: Message;
}

const MarkdownRenderer: React.FC<{ text: string; isBot: boolean }> = ({ text, isBot }) => {
  if (!isBot) {
    // User messages are plain text
    return <p className="whitespace-pre-wrap">{text}</p>;
  }

  // Bot messages use full markdown rendering
  // Ensure text is not null/undefined
  const safeText = text || '';
  const htmlContent = marked.parse(safeText);

  return (
    <div
      className="markdown-content"
      dangerouslySetInnerHTML={{ __html: htmlContent }}
    />
  );
};

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isBot = message.sender === 'bot';

  return (
    <div className={`flex items-start gap-3 ${isBot ? '' : 'justify-end'}`}>
      {isBot && (
        <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
          <RobotIcon className="w-5 h-5 text-slate-600" />
        </div>
      )}
      <div className={`flex flex-col ${isBot ? 'items-start' : 'items-end'}`}>
        <div
          className={`max-w-md rounded-lg p-3 text-sm ${
            isBot ? 'bg-slate-100 text-slate-800 rounded-tl-none' : 'bg-slate-900 text-white rounded-br-none'
          }`}
        >
          <MarkdownRenderer text={message.text} isBot={isBot} />
        </div>
        <p className="text-xs text-slate-400 mt-1.5">{message.timestamp}</p>
      </div>
       {!isBot && (
        <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
          <UserIcon className="w-5 h-5 text-slate-600" />
        </div>
      )}
    </div>
  );
};

export default MessageBubble;