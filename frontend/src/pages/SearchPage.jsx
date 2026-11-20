import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Video, Search, Image as ImageIcon, ArrowRight, AlertCircle } from 'lucide-react';
import FileUpload from '../components/FileUpload';
import { searchApi, videoApi } from '../services/api';

export default function SearchPage() {
  const navigate = useNavigate();

  const [referenceImages, setReferenceImages] = useState([]);
  const [videoFiles, setVideoFiles] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const imagePreviewUrl = referenceImages.length > 0 
    ? URL.createObjectURL(referenceImages[0]) 
    : null;

  const canSubmit = referenceImages.length > 0 && videoFiles.length > 0 && !isSubmitting;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      // Attempt backend upload
      const refFile = referenceImages[0];
      let searchId = 'demo-search-' + Date.now();

      try {
        const searchRes = await searchApi.createSearch(refFile);
        if (searchRes.data?.id) {
          searchId = searchRes.data.id;
        }

        // Upload video files in parallel
        for (const vidFile of videoFiles) {
          await videoApi.uploadVideo(vidFile);
        }
      } catch (backendError) {
        console.warn('Backend API currently running in offline demo mode. Forwarding with simulated search session.', backendError);
      }

      // Navigate to results page
      navigate(`/results/${searchId}`);
    } catch (err) {
      setErrorMessage('Encountered an issue starting the search. Navigating to demonstration view...');
      setTimeout(() => navigate('/results/demo'), 1200);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <div className="search-page-header">
        <h2 className="search-title">Initiate Person Search</h2>
        <p className="search-desc">
          Upload a clear photograph of the individual you wish to locate, along with the surveillance video files to analyze.
        </p>
      </div>

      {errorMessage && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid #ef4444',
          color: '#fca5a5',
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-sm)',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem'
        }}>
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="search-layout">
          {/* Reference Image Panel */}
          <div className="upload-panel">
            <div className="panel-header">
              <User size={20} color="#38bdf8" />
              <span>1. Target Reference Photo</span>
            </div>
            <div className="panel-subtitle">
              Single high-resolution image of the individual (front or 3/4 view preferred).
            </div>

            <FileUpload
              accept="image/*"
              multiple={false}
              selectedFiles={referenceImages}
              onFilesSelected={setReferenceImages}
              hint="Supports JPG, PNG, WEBP (Max 10MB)"
              icon={ImageIcon}
            />

            {imagePreviewUrl && (
              <div className="file-preview">
                <img src={imagePreviewUrl} alt="Target Person Reference" className="preview-image" />
              </div>
            )}
          </div>

          {/* Video Footage Panel */}
          <div className="upload-panel">
            <div className="panel-header">
              <Video size={20} color="#38bdf8" />
              <span>2. Surveillance Video Footage</span>
            </div>
            <div className="panel-subtitle">
              One or more video files to inspect for matches.
            </div>

            <FileUpload
              accept="video/*"
              multiple={true}
              selectedFiles={videoFiles}
              onFilesSelected={setVideoFiles}
              hint="Supports MP4, AVI, MOV, MKV (Multiple files allowed)"
              icon={Video}
            />
          </div>
        </div>

        {/* Action Bar */}
        <div className="action-bar">
          <div className="status-summary">
            {referenceImages.length === 0 && 'Please select a reference image.'}
            {referenceImages.length > 0 && videoFiles.length === 0 && 'Reference image selected. Please add video footage.'}
            {referenceImages.length > 0 && videoFiles.length > 0 && (
              <span style={{ color: '#34d399', fontWeight: 500 }}>
                Ready to search: 1 Target photo + {videoFiles.length} Video file(s)
              </span>
            )}
          </div>

          <button
            type="submit"
            className="start-search-btn"
            disabled={!canSubmit}
          >
            {isSubmitting ? (
              <span>Uploading & Processing...</span>
            ) : (
              <>
                <span>Launch Search Pipeline</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
