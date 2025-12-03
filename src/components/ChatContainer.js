import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./ChatContainer.css";
import axios from "axios";
import FAQ from "./FAQ";
import ChartRenderer from "./ChartRenderer";

const ChatContainer = ({
  onMapRequest = () => {},
  onMapData = () => {},
  onTableData = () => {},
  showChatHistory = false,
  onToggleChatHistory = () => {},
}) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [showFAQ, setShowFAQ] = useState(false);
  const [highlightFAQ, setHighlightFAQ] = useState(true);
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const userRequestedMapRef = useRef(false);
  
  // Chat history state
  const [chatHistory, setChatHistory] = useState([
    { id: 1, title: 'Ocean Temperature Analysis', date: '2024-01-15', preview: 'Analyzing temperature trends in Pacific...' },
    { id: 2, title: 'Salinity Data Query', date: '2024-01-14', preview: 'Looking at salinity levels in Arctic...' },
    { id: 3, title: 'Deep Ocean Exploration', date: '2024-01-13', preview: 'Exploring abyssal zone characteristics...' },
    { id: 4, title: 'Current Patterns Study', date: '2024-01-12', preview: 'Understanding ocean current patterns...' }
  ]);
  const [activeChat, setActiveChat] = useState(null);

  const actionOptions = [

    {
      title: "Analyse Data",
      description: "Perform analysis on oceanographic datasets",
      icon: "fa-chart-line",
      prompt: "I want to analyse oceanographic data",
    },
    {
      title: "Use Map",
      description: "Visualize data on interactive ocean maps",
      icon: "fa-map",
      prompt: "Show me data on the map",
    },
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

  // Load persisted chat state on mount
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem("floatchat_messages");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) setMessages(parsed);
      }
      const savedInput = sessionStorage.getItem("floatchat_input");
      if (savedInput) setInputValue(savedInput);
    } catch (_) {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Persist chat state on change
  useEffect(() => {
    try {
      sessionStorage.setItem("floatchat_messages", JSON.stringify(messages));
    } catch (_) {}
  }, [messages]);

  useEffect(() => {
    try {
      sessionStorage.setItem("floatchat_input", inputValue);
    } catch (_) {}
  }, [inputValue]);

  const handleOptionClick = async (option) => {
    const newMessages = [...messages, { type: "user", content: option.prompt }];
    setMessages(newMessages);

    // For 'Use Map', we still show fetching message, but open map only after backend returns show_map
    if (option.title === "Use Map") {
      userRequestedMapRef.current = true;
      setMessages((prev) => [
        ...prev,
        { type: "bot", content: "Fetching details..." },
      ]);
    }

    try {
      const response = await axios.post("http://127.0.0.1:8000", {
        query: option.prompt,
      });

      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          content: response.data.message,
          chartData: response.data.chart_data,
          tableData: response.data.table_data,
          hasData: response.data.has_data,
        },
      ]);

      // Open map overlay only if backend explicitly indicates AND there's no table view requested
      if (
        userRequestedMapRef.current &&
        response.data.show_map &&
        response.data.map_data &&
        !response.data.table_data
      ) {
        onMapData(response.data.map_data, true);
      }
      // Handle table data if present
      if (response.data.table_data) {
        onTableData(response.data.table_data);
      }
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          content: "⚠️ Sorry, could not fetch response from server.",
        },
      ]);
    }
  };

  const handleSend = async () => {
    if (inputValue.trim()) {
      // Add user message
      console.log("handle send");
      const newMessages = [...messages, { type: "user", content: inputValue }];
      setMessages(newMessages);

      // Store the current query before clearing
      const query = inputValue;
      setInputValue("");

      // Check if user is asking for map-related functionality
      const mapKeywords = [
        "map",
        "visualize",
        "show location",
        "geographic",
        "coordinates",
        "latitude",
        "longitude",
        "plot",
        "chart",
      ];
      const isMapRequest = mapKeywords.some((keyword) =>
        query.toLowerCase().includes(keyword.toLowerCase())
      );

      try {
        // Call FastAPI backend
        const response = await axios.post("http://127.0.0.1:8000", {
          query: query,
        });

        // Add bot message with response
        setMessages((prev) => [
          ...prev,
          {
            type: "bot",
            content: response.data.message,
            chartData: response.data.chart_data,
            tableData: response.data.table_data,
            hasData: response.data.has_data,
          },
        ]);

        // Open map overlay only if backend explicitly indicates AND there's no table view requested
        if (
          response.data.show_map &&
          response.data.map_data &&
          !response.data.table_data
        ) {
          onMapData(response.data.map_data, true);
        }
        // Handle table data if present
        if (response.data.table_data) {
          onTableData(response.data.table_data);
        }
      } catch (error) {
        console.log("Error fetching response:", error);
        setMessages((prev) => [
          ...prev,
          {
            type: "bot",
            content: "⚠️ Sorry, something went wrong connecting to the server.",
          },
        ]);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  const selectChat = (chatId) => {
    setActiveChat(chatId);
    // Here you would load the selected chat conversation
  };

  const deleteChat = (chatId, e) => {
    e.stopPropagation();
    setChatHistory(chatHistory.filter(chat => chat.id !== chatId));
    if (activeChat === chatId) {
      setActiveChat(null);
    }
  };

  const startNewChat = () => {
    setActiveChat(null);
    setMessages([]);
    onToggleChatHistory();
  };

  return (
    <main className="chat-container" id="chat">
      {/* Top buttons */}
      <div className="top-buttons">
        <button
          className="chat-history-icon-btn"
          onClick={onToggleChatHistory}
          aria-label="Toggle Chat History"
        >
          <i className="fas fa-comments"></i>
        </button>
        <button
          className="dashboard-top-btn"
          onClick={() => navigate("/dashboard")}
          aria-label="Open Dashboard"
        >
          <i className="fas fa-chart-line"></i>
          Dashboard
        </button>
      </div>
      
      {/* FAQ Button */}
      <button
        className={`faq-button ${highlightFAQ ? "highlight" : ""}`}
        onClick={() => setShowFAQ(true)}
        aria-label="Open Frequently Asked Questions"
      >
        <i className="fas fa-question-circle"></i>
        FAQ
      </button>

      {/* Chat History Slide-in Panel */}
      {showChatHistory && (
        <>
          <div className="chat-history-overlay" onClick={onToggleChatHistory}></div>
          <div className="chat-history-panel">
            <div className="chat-history-header">
              <h2>
                <i className="fas fa-comments"></i>
                Chat History
              </h2>
              <button className="close-panel-btn" onClick={onToggleChatHistory}>
                <i className="fas fa-times"></i>
              </button>
            </div>
            
            <button className="new-chat-btn" onClick={startNewChat}>
              <i className="fas fa-plus"></i>
              <span>New Chat</span>
            </button>

            <div className="chat-history-list">
              {chatHistory.map((chat) => (
                <div
                  key={chat.id}
                  className={`chat-history-item ${activeChat === chat.id ? "active" : ""}`}
                  onClick={() => selectChat(chat.id)}
                >
                  <div className="chat-info">
                    <div className="chat-title">{chat.title}</div>
                    <div className="chat-meta">
                      <span className="chat-date">{chat.date}</span>
                      <span className="chat-preview">{chat.preview}</span>
                    </div>
                  </div>
                  <button
                    className="delete-chat-btn"
                    onClick={(e) => deleteChat(chat.id, e)}
                    title="Delete chat"
                  >
                    <i className="fas fa-trash"></i>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

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
                {/* <img src={logo} alt="FloatChat logo" className="chat-logo" /> */}
              </div>
              <h2>How can I help you today?</h2>
              <p>
                I'm your oceanographic data assistant. Choose an option below to
                get started:
              </p>

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
            <React.Fragment key={index}>
              <div className={`message ${message.type}-message`}>
                <div className={`message-header ${message.type}-header`}>
                  <i
                    className={`fas ${
                      message.type === "user" ? "fa-user" : "fa-robot"
                    }`}
                  ></i>
                  {message.type === "user" ? "You" : "FloatChat"}
                </div>
                {message.content}
              </div>

              {/* Chart renderer, if available */}
              {message.chartData && message.type === "bot" && (
                <ChartRenderer chartData={message.chartData} />
              )}
            </React.Fragment>
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
