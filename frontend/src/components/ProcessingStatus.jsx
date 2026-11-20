import React from 'react';
import { Loader2, CheckCircle, AlertCircle, Clock } from 'lucide-react';

export default function ProcessingStatus({ status = 'processing', message = '' }) {
  const getStatusDisplay = () => {
    switch (status) {
      case 'processing':
        return {
          icon: <Loader2 size={24} className="spinner" color="#38bdf8" />,
          title: 'Processing Video Footage',
          subtitle: message || 'Detecting persons with YOLOX-Nano, tracking with ByteTrack, and extracting OSNet embeddings...',
          badgeClass: 'badge-processing',
        };
      case 'completed':
        return {
          icon: <CheckCircle size={24} color="#10b981" />,
          title: 'Search Completed',
          subtitle: message || 'Qdrant vector similarity search returned the highest confidence matches below.',
          badgeClass: 'badge-completed',
        };
      case 'failed':
        return {
          icon: <AlertCircle size={24} color="#ef4444" />,
          title: 'Processing Issue Encountered',
          subtitle: message || 'Could not complete similarity matching on this video batch.',
          badgeClass: 'badge-failed',
        };
      default:
        return {
          icon: <Clock size={24} color="#f59e0b" />,
          title: 'Job Queued',
          subtitle: message || 'Waiting for available compute worker...',
          badgeClass: 'badge-queued',
        };
    }
  };

  const { icon, title, subtitle } = getStatusDisplay();

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1rem',
      backgroundColor: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      padding: '1.25rem 1.5rem',
      borderRadius: 'var(--radius-md)',
      marginBottom: '2rem'
    }}>
      <div>{icon}</div>
      <div>
        <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff' }}>{title}</h4>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '2px' }}>{subtitle}</p>
      </div>
    </div>
  );
}
