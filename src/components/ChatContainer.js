import React, { useState, useEffect, useRef } from 'react';
import './ChatContainer.css';

const ChatContainer = () => {
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

  const handleOptionClick = (option) => {
    setInputValue(option.prompt);
    // Optionally auto-send the message
    const newMessages = [...messages, { type: 'user', content: option.prompt }];
    setMessages(newMessages);
    setInputValue('');
    
    // Simulate bot response after a delay
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        type: 'bot', 
        content: `Great! I'll help you ${option.title.toLowerCase()}. Let me know what specific information you need.` 
      }]);
    }, 700);
  };

  const handleSend = () => {
    if (inputValue.trim()) {
      // Add user message
      const newMessages = [...messages, { type: 'user', content: inputValue }];
      setMessages(newMessages);
      setInputValue('');
      
      // Simulate bot response after a delay
      setTimeout(() => {
        setMessages(prev => [...prev, { 
          type: 'bot', 
          content: "Nice question — in a real app I would fetch ARGO data and display charts here." 
        }]);
      }, 700);
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