import { useState } from 'react';
import UploadScreen from './components/UploadScreen';
import Dashboard from './components/Dashboard';
import './index.css';

function App() {
  const [screen, setScreen] = useState('upload');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleDataLoaded = (responseData) => {
    setData(responseData);
    setScreen('dashboard');
    setError(null);
  };

  const handleReset = () => {
    setScreen('upload');
    setData(null);
    setError(null);
  };

  return (
    <>
      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
        </div>
      )}

      {error && (
        <div className="error-toast" onClick={() => setError(null)}>
          ⚠️ {error}
        </div>
      )}

      {screen === 'upload' && (
        <UploadScreen
          onDataLoaded={handleDataLoaded}
          setLoading={setLoading}
          setError={setError}
        />
      )}

      {screen === 'dashboard' && data && (
        <Dashboard
          analytics={data.analytics}
          recommendations={data.recommendations}
          onReset={handleReset}
        />
      )}
    </>
  );
}

export default App;
