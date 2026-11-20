import React from 'react';
import { Video, Clock, Crosshair, UserCheck, Play } from 'lucide-react';

export default function SearchResultCard({ result }) {
  const {
    rank,
    similarity_score,
    matched_timestamp,
    matched_frame,
    bbox_x1,
    bbox_y1,
    bbox_x2,
    bbox_y2,
    video,
    detected_person,
  } = result;

  const scorePercentage = (similarity_score * 100).toFixed(1);
  const formattedTime = matched_timestamp ? `${matched_timestamp.toFixed(1)}s` : 'N/A';

  return (
    <div className="result-card">
      <div className="card-thumbnail">
        <span className="card-badge-rank">Rank #{rank}</span>
        <span className="card-badge-score">{scorePercentage}% Match</span>
        
        {/* Visual bounding box representation */}
        <div style={{
          width: '75px',
          height: '110px',
          border: '2px solid #10b981',
          borderRadius: '4px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          position: 'relative'
        }}>
          <UserCheck size={28} color="#10b981" />
          <span style={{ fontSize: '10px', color: '#10b981', marginTop: '4px', fontWeight: 600 }}>
            Track ID #{detected_person?.track_id || '1'}
          </span>
        </div>
      </div>

      <div className="card-body">
        <div className="card-title">
          <span>{video?.original_filename || 'Video Segment'}</span>
          <Video size={16} color="#94a3b8" />
        </div>

        <div className="card-details">
          <div className="detail-row">
            <span>Timestamp:</span>
            <strong>{formattedTime} (Frame #{matched_frame})</strong>
          </div>
          <div className="detail-row">
            <span>Track Duration:</span>
            <span>
              {detected_person?.first_timestamp?.toFixed(1) || 0}s – {detected_person?.last_timestamp?.toFixed(1) || 0}s
            </span>
          </div>
          <div className="detail-row">
            <span>Detection Confidence:</span>
            <span>{((detected_person?.avg_confidence || 0.9) * 100).toFixed(0)}%</span>
          </div>
          <div className="detail-row">
            <span>Bounding Box:</span>
            <span>[{bbox_x1 || 0}, {bbox_y1 || 0}, {bbox_x2 || 0}, {bbox_y2 || 0}]</span>
          </div>
        </div>
      </div>

      <div className="card-footer">
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#64748b' }}>
          <Clock size={14} /> At {formattedTime}
        </span>
        <button 
          type="button" 
          style={{ 
            color: '#38bdf8', 
            fontWeight: 600, 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.25rem',
            fontSize: '0.825rem' 
          }}
          onClick={() => alert(`Play preview at ${formattedTime} for video: ${video?.original_filename}`)}
        >
          <Play size={14} /> View Frame
        </button>
      </div>
    </div>
  );
}
