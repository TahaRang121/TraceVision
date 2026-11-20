import React, { useRef, useState } from 'react';
import { UploadCloud, File, X, CheckCircle } from 'lucide-react';

export default function FileUpload({
  accept,
  multiple = false,
  onFilesSelected,
  selectedFiles = [],
  hint = "Drag & drop files here, or click to browse",
  icon: Icon = UploadCloud,
}) {
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const fileList = Array.from(e.dataTransfer.files);
      onFilesSelected(multiple ? [...selectedFiles, ...fileList] : [fileList[0]]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const fileList = Array.from(e.target.files);
      onFilesSelected(multiple ? [...selectedFiles, ...fileList] : [fileList[0]]);
    }
  };

  const handleRemove = (index, e) => {
    e.stopPropagation();
    const updated = selectedFiles.filter((_, i) => i !== index);
    onFilesSelected(updated);
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div>
      <div
        className={`dropzone ${isDragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        <div className="dropzone-icon">
          <Icon size={36} />
        </div>
        <div className="dropzone-text">
          {multiple ? 'Choose video files or drop them here' : 'Choose reference image or drop it here'}
        </div>
        <div className="dropzone-hint">{hint}</div>
      </div>

      {selectedFiles.length > 0 && (
        <div className="file-list">
          {selectedFiles.map((file, idx) => (
            <div key={`${file.name}-${idx}`} className="file-item">
              <div className="file-info">
                <File size={16} className="file-icon" />
                <span className="file-name">{file.name}</span>
                <span className="file-size">({formatFileSize(file.size)})</span>
              </div>
              <button
                type="button"
                className="remove-btn"
                onClick={(e) => handleRemove(idx, e)}
                title="Remove file"
              >
                <X size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
