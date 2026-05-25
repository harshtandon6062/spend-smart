import { useState, useRef } from 'react';
import { LuCloudUpload, LuFileSpreadsheet, LuSparkles } from 'react-icons/lu';
import { uploadCSV, loadSample } from '../services/api';

export default function UploadScreen({ onDataLoaded, setLoading, setError }) {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'pdf'].includes(ext)) {
      setError('Please upload a .csv or .pdf file');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await uploadCSV(file);
      onDataLoaded(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process file');
    } finally {
      setLoading(false);
    }
  };

  const handleSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await loadSample();
      onDataLoaded(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load sample data');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const onDragLeave = () => setDragOver(false);

  return (
    <div className="hero-screen">
      <div className="hero-content">
        <h1>💰 SpendSmart</h1>
        <p className="tagline">
          Upload your transactions and get personalized savings suggestions
          powered by intelligent pattern analysis.
        </p>

        <div
          className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="upload-icon">
            <LuCloudUpload size={48} />
          </div>
          <p className="upload-text">
            Drag & drop your file here, or click to browse
          </p>
          <p className="upload-hint">
            Supports: CSV (Date, Merchant, Amount, Category) or PhonePe/UPI statement PDF
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.pdf"
            style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
        </div>

        <div className="hero-actions">
          <button className="btn-ghost" onClick={handleSample}>
            <LuFileSpreadsheet />
            Try with Sample Data
          </button>
        </div>
      </div>
    </div>
  );
}
