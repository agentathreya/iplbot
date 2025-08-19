import React from 'react';
import { ChatMessage as ChatMessageType } from '../types';
import { User, Bot, Clock, Database } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import DataTable from './DataTable';

interface Props {
  message: ChatMessageType;
}

const ChatMessage: React.FC<Props> = ({ message }) => {
  const isUser = message.type === 'user';

  if (message.isLoading) {
    return (
      <div className="flex items-start space-x-3 message-appear">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
        </div>
        <div className="flex-1 bg-gray-100 rounded-lg p-4">
          <div className="typing-indicator">
            <span className="text-sm text-gray-600 mr-2">Thinking</span>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex items-start space-x-3 message-appear ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-green-500' : 'bg-blue-500'
        }`}>
          {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
        </div>
      </div>

      {/* Message content */}
      <div className="flex-1 max-w-4xl">
        <div className={`rounded-lg p-4 ${
          isUser 
            ? 'bg-green-500 text-white ml-auto max-w-md' 
            : 'bg-white border border-gray-200 shadow-sm'
        }`}>
          {/* Main message */}
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {/* Metadata for bot responses */}
          {!isUser && (message.executionTime || message.matchedPlayers?.length) && (
            <div className="mt-3 pt-3 border-t border-gray-100 flex items-center space-x-4 text-xs text-gray-500">
              {message.executionTime && (
                <div className="flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{message.executionTime}s</span>
                </div>
              )}
              
              {message.matchedPlayers && message.matchedPlayers.length > 0 && (
                <div className="flex items-center space-x-1">
                  <User className="w-3 h-3" />
                  <span>Players: {message.matchedPlayers.join(', ')}</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Data table */}
        {!isUser && message.data && message.data.length > 0 && (
          <div className="mt-3">
            <DataTable data={message.data} />
          </div>
        )}

        {/* SQL Query */}
        {!isUser && message.sqlQuery && (
          <div className="mt-3">
            <details className="group">
              <summary className="cursor-pointer flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900">
                <Database className="w-4 h-4" />
                <span>View SQL Query</span>
                <span className="group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="mt-2 rounded-lg overflow-hidden border">
                <SyntaxHighlighter 
                  language="sql" 
                  style={tomorrow}
                  customStyle={{
                    margin: 0,
                    fontSize: '12px'
                  }}
                >
                  {message.sqlQuery}
                </SyntaxHighlighter>
              </div>
            </details>
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;