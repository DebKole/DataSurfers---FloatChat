import React, { useState } from 'react';
import './Sidebar.css';

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    { id: 1, title: 'Ocean Temperature Analysis', date: '2024-01-15', preview: 'Analyzing temperature trends in Pacific...' },
    { id: 2, title: 'Salinity Data Query', date: '2024-01-14', preview: 'Looking at salinity levels in Arctic...' },
    { id: 3, title: 'Deep Ocean Exploration', date: '2024-01-13', preview: 'Exploring abyssal zone characteristics...' },
    { id: 4, title: 'Current Patterns Study', date: '2024-01-12', preview: 'Understanding ocean current patterns...' }
  ]);
  const [activeChat, setActiveChat] = useState(null);

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
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
    // Here you would clear the current chat and start fresh
  };

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`} id="leftSidebar" aria-label="Chat and Filters sidebar">
      <button className="collapse-btn left-toggle" onClick={toggleSidebar} aria-expanded={!collapsed} title="Collapse sidebar">
        <i className={`fas ${collapsed ? 'fa-chevron-right' : 'fa-chevron-left'}`} aria-hidden="true"></i>
      </button>

      {/* Chat History Section */}
      <div className="chat-history-section">
        <div className="section-header">
          <i className="fas fa-comments" aria-hidden="true"></i>
          <h2>Chat History</h2>
        </div>
        
        <button className="new-chat-btn" onClick={startNewChat}>
          <i className="fas fa-plus"></i>
          <span>New Chat</span>
        </button>

        <div className="chat-history-list">
          {chatHistory.map(chat => (
            <div 
              key={chat.id} 
              className={`chat-history-item ${activeChat === chat.id ? 'active' : ''}`}
              onClick={() => selectChat(chat.id)}
            >
              <div className="chat-info">
                <div className="chat-title">{chat.title}</div>
                <div className="chat-preview">{chat.preview}</div>
                <div className="chat-date">{chat.date}</div>
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

      {/* Data Filters Section */}
      <div className="filters-section">
        <div className="section-header">
          <i className="fas fa-filter" aria-hidden="true"></i>
          <h2>Data Filters</h2>
        </div>
        
        <div className="filters-content">
          <div className="filter-group">
        <h3>
          <i className="fas fa-water"></i>
          Ocean Region
        </h3>
        <div className="filter-options">
          <div className="option">
            <label htmlFor="ocean-basin">Basin</label>
            <select id="ocean-basin">
              <option>Global</option>
              <option>Pacific Ocean</option>
              <option>Atlantic Ocean</option>
              <option>Indian Ocean</option>
              <option>Southern Ocean</option>
              <option>Arctic Ocean</option>
            </select>
          </div>
          <div className="option">
            <label htmlFor="depth-range">Depth Range (m)</label>
            <select id="depth-range">
              <option>All Depths</option>
              <option>Surface (0-100m)</option>
              <option>Thermocline (100-700m)</option>
              <option>Deep Ocean (700-2000m)</option>
              <option>Abyssal (&gt;2000m)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="filter-group">
        <h3>
          <i className="fas fa-ruler"></i>
          Parameters
        </h3>
        <div className="filter-options">
          <div className="option">
            <label htmlFor="temperature">Temperature Range (°C)</label>
            <select id="temperature">
              <option>Any</option>
              <option>Polar (-2 to 5°C)</option>
              <option>Temperate (5 to 20°C)</option>
              <option>Tropical (20 to 30°C)</option>
            </select>
          </div>
          <div className="option">
            <label htmlFor="salinity">Salinity (PSU)</label>
            <select id="salinity">
              <option>Any</option>
              <option>Low (&lt;33)</option>
              <option>Medium (33-36)</option>
              <option>High (&gt;36)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="filter-group">
        <h3>
          <i className="fas fa-calendar"></i>
          Time Frame
        </h3>
        <div className="filter-options">
          <div className="option">
            <label htmlFor="time-range">Date Range</label>
            <select id="time-range">
              <option>Last 7 days</option>
              <option>Last 30 days</option>
              <option>Last 3 months</option>
              <option>Last year</option>
              <option>All time</option>
            </select>
          </div>
        </div>
      </div>

        </div>
        
        <button className="apply-btn">Apply Filters</button>
      </div>
    </aside>
  );
};

export default Sidebar;