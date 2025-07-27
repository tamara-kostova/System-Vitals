import React, { useState, useEffect, useRef } from 'react';

const SystemDashboard = () => {
  const [systemData, setSystemData] = useState(null);
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: '👋 Hi! I\'m your system assistant. Ask me anything about your computer\'s performance!', timestamp: new Date() }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const wsRef = useRef(null);
  const chatMessagesRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = 'ws://localhost:8000/ws';
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('🔗 WebSocket connected');
        setIsConnected(true);
      };
      
      wsRef.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'system_data') {
          setSystemData(message.data);
          setLastUpdate(new Date(message.timestamp));
        } else if (message.type === 'chat_response') {
          setChatMessages(prev => [...prev, {
            role: 'assistant',
            content: message.response,
            timestamp: new Date(message.timestamp)
          }]);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('❌ WebSocket disconnected');
        setIsConnected(false);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Auto-scroll chat messages
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Send chat message
  const sendChatMessage = (message) => {
    if (!message.trim() || !wsRef.current) return;
    
    // Add user message to chat
    setChatMessages(prev => [...prev, {
      role: 'user',
      content: message,
      timestamp: new Date()
    }]);
    
    // Send to server via WebSocket
    wsRef.current.send(JSON.stringify({
      type: 'chat',
      message: message
    }));
    
    setChatInput('');
  };

  const handleChatSubmit = () => {
    sendChatMessage(chatInput);
  };

  const getStatusColor = (percentage, type = 'default') => {
    if (type === 'disk' && percentage > 85) return 'bg-red-500';
    if (percentage > 80) return 'bg-red-500';
    if (percentage > 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getProgressColor = (percentage, type = 'cpu') => {
    if (type === 'cpu') return 'from-blue-400 to-blue-600';
    if (type === 'memory') return 'from-green-400 to-green-600';
    if (type === 'disk') return 'from-orange-400 to-orange-600';
    return 'from-gray-400 to-gray-600';
  };

  const formatUptime = (hours) => {
    if (hours < 24) return `${hours.toFixed(1)}h`;
    const days = Math.floor(hours / 24);
    const remainingHours = Math.floor(hours % 24);
    return `${days}d ${remainingHours}h`;
  };

  if (!systemData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-lg">Connecting to system monitor...</p>
          <p className="text-sm opacity-75">
            {isConnected ? 'Connected - Loading data...' : 'Establishing connection...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
        
        {/* Main Dashboard - 2 columns on large screens */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Connection Status */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
                <span className="text-white font-medium">
                  {isConnected ? 'System Connected' : 'Disconnected'}
                </span>
              </div>
              {lastUpdate && (
                <span className="text-white/70 text-sm">
                  Last update: {lastUpdate.toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>

          {/* System Overview Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* System Info Card */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white text-lg font-semibold">System Overview</h3>
                <div className={`w-3 h-3 rounded-full ${getStatusColor(50)} animate-pulse`}></div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-white/60 uppercase tracking-wide text-xs">Platform</p>
                  <p className="text-white font-medium">{systemData.system.platform} {systemData.system.release}</p>
                </div>
                <div>
                  <p className="text-white/60 uppercase tracking-wide text-xs">Uptime</p>
                  <p className="text-white font-medium">{formatUptime(systemData.uptime_hours)}</p>
                </div>
                <div>
                  <p className="text-white/60 uppercase tracking-wide text-xs">CPU Cores</p>
                  <p className="text-white font-medium">{systemData.cpu.cores}</p>
                </div>
                <div>
                  <p className="text-white/60 uppercase tracking-wide text-xs">Frequency</p>
                  <p className="text-white font-medium">{systemData.cpu.frequency_mhz} MHz</p>
                </div>
              </div>
            </div>

            {/* CPU Usage Card */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white text-lg font-semibold">CPU Usage</h3>
                <div className={`w-3 h-3 rounded-full ${getStatusColor(systemData.cpu.usage_percent)} animate-pulse`}></div>
              </div>
              
              <div className="mb-4">
                <div className="text-white text-3xl font-bold mb-2">
                  {systemData.cpu.usage_percent}%
                </div>
                <div className="w-full bg-white/20 rounded-full h-2">
                  <div 
                    className={`bg-gradient-to-r ${getProgressColor(systemData.cpu.usage_percent, 'cpu')} h-2 rounded-full transition-all duration-500`}
                    style={{ width: `${systemData.cpu.usage_percent}%` }}
                  ></div>
                </div>
              </div>
              
              <p className="text-white/70 text-sm">
                {systemData.cpu.usage_percent < 50 ? '✅ Excellent performance' :
                 systemData.cpu.usage_percent < 75 ? '⚠️ Moderate usage' : '🔴 High usage'}
              </p>
            </div>

            {/* Memory Usage Card */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white text-lg font-semibold">Memory Usage</h3>
                <div className={`w-3 h-3 rounded-full ${getStatusColor(systemData.memory.usage_percent)} animate-pulse`}></div>
              </div>
              
              <div className="mb-4">
                <div className="text-white text-3xl font-bold mb-2">
                  {systemData.memory.usage_percent}%
                </div>
                <div className="w-full bg-white/20 rounded-full h-2">
                  <div 
                    className={`bg-gradient-to-r ${getProgressColor(systemData.memory.usage_percent, 'memory')} h-2 rounded-full transition-all duration-500`}
                    style={{ width: `${systemData.memory.usage_percent}%` }}
                  ></div>
                </div>
              </div>
              
              <div className="flex justify-between text-sm text-white/70">
                <span>{systemData.memory.used_gb} GB used</span>
                <span>{systemData.memory.total_gb} GB total</span>
              </div>
            </div>

            {/* Quick Actions Card */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-200">
              <h3 className="text-white text-lg font-semibold mb-4">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-2">
                <button 
                  onClick={() => sendChatMessage('What is my current system status?')}
                  className="bg-white/20 hover:bg-white/30 text-white text-xs py-2 px-3 rounded-lg transition-all duration-200 hover:scale-105"
                >
                  📊 System Status
                </button>
                <button 
                  onClick={() => sendChatMessage('Is my CPU usage normal?')}
                  className="bg-white/20 hover:bg-white/30 text-white text-xs py-2 px-3 rounded-lg transition-all duration-200 hover:scale-105"
                >
                  🔥 CPU Check
                </button>
                <button 
                  onClick={() => sendChatMessage('How much memory am I using?')}
                  className="bg-white/20 hover:bg-white/30 text-white text-xs py-2 px-3 rounded-lg transition-all duration-200 hover:scale-105"
                >
                  💾 Memory Check
                </button>
                <button 
                  onClick={() => sendChatMessage('Check my disk space')}
                  className="bg-white/20 hover:bg-white/30 text-white text-xs py-2 px-3 rounded-lg transition-all duration-200 hover:scale-105"
                >
                  💿 Disk Space
                </button>
              </div>
            </div>
          </div>

          {/* Disk Usage Card - Full Width */}
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-200">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-white text-lg font-semibold">Disk Usage</h3>
              <div className={`w-3 h-3 rounded-full ${getStatusColor(Math.max(...systemData.disks.map(d => d.percentage)), 'disk')} animate-pulse`}></div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {systemData.disks.map((disk, index) => (
                <div key={index} className="bg-white/10 rounded-lg p-4 border-l-4 border-blue-400">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-white font-semibold">{disk.device}</span>
                    <span className="text-white/70 text-sm">{disk.percentage}% used</span>
                  </div>
                  
                  <div className="w-full bg-white/20 rounded-full h-2 mb-2">
                    <div 
                      className={`bg-gradient-to-r ${getProgressColor(disk.percentage, 'disk')} h-2 rounded-full transition-all duration-500`}
                      style={{ width: `${disk.percentage}%` }}
                    ></div>
                  </div>
                  
                  <div className="flex justify-between text-xs text-white/60">
                    <span>{disk.used_gb} GB used</span>
                    <span>{disk.free_gb} GB free</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Chat Panel - 1 column on large screens */}
        <div className="lg:col-span-1">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 h-full flex flex-col">
            
            {/* Chat Header */}
            <div className="p-6 border-b border-white/20">
              <h3 className="text-white text-lg font-semibold mb-2">System Assistant</h3>
              <p className="text-white/70 text-sm">Ask me about your system performance</p>
            </div>
            
            {/* Chat Messages */}
            <div 
              ref={chatMessagesRef}
              className="flex-1 p-6 overflow-y-auto max-h-96 space-y-4"
            >
              {chatMessages.map((message, index) => (
                <div
                  key={index}
                  className={`max-w-[85%] p-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white ml-auto'
                      : 'bg-white/20 text-white border border-white/20'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                  {message.timestamp && (
                    <div className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            {/* Chat Input */}
            <div className="p-6 border-t border-white/20">
              <div className="space-y-3">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendChatMessage(chatInput); 
                    }
                  }}
                  placeholder="Ask about system performance..."
                  className="w-full px-4 py-3 bg-white/20 border border-white/30 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-white/50 focus:bg-white/25 transition-all duration-200"
                />
                <button
                  onClick={() => sendChatMessage(chatInput)}
                  disabled={!chatInput.trim() || !isConnected}
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-500 disabled:to-gray-600 text-white py-3 px-4 rounded-lg font-medium transition-all duration-200 hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
                >
                  {isConnected ? 'Send Message' : 'Connecting...'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemDashboard;