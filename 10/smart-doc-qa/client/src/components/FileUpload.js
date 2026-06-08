import React, { useState, useRef, useCallback } from 'react';

function FileUpload({ apiBase, onUploadComplete, onError }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleFileSelect = useCallback((selectedFile) => {
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    } else {
      onError?.('Please select a valid PDF file');
    }
  }, [onError]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    handleFileSelect(droppedFile);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file) return;

    setUploading(true);
    setProgress(30);

    const formData = new FormData();
    formData.append('pdf', file);

    try {
      // Use XMLHttpRequest for progress tracking
      const xhr = new XMLHttpRequest();

      const result = await new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 70) + 30;
            setProgress(Math.min(pct, 95));
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            try {
              reject(new Error(JSON.parse(xhr.responseText).error));
            } catch {
              reject(new Error(`Upload failed (${xhr.status})`));
            }
          }
        });

        xhr.addEventListener('error', () => reject(new Error('Network error')));
        xhr.open('POST', `${apiBase}/upload`);
        xhr.send(formData);
      });

      setProgress(100);
      setTimeout(() => setProgress(0), 500);

      onUploadComplete?.(result.document);
      setFile(null);
    } catch (err) {
      onError?.(err.message);
      setProgress(0);
    } finally {
      setUploading(false);
    }
  }, [file, apiBase, onUploadComplete, onError]);

  return (
    <div className="upload-card">
      <h3>📤 Upload PDF</h3>

      <div
        className={`dropzone ${dragOver ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => !uploading && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={(e) => handleFileSelect(e.target.files[0])}
        />

        {file ? (
          <>
            <span style={{ fontSize: '2rem' }}>📄</span>
            <p className="file-name">{file.name}</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
              {(file.size / 1024 / 1024).toFixed(1)} MB
            </p>
          </>
        ) : (
          <>
            <span style={{ fontSize: '2rem' }}>📁</span>
            <p>Drop your PDF here or click to browse</p>
          </>
        )}
      </div>

      {file && !uploading && (
        <button className="upload-btn" onClick={handleUpload}>
          ⬆ Upload & Parse
        </button>
      )}

      {uploading && (
        <button className="upload-btn loading" disabled>
          ⏳ Uploading...
        </button>
      )}

      {progress > 0 && (
        <div className="progress-bar-container">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}

export default FileUpload;
