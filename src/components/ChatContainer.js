import React, { useState, useEffect, useRef } from 'react';
import './ChatContainer.css';
import axios from 'axios';

const ChatContainer = ({ onMapRequest }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);
  
  const actionOptions = [
    {
      title: "Retrieve Argo Data",
      description: "Access oceanographic data from ARGO floats worldwide",
      icon: "fa-download",
      prompt: "Help me retrieve ARGO float data"
    },
    {
      title: "Analyse Data",
      description: "Perform analysis on oceanographic datasets",
      icon: "fa-chart-line",
      prompt: "I want to analyse oceanographic data"
    },
    {
      title: "Use Map",
      description: "Visualize data on interactive ocean maps",
      icon: "fa-map",
      prompt: "Show me data on the map"
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleOptionClick = async (option) => {
  const newMessages = [...messages, { type: 'user', content: option.prompt }];
  setMessages(newMessages);

  // Trigger map view if this is the "Use Map" action
  if (option.title === "Use Map" && onMapRequest) {
    onMapRequest();
  }

  try {
    const response = await axios.post("http://127.0.0.1:8000", {
      query: option.prompt,
    });

    setMessages(prev => [
      ...prev,
      { type: 'bot', content: response.data.message }
    ]);
  } catch (error) {
    console.error("Error fetching response:", error);
    setMessages(prev => [
      ...prev,
      { type: 'bot', content: "⚠️ Could not fetch response from server." }
    ]);
  }
};


  const handleSend = async () => {
  if (inputValue.trim()) {
    // Add user message
    console.log("handle send");
    const newMessages = [...messages, { type: 'user', content: inputValue }];
    setMessages(newMessages);

    // Store the current query before clearing
    const query = inputValue;
    setInputValue('');

    // Check if user is asking for map-related functionality
    const mapKeywords = ['map', 'visualize', 'show location', 'geographic', 'coordinates', 'latitude', 'longitude', 'plot', 'chart'];
    const isMapRequest = mapKeywords.some(keyword => 
      query.toLowerCase().includes(keyword.toLowerCase())
    );
    
    if (isMapRequest && onMapRequest) {
      onMapRequest();
    }

    try {
      // Call FastAPI backend
      const response = await axios.post("http://127.0.0.1:8000", {
        query: query,
      });

      // Add bot message with response
      setMessages(prev => [
        ...prev,
        { type: 'bot', content: response.data.message }
      ]);

    } catch (error) {
      console.log("Error fetching response:", error);
      setMessages(prev => [
        ...prev,
        { type: 'bot', content: "⚠️ Sorry, something went wrong connecting to the server." }
      ]);
    }
  }
};

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <main className="chat-container" id="chat">
      <div className="chat-header">
        <h1>FloatChat</h1>
        <p>Your friendly marine scientist</p>
      </div>

      <div className="chat-messages" id="messages">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <div className="welcome-content">
              <div className="welcome-icon">
                <i className="fas fa-robot"></i>
              </div>
              <h2>How can I help you today?</h2>
              <p>I'm your oceanographic data assistant. Choose an option below to get started:</p>
              
              <div className="action-options">
                {actionOptions.map((option, index) => (
                  <div 
                    key={index} 
                    className="action-card"
                    onClick={() => handleOptionClick(option)}
                  >
                    <div className="action-icon">
                      <i className={`fas ${option.icon}`}></i>
                    </div>
                    <div className="action-content">
                      <h3>{option.title}</h3>
                      <p>{option.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message ${message.type}-message`}>
              <div className={`message-header ${message.type}-header`}>
                <i className={`fas ${message.type === 'user' ? 'fa-user' : 'fa-robot'}`} aria-hidden="true"></i>
                {message.type === 'user' ? 'You' : 'FloatChat'}
              </div>
              {message.content}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <input 
          type="text" 
          placeholder="Ask about ocean data..." 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          aria-label="Ask about ocean data"
        />
        <button onClick={handleSend} id="sendBtn">
          <i className="fas fa-paper-plane" aria-hidden="true"></i>
          Send
        </button>
      </div>
    </main>
  );
};

export default ChatContainer;