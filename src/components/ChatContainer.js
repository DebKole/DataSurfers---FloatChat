import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './ChatContainer.css';
import axios from 'axios';
import FAQ from './FAQ';

const ChatContainer = ({ onMapRequest = () => { }, onMapData = () => { }, onTableData = () => { } }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [showFAQ, setShowFAQ] = useState(false);
  const [highlightFAQ, setHighlightFAQ] = useState(true);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const actionOptions = [
    // {
    //   title: "Retrieve Argo Data",
    //   description: "Access oceanographic data from ARGO floats worldwide",
    //   icon: "fa-download",
    //   prompt: "Help me retrieve ARGO float data"
    // },
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

  // Subtle FAQ highlight on initial load for ~6 seconds
  useEffect(() => {
    const t = setTimeout(() => setHighlightFAQ(false), 6000);
    return () => clearTimeout(t);
  }, []);

  const handleOptionClick = async (option) => {
    const newMessages = [...messages, { type: 'user', content: option.prompt }];
    setMessages(newMessages);

    // Open map immediately and continue backend call
    if (option.title === "Use Map") {
      setMessages(prev => [
        ...prev,
        { type: 'bot', content: 'Fetching details...' }
      ]);
      if (onMapRequest) onMapRequest();
    }

    try {
      const response = await axios.post("http://127.0.0.1:8000", {
        query: option.prompt,
      });

      setMessages(prev => [
        ...prev,
        { type: 'bot', content: response.data.message }
      ]);

      // Handle map data if present
      if (response.data.show_map && response.data.map_data) {
        onMapData(response.data.map_data, true);
      }
      // Handle table data if present
      if (response.data.table_data) {
        onTableData(response.data.table_data);
      }
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages(prev => [
        ...prev,
        { type: 'bot', content: "⚠️ Sorry, could not fetch response from server." }
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

        // Handle map data if present
        if (response.data.show_map && response.data.map_data) {
          onMapData(response.data.map_data, true);
        }
        // Handle table data if present
        if (response.data.table_data) {
          onTableData(response.data.table_data);
        }
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
      {/* Dashboard Button (top-left) */}
      <button 
        className="dashboard-top-btn"
        onClick={() => navigate('/dashboard')}
        aria-label="Open Dashboard"
      >
        <i className="fas fa-chart-line"></i>
        Dashboard
      </button>
      {/* FAQ Button */}
      <button 
        className={`faq-button ${highlightFAQ ? 'highlight' : ''}`}
        onClick={() => setShowFAQ(true)}
        aria-label="Open Frequently Asked Questions"
      >
        <i className="fas fa-question-circle"></i>
        FAQ
      </button>

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

      {/* FAQ Modal */}
      <FAQ isOpen={showFAQ} onClose={() => setShowFAQ(false)} />
    </main>
  );
};

export default ChatContainer;