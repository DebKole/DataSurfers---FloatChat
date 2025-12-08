import React, { useMemo, useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./ChatContainer.css";
import axios from "axios";
import FAQ from "./FAQ";
import ChartRenderer from "./ChartRenderer";
import logo from "../assets/Logo (3).png";

// QuestionPanel component
export const QuestionPanel = ({ onQuestionClick }) => {
  const questions = [
    "Show me ocean temperature trends",
    "What's the current sea level?",
    "Analyze water quality data"
  ];

  return (
    <div className="question-panel">
      <div className="question-panel-title">Quick Start</div>
      <div className="suggested-questions">
        {questions.map((question, index) => (
          <button
            key={index}
            className="suggested-question"
            onClick={() => onQuestionClick(question)}
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
};

const ChatContainer = ({
  onMapRequest = () => {},
  onMapData = () => {},
  onTableData = () => {},
  showChatHistory = false,
  onToggleChatHistory = () => {},
  chatHistory = [],
  onSelectChat = () => {},
}) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [showFAQ, setShowFAQ] = useState(false);
  const [highlightFAQ, setHighlightFAQ] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const [showHistoryBox, setShowHistoryBox] = useState(false);
  
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();
  const userRequestedMapRef = useRef(false);
  
  // Chat history state
  const [activeChat, setActiveChat] = useState(null);
  const [localChatHistory, setLocalChatHistory] = useState(
    chatHistory.length > 0 
      ? chatHistory 
      : [
          { id: 1, title: 'Ocean Temperature Analysis', date: '2024-01-15', preview: 'Analyzing temperature trends in Pacific...' },
          { id: 2, title: 'Salinity Data Query', date: '2024-01-14', preview: 'Looking at salinity levels in Arctic...' },
          { id: 3, title: 'Deep Ocean Exploration', date: '2024-01-13', preview: 'Exploring abyssal zone characteristics...' },
          { id: 4, title: 'Current Patterns Study', date: '2024-01-12', preview: 'Understanding ocean current patterns...' }
        ]
  );

  // Update local chat history when prop changes
  useEffect(() => {
    if (chatHistory && chatHistory.length > 0) {
      setLocalChatHistory(chatHistory);
    }
  }, [chatHistory]);

  const actionOptions = [

    // {
    //   title: "Analyse Data",
    //   description: "Perform analysis on oceanographic datasets",
    //   icon: "fa-chart-line",
    //   prompt: "I want to analyse oceanographic data",
    // },
    // {
    //   title: "Use Map",
    //   description: "Visualize data on interactive ocean maps",
    //   icon: "fa-map",
    //   prompt: "Show me data on the map",
    // },
  ];

  // --- Chat history helpers ---
  const recentChats = useMemo(() => {
    if (!Array.isArray(chatHistory)) return [];
    // try updatedAt, fall back to lastUpdated if that’s what your data uses
    return [...chatHistory]
      .sort(
        (a, b) =>
          new Date(b.updatedAt || b.lastUpdated || 0) -
          new Date(a.updatedAt || a.lastUpdated || 0)
      )
      .slice(0, 3);
  }, [chatHistory]);

  const getChatTitle = (chat) =>
    chat?.title || chat?.name || "Untitled chat";

  const getChatTime = (chat, withTime = false) => {
  const ts = chat?.updatedAt || chat?.lastUpdated || chat?.date;
  if (!ts) return "";
  const d = new Date(ts);
  return withTime ? d.toLocaleString() : d.toLocaleDateString();
};


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

  const updateLoadingState = async (messageId) => {
    const states = [
      { state: 'thinking', text: 'Thinking...', duration: 1500 },
      { state: 'retrieving', text: 'Retrieving data...', duration: 2000 },
      { state: 'analyzing', text: 'Analyzing...', duration: 1500 }
    ];

    for (const { state, text, duration } of states) {
      // Update to current state
      setMessages(prev => {
        const newMessages = [...prev];
        const messageIndex = newMessages.findIndex(msg => msg.id === messageId);
        if (messageIndex !== -1) {
          newMessages[messageIndex] = {
            ...newMessages[messageIndex],
            loadingState: state,
            loadingText: text
          };
        }
        return newMessages;
      });

      // Wait for the specified duration before moving to next state
      await new Promise(resolve => setTimeout(resolve, duration));
    }
  };

  const handleOptionClick = async (option) => {
    const userMessage = { 
      type: "user", 
      content: option.prompt,
      id: Date.now()
    };
    setMessages(prev => [...prev, userMessage]);

    // Add loading message
    const loadingMessage = {
      type: "bot",
      content: "",
      loadingState: "thinking",
      id: Date.now() + 1,
      isLoading: true
    };
    setMessages(prev => [...prev, loadingMessage]);
    setIsLoading(true);

    // For 'Use Map', we still show fetching message, but open map only after backend returns show_map
    if (option.title === "Use Map") {
      userRequestedMapRef.current = true;
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
    } finally {
      // Enable input and send button
      setIsLoading(false);
    };
  };

  const handleSend = async () => {
    if (inputValue.trim()) {
      // Add user message
      console.log("handle send");
      const userMessage = {
        type: "user",
        content: inputValue,
        id: Date.now()
      };
      setMessages(prev => [...prev, userMessage]);

      // Add loading message
      const loadingMessageId = Date.now() + 1;
      const loadingMessage = {
        type: "bot",
        content: "",
        loadingState: "thinking",
        id: loadingMessageId,
        isLoading: true
      };
      setMessages(prev => [...prev, loadingMessage]);
      setIsLoading(true);

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
        // Run through all loading states
        await updateLoadingState(loadingMessageId);

        // Call FastAPI backend
        const response = await axios.post("http://127.0.0.1:8000", {
          query: query,
        });

        // Update the loading message with the actual response
        setMessages(prev => {
          const newMessages = [...prev];
          const messageIndex = newMessages.findIndex(msg => msg.id === loadingMessageId);
          if (messageIndex !== -1) {
            newMessages[messageIndex] = {
              ...newMessages[messageIndex],
              content: response.data.message,
              chartData: response.data.chart_data || response.data.chartData, // Handle both formats
              tableData: response.data.table_data,
              hasData: response.data.has_data,
              isLoading: false,
              loadingState: null
            };
          }
          return newMessages;
        });

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
        setMessages(prev => {
          const newMessages = [...prev];
          const messageIndex = newMessages.findIndex(msg => msg.id === loadingMessageId);
          if (messageIndex !== -1) {
            newMessages[messageIndex] = {
              ...newMessages[messageIndex],
              content: "⚠️ Sorry, something went wrong connecting to the server.",
              isLoading: false,
              loadingState: null
            };
          }
          return newMessages;
        });
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  const handleQuestionClick = (question) => {
    setInputValue(question);
    // Optional: Auto-focus the input field
    const input = document.querySelector('.chat-input input');
    if (input) input.focus();
  };

  const selectChat = (chatId) => {
    setActiveChat(chatId);
    // Here you would load the selected chat conversation
  };

  const deleteChat = (chatId, e) => {
    e.stopPropagation();
    const updatedHistory = localChatHistory.filter(chat => chat.id !== chatId);
    setLocalChatHistory(updatedHistory);
    
    // If we have an onSelectChat prop, use it to notify parent
    if (onSelectChat) {
      onSelectChat(null);
    }
    
    if (activeChat === chatId) {
      setActiveChat(null);
    }
  };

  const startNewChat = () => {
    setActiveChat(null);
    setMessages([]);
    
    // If we have the toggle prop, use it, otherwise just clear the chat
    if (onToggleChatHistory) {
      onToggleChatHistory();
    }
  };

  return (
    <main className="chat-container" id="chat">
      {/* Top buttons */}
      <div className="top-buttons">
        <button
          className="chat-history-icon-btn"
          onClick={onToggleChatHistory}
          aria-label="View Chat History"
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
          <div
          className="chat-history-overlay" onClick={onToggleChatHistory}></div>
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
              {localChatHistory.map((chat) => (
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
                {message.isLoading ? (
                  <div className="loading-state active">
                    <div className="loading-dot"></div>
                    <span>{message.loadingText || 'Processing...'}</span>
                  </div>
                ) : (
                  <div className="message-content">
                    {message.content}
                  </div>
                )}
              </div>

              {/* Chart renderer, if available */}
              {message.chartData && message.type === "bot" && !message.isLoading && (
                <div className="chart-container" style={{ width: '100%', marginTop: '20px' }}>
                  <ChartRenderer chartData={message.chartData} />
                </div>
              )}
            </React.Fragment>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/*Chat history preview bar at the bottom*/}
      {/* <div className="chat-history-preview">
        <div className="chat-history-items">
          {recentChats.length === 0 ? (
            <span className="chat-history-empty">No recent chats yet</span>
          ) : (
            recentChats.map((chat) => (
              <button
                key={chat.id}
                className="chat-history-item"
                onClick={() => onSelectChat(chat)}
              >
                <span className="chat-history-title">
                  {getChatTitle(chat)}
                </span>
                {getChatTime(chat) && (
                  <span className="chat-history-time">
                    {getChatTime(chat)}
                  </span>
                )}
              </button>
            ))
          )}
        </div>

        <button
          className="chat-history-view-all"
          onClick={() => setShowHistoryBox(true)}
        >
          View all
        </button>
      </div> */}

      {/* <div className="chat-input">
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

      {/* 🔹 Chat history small box */}
      {/* {showHistoryBox && (
        <div
          className="chat-history-modal-backdrop"
          onClick={() => setShowHistoryBox(false)}
        >
          <div
            className="chat-history-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="chat-history-modal-header">
              <span>Chat history</span>
              <button
                className="chat-history-close"
                onClick={() => setShowHistoryBox(false)}
              >
                ✕
              </button>
            </div>

            <div className="chat-history-modal-list">
              {(!localChatHistory || localChatHistory.length === 0) && (
                <div className="chat-history-empty">No chats yet</div>
              )}

              {localChatHistory &&
                localChatHistory.map((chat) => (
                  <button
                    key={chat.id}
                    className="chat-history-modal-item"
                    onClick={() => {
                      onSelectChat(chat);
                      setShowHistoryBox(false);
                    }}
                  >
                    <div className="chat-history-modal-title">
                      {getChatTitle(chat)}
                    </div>
                    {getChatTime(chat, true) && (
                      <div className="chat-history-modal-subtitle">
                        {getChatTime(chat, true)}
                      </div>
                    )}
                  </button>
                ))}
            </div>
          </div>
        </div>
      )} */}

      <QuestionPanel onQuestionClick={handleQuestionClick} />
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
