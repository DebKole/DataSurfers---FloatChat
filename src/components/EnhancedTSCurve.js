import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchTsCurveEnhanced } from '../api';
import './EnhancedTSCurve.css';

const EnhancedTSCurve = ({ floatId }) => {
  // 1. All state hooks at the top
  const [imageData, setImageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDebug, setShowDebug] = useState(false);
  const [debugInfo, setDebugInfo] = useState({
    dataLength: 0,
    isValidBase64: false,
    dataPreview: '',
    timestamp: null,
    status: 'idle',
    mimeType: '',
    lastOperation: '',
    error: null,
    lastError: null,
    sourceType: '',
    dataType: ''
  });

  // 2. Helper functions that use hooks
  const updateDebugInfo = useCallback((updates) => {
    setDebugInfo(prev => ({
      ...prev,
      ...(typeof updates === 'function' ? updates(prev) : updates),
      timestamp: new Date().toISOString()
    }));
  }, []);

  const isValidBase64 = useCallback((str) => {
    if (!str) return false;
    try {
      if (str.startsWith('data:')) {
        const parts = str.split(',');
        return parts.length === 2;
      }
      return btoa(atob(str)) === str;
    } catch (e) {
      console.error('Base64 validation error:', e);
      return false;
    }
  }, []);

  const getImageSource = useCallback(async (data) => {
    if (!data) {
      console.error('No image data provided');
      updateDebugInfo(prev => ({
        ...prev,
        status: 'error',
        error: 'No image data provided',
        dataType: 'null/undefined',
        dataLength: 0
      }));
      return '';
    }
    
    try {
      // If it's already a data URL, validate it
      if (typeof data === 'string' && data.startsWith('data:')) {
        console.log('Processing data URL');
        
        // Basic validation of the data URL format
        const parts = data.split(',');
        if (parts.length < 2) {
          throw new Error('Invalid data URL format: missing comma separator');
        }
        
        const [header, base64Data] = parts;
        const mimeType = header.match(/^data:(.*?);/)?.[1] || 'image/png';
        
        // Validate the base64 data
        const cleanBase64 = base64Data.replace(/\s/g, '');
        
        // Check if the base64 data is properly padded
        if (cleanBase64.length % 4 > 0) {
          throw new Error('Invalid base64: incorrect padding');
        }
        
        // Test if it's valid base64
        try {
          atob(cleanBase64);
        } catch (e) {
          throw new Error(`Invalid base64 data: ${e.message}`);
        }
        
        // Reconstruct the data URL with proper formatting
        const fixedDataUrl = `data:${mimeType};base64,${cleanBase64}`;
        
        updateDebugInfo(prev => ({
          ...prev,
          status: 'success',
          mimeType,
          dataLength: cleanBase64.length,
          dataPreview: cleanBase64.substring(0, 30) + '...',
          lastOperation: 'Processed data URL'
        }));
        
        console.log('Successfully processed data URL');
        return fixedDataUrl;
      }
      
      // If it's not a data URL, try to convert it
      console.log('Converting raw data to data URL');
      
      let base64;
      if (data instanceof ArrayBuffer || ArrayBuffer.isView(data)) {
        // Handle ArrayBuffer or TypedArray
        const bytes = new Uint8Array(data);
        base64 = btoa(String.fromCharCode(...bytes));
      } else if (typeof data === 'string') {
        // Handle base64 string
        base64 = data;
      } else {
        throw new Error(`Unsupported data type: ${typeof data}`);
      }
      
      // Clean and validate the base64 data
      const cleanBase64 = base64.replace(/\s/g, '').replace(/[^A-Za-z0-9+/=]/g, '');
      
      // Ensure proper padding
      const paddedBase64 = cleanBase64.padEnd(
        cleanBase64.length + (4 - (cleanBase64.length % 4)) % 4, '='
      );
      
      // Test if it's valid base64
      atob(paddedBase64);
      
      const dataUrl = `data:image/png;base64,${paddedBase64}`;
      
      updateDebugInfo(prev => ({
        ...prev,
        status: 'success',
        mimeType: 'image/png',
        dataLength: paddedBase64.length,
        dataPreview: paddedBase64.substring(0, 30) + '...',
        lastOperation: 'Converted raw data to data URL'
      }));
      
      console.log('Successfully converted data to data URL');
      return dataUrl;
      
    } catch (error) {
      console.error('Error processing image data:', {
        error: error.message,
        dataType: typeof data,
        dataLength: data?.length,
        dataPreview: typeof data === 'string' ? data.substring(0, 100) : 'Not a string'
      });
      
      updateDebugInfo(prev => ({
        ...prev,
        status: 'error',
        error: error.message,
        dataType: typeof data,
        dataLength: data?.length || 0,
        dataPreview: typeof data === 'string' ? data.substring(0, 50) + '...' : 'Not a string',
        lastOperation: 'Error processing image data'
      }));
      
      throw error; // Re-throw to be caught by the error boundary
    }
  }, [updateDebugInfo]);

  // 3. State for tracking image source and loading state
  const [imageSource, setImageSource] = useState('');
  const [imageError, setImageError] = useState(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  // Update image source when imageData changes
  useEffect(() => {
    let isMounted = true;
    
    const updateSource = async () => {
      if (!imageData) {
        if (isMounted) {
          setImageSource('');
          setImageError('No image data available');
        }
        return;
      }
      
      try {
        console.log('Processing image data...');
        const source = await getImageSource(imageData);
        
        if (!source) {
          throw new Error('No valid image source could be generated from the data');
        }
        
        console.log('Image source prepared, testing load...');
        
        // Test the image source by creating an image element
        const testImg = new Image();
        
        // Set a timeout to handle cases where the image doesn't load
        const loadTimeout = setTimeout(() => {
          if (isMounted && !testImg.complete) {
            console.error('Image load timed out');
            setImageError('Image load timed out');
            setImageSource('');
          }
        }, 5000); // 5 second timeout
        
        testImg.onload = () => {
          clearTimeout(loadTimeout);
          
          if (!isMounted) return;
          
          console.log('Image loaded successfully', { 
            width: testImg.width, 
            height: testImg.height,
            sourceType: typeof source,
            sourceLength: source.length,
            complete: testImg.complete,
            naturalWidth: testImg.naturalWidth,
            naturalHeight: testImg.naturalHeight
          });
          
          // Only update state if the component is still mounted
          if (isMounted) {
            setImageDimensions({
              width: testImg.naturalWidth || testImg.width,
              height: testImg.naturalHeight || testImg.height
            });
            setImageSource(source);
            setImageError(null);
          }
        };
        
        testImg.onerror = (e) => {
          clearTimeout(loadTimeout);
          
          const errorDetails = {
            event: e,
            sourceType: typeof source,
            sourceLength: source?.length || 0,
            sourcePreview: source ? source.substring(0, 100) : 'No source',
            timestamp: new Date().toISOString(),
            errorMessage: e.message || 'Unknown image error',
            targetError: e.target?.error ? {
              code: e.target.error.code,
              message: e.target.error.message,
              name: e.target.error.name
            } : null
          };
          
          console.error('Image load error:', errorDetails);
          
          // Try to get more detailed error information
          const errorMessage = e.nativeEvent?.message || 
                             (e.target?.error ? `Image error: ${e.target.error.message}` : 'Unknown image error');
          
          if (isMounted) {
            setImageError(`Failed to load image: ${errorMessage}`);
            setImageSource('');
            
            updateDebugInfo(prev => ({
              ...prev,
              error: `Image load failed: ${errorMessage}`,
              status: 'error',
              lastError: errorDetails,
              lastOperation: 'Image load error'
            }));
          }
        };
        
        // Set the source last to ensure event handlers are in place
        testImg.src = source;
        
      } catch (error) {
        console.error('Error processing image data:', {
          error,
          imageDataType: typeof imageData,
          imageDataLength: typeof imageData === 'string' ? imageData.length : 'N/A'
        });
        
        if (isMounted) {
          setImageError(`Failed to process image data: ${error.message}`);
          setImageSource('');
        }
      }
    };
    
    updateSource();
    
    // Cleanup function
    return () => {
      isMounted = false;
    };
  }, [imageData, getImageSource]);


  // 4. Effects
  useEffect(() => {
    const loadData = async () => {
      if (!floatId) return;
      
      setLoading(true);
      setError(null);
      updateDebugInfo({ status: 'fetching' });
      
      try {
        console.log(`[TS Curve] Fetching data for float ${floatId}...`);
        const imageData = await fetchTsCurveEnhanced(floatId);
        
        if (!imageData) {
          throw new Error('No image data received from server');
        }
        
        setImageData(imageData);
        updateDebugInfo(prev => ({
          ...prev,
          dataLength: imageData.length,
          isValidBase64: isValidBase64(imageData),
          dataPreview: imageData.substring(0, 50) + (imageData.length > 50 ? '...' : ''),
          status: 'success'
        }));
      } catch (err) {
        console.error('Error loading TS curve:', err);
        setError('Failed to load temperature-salinity curve');
        updateDebugInfo(prev => ({
          ...prev,
          error: err.message,
          status: 'error'
        }));
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [floatId, isValidBase64, updateDebugInfo]);

  // 5. Event handlers
  const handleDownload = useCallback(async () => {
    if (!imageSource) {
      setError('No image data available for download');
      return;
    }
    
    try {
      // If it's already a data URL, use it directly
      if (imageSource.startsWith('data:')) {
        const link = document.createElement('a');
        link.href = imageSource;
        link.download = `ts_curve_${floatId || 'unknown'}_${new Date().toISOString().split('T')[0]}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        return;
      }

      // Fallback for non-data URL format (shouldn't happen with current implementation)
      const response = await fetch(imageSource);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `ts_curve_${floatId || 'unknown'}_${new Date().toISOString().split('T')[0]}.png`;
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(blobUrl);
      }, 100);
      
    } catch (error) {
      console.error('Error downloading the graph:', error);
      setError('Failed to download the graph: ' + (error.message || 'Unsupported file format'));
      updateDebugInfo(prev => ({
        ...prev,
        error: `Download failed: ${error.message || 'Unsupported file format'}`,
        status: 'error',
        lastError: {
          message: error.message,
          timestamp: new Date().toISOString()
        }
      }));
    }
  }, [imageSource, floatId, updateDebugInfo]);

  const toggleDebug = useCallback(() => {
    setShowDebug(prev => !prev);
  }, []);


  // 6. Conditional rendering
  if (loading) {
    return (
      <div className="ts-curve-container">
        <div className="loading">
          {debugInfo.status === 'retrying' ? 'Retrying...' : 'Loading temperature-salinity curve...'}
        </div>
        {floatId && <div className="float-id">Float ID: {floatId}</div>}
      </div>
    );
  }

  if (error || !imageData) {
    return (
      <div className="ts-curve-container error">
        <div className="error-message">{error || 'No temperature-salinity data available'}</div>
        {floatId && <div className="float-id">Float ID: {floatId}</div>}
        <button className="retry-button" onClick={() => window.location.reload()}>
          Retry
        </button>
      </div>
    );
  }


  return (
    <div className="ts-curve-container">
      <div className="ts-curve-header">
        <h3>Temperature-Salinity Diagram</h3>
        <div className="ts-curve-actions">
          <button 
            className="download-button"
            onClick={handleDownload}
            disabled={!imageSource}
            title="Download TS Curve"
          >
            ↓ Download
          </button>
          <button 
            className="debug-toggle" 
            onClick={toggleDebug}
            aria-label={showDebug ? 'Hide debug info' : 'Show debug info'}
          >
            {showDebug ? '▲' : '▼'} Debug
          </button>
        </div>
      </div>
      
      <div className="ts-curve-image" style={{
        width: '100%',
        minHeight: '500px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        overflow: 'auto',
        margin: '20px 0',
        position: 'relative',
        padding: '20px',
        boxSizing: 'border-box'
      }}>
        {imageError ? (
          <div style={{ 
            color: 'red', 
            padding: '20px',
            textAlign: 'center',
            backgroundColor: 'rgba(255, 200, 200, 0.2)',
            borderRadius: '4px',
            border: '1px solid #ffcccc'
          }}>
            <p>Error loading image: {imageError}</p>
            <p>Image data preview: {imageData ? 
              `${imageData.substring(0, 50)}...` : 'No image data'}</p>
          </div>
        ) : imageSource ? (
          <div style={{ 
            width: '100%',
            height: '100%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            overflow: 'auto'
          }}>
            <img 
              key={`img-${Date.now()}`}
              src={imageSource}
              alt="Temperature-Salinity Diagram"
              style={{
                maxWidth: '100%',
                maxHeight: '80vh',
                objectFit: 'contain',
                display: 'block',
                margin: '0 auto',
                padding: '10px',
                boxSizing: 'border-box',
                border: '1px solid #eee',
                backgroundColor: 'white',
                minWidth: Math.min(800, window.innerWidth - 40) + 'px',
                minHeight: '400px'
              }}
              onError={(e) => {
                const errorDetails = {
                  event: e,
                  sourceType: typeof imageSource,
                  sourceLength: imageSource?.length,
                  sourcePreview: imageSource?.substring(0, 100) + '...',
                  timestamp: new Date().toISOString()
                };
                
                console.error('Error loading image:', errorDetails);
                
                // Don't try to fix the image source here as it's already been processed
                // Just update the error state and debug info
                const errorMsg = 'Failed to display image. The image data may be corrupted or in an unsupported format.';
                
                if (imageError !== errorMsg) {
                  setImageError(errorMsg);
                }
                
                updateDebugInfo(prev => ({
                  ...prev,
                  error: `Image render error: ${e.message || 'Unknown error'}`,
                  status: 'error',
                  lastError: {
                    ...errorDetails,
                    message: e.message || 'Image load failed',
                    type: e.type || 'render_error'
                  }
                }));
              }}
              onLoad={(e) => {
                const img = e.target;
                console.log('Image loaded successfully', {
                  naturalWidth: img.naturalWidth,
                  naturalHeight: img.naturalHeight,
                  width: img.width,
                  height: img.height,
                  complete: img.complete
                });
                
                // Update dimensions for container
                setImageDimensions({
                  width: img.naturalWidth,
                  height: img.naturalHeight
                });
                
                updateDebugInfo(prev => ({
                  ...prev,
                  renderedDimensions: {
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    displayWidth: img.width,
                    displayHeight: img.height,
                    complete: img.complete
                  },
                  status: 'loaded',
                  lastLoaded: new Date().toISOString()
                }));
              }}
            />
          </div>
        ) : (
          <div style={{
            textAlign: 'center',
            color: '#666',
            padding: '20px',
            fontStyle: 'italic',
            width: '100%'
          }}>
            {loading ? 'Loading temperature-salinity diagram...' : 'No image data available'}
          </div>
        )}
        
        {error && (
          <div style={{
            position: 'absolute',
            bottom: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'rgba(255, 0, 0, 0.8)',
            color: 'white',
            padding: '5px 10px',
            borderRadius: '4px',
            fontSize: '14px',
            zIndex: 10
          }}>
            {error}
          </div>
        )}
      </div>
      
      {showDebug && (
        <div className="debug-info">
          <h4>Debug Information</h4>
          <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default EnhancedTSCurve;
