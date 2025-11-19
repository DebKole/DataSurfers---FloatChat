import React from 'react';
import './FAQ.css';

const FAQ = ({ isOpen, onClose }) => {
  const faqData = [
    {
      question: "What types of oceanographic data can I access through FloatChat?",
      answer: "FloatChat provides access to comprehensive oceanographic data from ARGO floats worldwide, including temperature, salinity, and BGC (Biogeochemical) parameters. The system processes NetCDF files and converts them into structured formats for easy querying and visualization."
    },
    {
      question: "How does the AI-powered conversational interface work?",
      answer: "Our system uses Retrieval-Augmented Generation (RAG) pipelines powered by multimodal LLMs to interpret natural language queries. It maps your questions to database queries (SQL) and provides meaningful responses through a chatbot-style interface using Model Context Protocol (MCP)."
    },
    {
      question: "What visualization features are available?",
      answer: "You can visualize data through interactive dashboards including mapped trajectories of ARGO floats, depth-time plots, profile comparisons, and geospatial visualizations using tools like Leaflet, Plotly, or Cesium. The system also provides tabular summaries and export capabilities to ASCII and NetCDF formats."
    },
    {
      question: "Can I query specific regions or time periods?",
      answer: "Yes! You can ask questions like 'Show me salinity profiles near the equator in March 2023' or 'Compare BGC parameters in the Arabian Sea for the last 6 months.' The system supports spatial and temporal filtering for precise data exploration using natural language."
    },
    {
      question: "What makes FloatChat different from traditional ocean data tools?",
      answer: "FloatChat bridges the gap between domain experts and raw data by allowing non-technical users to extract meaningful insights effortlessly. It combines AI-powered natural language processing with comprehensive data visualization, eliminating the need for technical expertise in data formats and complex analysis tools."
    }
  ];

  if (!isOpen) return null;

  return (
    <div className="faq-modal-overlay" onClick={onClose}>
      <div className="faq-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="faq-header">
          <h2>Frequently Asked Questions</h2>
          <button className="faq-close-btn" onClick={onClose}>
            &times;
          </button>
        </div>
        <div className="faq-list">
          {faqData.map((item, index) => (
            <div key={index} className="faq-item">
              <div className="faq-question">
                {item.question}
              </div>
              <div className="faq-answer">
                {item.answer}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FAQ;