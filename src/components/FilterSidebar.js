import React, { useState, useEffect } from "react";
import "./FilterSidebar.css";

const FilterSidebar = ({ onFilterChange, isOpen, onToggle }) => {
  const [filters, setFilters] = useState({
    status: [],
    yearOfDeployment: [],
    country: [],
    basin: [],
    telecom: [],
    dataMode: [],
    startDate: "",
    endDate: ""
  });

  const [availableFilters, setAvailableFilters] = useState({
    status: [],
    yearOfDeployment: [],
    country: [],
    basin: [],
    telecom: [],
    dataMode: []
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/metadata/filters");
      if (res.ok) {
        const data = await res.json();
        setAvailableFilters(data);
      }
    } catch (e) {
      console.error("Failed to fetch filter options:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterToggle = (category, value) => {
    setFilters(prev => {
      const current = prev[category];
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      
      const newFilters = { ...prev, [category]: updated };
      onFilterChange(newFilters);
      return newFilters;
    });
  };

  const handleDateChange = (type, value) => {
    setFilters(prev => {
      const newFilters = { ...prev, [type]: value };
      onFilterChange(newFilters);
      return newFilters;
    });
  };

  const clearFilters = () => {
    const emptyFilters = {
      status: [],
      yearOfDeployment: [],
      country: [],
      basin: [],
      telecom: [],
      dataMode: [],
      startDate: "",
      endDate: ""
    };
    setFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };

  const hasActiveFilters = Object.values(filters).some(val => 
    Array.isArray(val) ? val.length > 0 : val !== ""
  );

  const FilterSection = ({ title, category, options }) => (
    <div className="filter-section">
      <div className="filter-section-title">{title}</div>
      <div className="filter-options">
        {options.map(({ value, count }) => (
          <label key={value} className="filter-option">
            <input
              type="checkbox"
              checked={filters[category].includes(value)}
              onChange={() => handleFilterToggle(category, value)}
            />
            <span className="filter-label">
              {value}
              <span className="filter-count">{count}</span>
            </span>
          </label>
        ))}
      </div>
    </div>
  );

  return (
    <>
      <button className="filter-toggle-btn" onClick={onToggle}>
        <span className="filter-icon">⚙️</span>
        Filters
        {hasActiveFilters && <span className="filter-badge">{Object.values(filters).flat().length}</span>}
      </button>

      <div className={`filter-sidebar ${isOpen ? 'open' : ''}`}>
        <div className="filter-header">
          <h3>Filters</h3>
          <button className="close-btn" onClick={onToggle}>✕</button>
        </div>

        {hasActiveFilters && (
          <button className="clear-filters-btn" onClick={clearFilters}>
            Clear All Filters
          </button>
        )}

        {loading ? (
          <div className="filter-loading">Loading filters...</div>
        ) : (
          <div className="filter-content">
            <div className="filter-section">
              <div className="filter-section-title">Date Range</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px', display: 'block' }}>
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={filters.startDate}
                    onChange={(e) => handleDateChange('startDate', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(15, 26, 46, 0.5)',
                      border: '1px solid rgba(49, 130, 206, 0.3)',
                      borderRadius: '6px',
                      color: '#e2e8f0',
                      fontSize: '14px'
                    }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px', display: 'block' }}>
                    End Date
                  </label>
                  <input
                    type="date"
                    value={filters.endDate}
                    onChange={(e) => handleDateChange('endDate', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      background: 'rgba(15, 26, 46, 0.5)',
                      border: '1px solid rgba(49, 130, 206, 0.3)',
                      borderRadius: '6px',
                      color: '#e2e8f0',
                      fontSize: '14px'
                    }}
                  />
                </div>
              </div>
            </div>

            <FilterSection
              title="Year of Deployment"
              category="yearOfDeployment"
              options={availableFilters.yearOfDeployment}
            />
            <FilterSection
              title="Basin"
              category="basin"
              options={availableFilters.basin}
            />
            <FilterSection
              title="Data Mode"
              category="dataMode"
              options={availableFilters.dataMode}
            />
          </div>
        )}
      </div>

      {isOpen && <div className="filter-overlay" onClick={onToggle} />}
    </>
  );
};

export default FilterSidebar;
