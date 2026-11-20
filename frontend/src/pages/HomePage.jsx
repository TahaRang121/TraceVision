import React from 'react';
import { Link } from 'react-router-dom';
import { Search, UserCheck, Video, Database, Zap, Shield, ArrowRight } from 'lucide-react';

export default function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-pill">
          <span>AI-Powered Video Analytics</span>
        </div>
        <h1 className="hero-title">
          Person Search Across Video Footage
        </h1>
        <p className="hero-subtitle">
          TraceVision enables instantaneous search for specific individuals across multi-camera 
          surveillance footage using state-of-the-art detection, multi-target tracking, and deep re-identification.
        </p>
        <Link to="/search" className="cta-button">
          <span>Start Person Search</span>
          <ArrowRight size={18} />
        </Link>
      </section>

      {/* Feature Cards Grid */}
      <section className="features-grid">
        <div className="feature-card">
          <div className="feature-icon-wrapper">
            <UserCheck size={24} />
          </div>
          <h3 className="feature-title">Target Photo Upload</h3>
          <p className="feature-desc">
            Provide a single reference photo of a person. TraceVision extracts deep appearance embeddings invariant to angle and clothing changes.
          </p>
        </div>

        <div className="feature-card">
          <div className="feature-icon-wrapper">
            <Video size={24} />
          </div>
          <h3 className="feature-title">Multi-Video Ingestion</h3>
          <p className="feature-desc">
            Upload multiple surveillance videos or camera feeds. Frames are efficiently decoded, processed, and tracked in parallel.
          </p>
        </div>

        <div className="feature-card">
          <div className="feature-icon-wrapper">
            <Zap size={24} />
          </div>
          <h3 className="feature-title">YOLOX + ByteTrack</h3>
          <p className="feature-desc">
            Lightweight YOLOX-Nano detects every person in real-time, while ByteTrack assigns persistent trajectory track IDs across occlusions.
          </p>
        </div>

        <div className="feature-card">
          <div className="feature-icon-wrapper">
            <Database size={24} />
          </div>
          <h3 className="feature-title">Qdrant Vector Retrieval</h3>
          <p className="feature-desc">
            512-dimensional OSNet embeddings are indexed in Qdrant for sub-second cosine similarity search across millions of frames.
          </p>
        </div>
      </section>

      {/* Tech Stack Badges */}
      <section className="tech-stack-section">
        <div className="tech-stack-title">Engineered with Modern Computer Vision & Systems Stack</div>
        <div className="tech-badges-container">
          <span className="tech-badge">React.js</span>
          <span className="tech-badge">FastAPI</span>
          <span className="tech-badge">YOLOX-Nano</span>
          <span className="tech-badge">ByteTrack</span>
          <span className="tech-badge">OSNet ReID</span>
          <span className="tech-badge">Qdrant Vector DB</span>
          <span className="tech-badge">PostgreSQL</span>
          <span className="tech-badge">OpenCV</span>
          <span className="tech-badge">PyTorch</span>
        </div>
      </section>
    </div>
  );
}
