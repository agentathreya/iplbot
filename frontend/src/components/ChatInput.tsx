import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Lightbulb } from 'lucide-react';

interface Props {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const ChatInput: React.FC<Props> = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const suggestions = [
    "Who scored the most runs in death overs?",
    "Best bowlers vs left-handed batsmen",
    "Kohli's strike rate in powerplay overs",
    "Most wickets taken in middle overs",
    "Dhoni's average in death overs min 200 runs",
    "Best economy rate in powerplay",
    "Most sixes hit by Rohit Sharma",
    "Bumrah's bowling average vs RHB",
    "Highest individual score in IPL",
    "Best bowling figures in a match",
    "Most runs in a single season",
    "Strike rate comparison: Kohli vs Rohit",
    "Team with most wins at Wankhede",
    "Most expensive over in IPL history"
  ];

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
      setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    textareaRef.current?.focus();
  };

  return (
    <div className="relative">
      {/* Suggestions dropdown */}
      {showSuggestions && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto z-10">
          <div className="p-2 border-b border-gray-100">
            <div className="flex items-center space-x-2 text-sm font-medium text-gray-700">
              <Lightbulb className="w-4 h-4" />
              <span>Example Questions</span>
            </div>
          </div>
          <div className="p-1">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input form */}
      <form onSubmit={handleSubmit} className="flex items-end space-x-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => !message && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder="Ask me anything about IPL cricket... (e.g., 'Who scored most runs in death overs min 1000 runs?')"
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={1}
            style={{ minHeight: '48px', maxHeight: '120px' }}
            disabled={isLoading}
          />
          
          {/* Suggestion trigger button */}
          {!message && !showSuggestions && (
            <button
              type="button"
              onClick={() => setShowSuggestions(true)}
              className="absolute right-12 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <Lightbulb className="w-4 h-4" />
            </button>
          )}
        </div>

        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>

      {/* Helper text */}
      <div className="mt-2 text-xs text-gray-500">
        <p>
          💡 Try queries like: "Kohli vs Rohit strike rate", "Best bowlers in death overs min 500 runs", 
          "Most sixes in powerplay"
        </p>
      </div>
    </div>
  );
};

export default ChatInput;