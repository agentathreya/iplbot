import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { BarChart3, Users, MapPin, Trophy, AlertCircle, RefreshCw } from 'lucide-react';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import DataTable from './components/DataTable';
import { ChatMessage as ChatMessageType, SummaryStats } from './types';
import { apiService } from './services/api';

function App() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [summaryStats, setSummaryStats] = useState<SummaryStats | null>(null);
  const [isConnected, setIsConnected] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize with welcome message and load summary stats
    const welcomeMessage: ChatMessageType = {
      id: uuidv4(),
      type: 'bot',
      content: `# Welcome to IPL Cricket Analytics Chatbot! 🏏

I'm your cricket analytics assistant powered by comprehensive IPL data. I can help you with:

**📊 Batting Analytics**
- Player statistics, averages, strike rates
- Performance in specific phases (powerplay, middle overs, death overs)
- Comparisons between players

**🎯 Bowling Analytics** 
- Economy rates, bowling averages, wicket counts
- Performance against different batting styles (LHB/RHB)
- Phase-wise bowling analysis

**🔥 Advanced Queries**
- "Best batters vs pace in death overs min 1000 runs"
- "Top economy rates in powerplay min 300 balls"
- "Kohli vs Rohit strike rate comparison"

**💡 Smart Features**
- Partial name matching (just type "Kohli" instead of full name)
- Automatic threshold filtering for meaningful results
- Custom minimum requirements (e.g., "min 500 runs")

Try asking me anything about IPL cricket statistics!`,
      timestamp: new Date(),
    };

    setMessages([welcomeMessage]);
    loadSummaryStats();
    checkConnection();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSummaryStats = async () => {
    try {
      const stats = await apiService.getSummaryStats();
      setSummaryStats(stats);
    } catch (error) {
      console.error('Failed to load summary stats:', error);
    }
  };

  const checkConnection = async () => {
    try {
      await apiService.healthCheck();
      setIsConnected(true);
      setError(null);
    } catch (error) {
      setIsConnected(false);
      setError('Unable to connect to server. Please check if the backend is running.');
    }
  };

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage: ChatMessageType = {
      id: uuidv4(),
      type: 'user',
      content,
      timestamp: new Date(),
    };

    // Add loading message
    const loadingMessage: ChatMessageType = {
      id: uuidv4(),
      type: 'bot',
      content: '',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiService.sendMessage(content);
      
      // Remove loading message and add response
      setMessages(prev => {
        const withoutLoading = prev.filter(msg => !msg.isLoading);
        const botMessage: ChatMessageType = {
          id: uuidv4(),
          type: 'bot',
          content: response.response,
          timestamp: new Date(),
          data: response.data,
          sqlQuery: response.sql_query,
          matchedPlayers: response.matched_players,
          executionTime: response.execution_time,
        };
        return [...withoutLoading, botMessage];
      });

    } catch (error: any) {
      // Remove loading message and add error
      setMessages(prev => {
        const withoutLoading = prev.filter(msg => !msg.isLoading);
        const errorMessage: ChatMessageType = {
          id: uuidv4(),
          type: 'bot',
          content: `❌ **Error**: ${error.message}\n\nPlease try rephrasing your question or check if the player names are correct.`,
          timestamp: new Date(),
        };
        return [...withoutLoading, errorMessage];
      });
      
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetryConnection = () => {
    checkConnection();
    loadSummaryStats();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">IPL Cricket Analytics</h1>
                <p className="text-sm text-gray-600">AI-Powered Cricket Statistics Chatbot</p>
              </div>
            </div>
            
            {/* Connection status */}
            <div className="flex items-center space-x-4">
              {!isConnected && (
                <button
                  onClick={handleRetryConnection}
                  className="flex items-center space-x-1 text-sm text-red-600 hover:text-red-800"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry</span>
                </button>
              )}
              
              <div className={`flex items-center space-x-2 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm font-medium">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      {summaryStats && (
        <div className="bg-blue-50 border-b border-blue-200">
          <div className="max-w-6xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <Trophy className="w-4 h-4 text-blue-600" />
                  <span className="text-blue-800 font-medium">
                    {summaryStats.total_matches?.toLocaleString()} Matches
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="w-4 h-4 text-blue-600" />
                  <span className="text-blue-800 font-medium">
                    {summaryStats.total_batters?.toLocaleString()} Players
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-blue-600" />
                  <span className="text-blue-800 font-medium">
                    {summaryStats.total_venues} Venues
                  </span>
                </div>
                <div className="text-blue-700">
                  📅 {summaryStats.earliest_date} - {summaryStats.latest_date}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200">
          <div className="max-w-6xl mx-auto px-4 py-2">
            <div className="flex items-center space-x-2 text-red-800">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        </div>
      )}

      {/* Chat Container */}
      <div className="max-w-6xl mx-auto px-4 py-6 flex-1">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-[calc(100vh-300px)] flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <ChatInput 
              onSendMessage={handleSendMessage} 
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="text-center text-sm text-gray-600">
            <p>
              🏏 Powered by comprehensive IPL data with ball-by-ball analytics
              {summaryStats && (
                <span className="ml-2">
                  • {summaryStats.total_balls?.toLocaleString()} balls analyzed
                </span>
              )}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;