import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error("Dashboard Crash Caught:", error, errorInfo);
    
    fetch('/api/errors/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        error: error.toString(),
        stack: error.stack,
        info: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent
      })
    }).catch(err => console.warn("Failed to report crash:", err));
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ 
          height: '100vh', width: '100vw', background: '#09090b', color: '#ff4d4d',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          padding: '40px', textAlign: 'center', fontFamily: 'system-ui, sans-serif'
        }}>
          <h1 style={{ fontSize: '3rem', marginBottom: '10px' }}>⚠️ DASHBOARD CRASH</h1>
          <p style={{ color: '#aaa', maxWidth: '600px', marginBottom: '30px' }}>
            A critical error was caught by the multi-agent guardian system. 
            Telemetry has been sent to the GCS error logs for investigation.
          </p>
          <div style={{ 
            background: 'rgba(255,77,77,0.05)', border: '1px solid rgba(255,77,77,0.2)',
            padding: '20px', borderRadius: '12px', textAlign: 'left', maxWidth: '800px', 
            overflow: 'auto', maxHeight: '300px', fontSize: '13px', color: '#ff8888', fontFamily: 'monospace'
          }}>
            {this.state.error && this.state.error.toString()}
          </div>
          <button 
            onClick={() => window.location.reload()}
            style={{ 
              marginTop: '40px', padding: '15px 40px', background: '#ff4d4d', color: 'white',
              border: 'none', borderRadius: '12px', fontWeight: 'bold', cursor: 'pointer',
              boxShadow: '0 10px 20px rgba(255,77,77,0.3)'
            }}
          >
            RESTORE DASHBOARD
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
