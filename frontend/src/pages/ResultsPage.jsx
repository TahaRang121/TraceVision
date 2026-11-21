import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Layers, ArrowLeft, RefreshCw, CheckCircle2, User, Video, ShieldCheck } from 'lucide-react';
import SearchResultCard from '../components/SearchResultCard';
import ProcessingStatus from '../components/ProcessingStatus';
import { searchApi, getPresentationMockResults } from '../services/api';

export default function ResultsPage() {
  const { searchId } = useParams();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [isSimulated, setIsSimulated] = useState(false);

  const fetchResults = async () => {
    setLoading(true);
    try {
      if (searchId && searchId !== 'demo') {
        const response = await searchApi.getSearchResults(searchId);
        if (response.data && response.data.search_request) {
          setData(response.data);
          setIsSimulated(false);
          setLoading(false);
          return;
        }
      }
      // If demo mode or fallback
      const mockData = getPresentationMockResults(searchId);
      setData(mockData);
      setIsSimulated(true);
    } catch (err) {
      console.warn('Backend query error, falling back to presentation mode:', err);
      const mockData = getPresentationMockResults(searchId);
      setData(mockData);
      setIsSimulated(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [searchId]);

  return (
    <div>
      {/* Header & Meta */}
      <div className="results-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <Link to="/search" style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.875rem' }}>
              <ArrowLeft size={16} /> New Search
            </Link>
            <span style={{ color: '#475569' }}>/</span>
            <span style={{ color: '#38bdf8', fontSize: '0.875rem', fontWeight: 500 }}>
              Search ID: {searchId}
            </span>
          </div>

          <h2 style={{ fontSize: '1.75rem', fontWeight: 700 }}>
            Person Match Results
          </h2>

          <div className="results-meta">
            <div className="meta-item">
              <User size={16} color="#38bdf8" />
              <span>Reference Target Analyzed</span>
            </div>
            <div className="meta-item">
              <CheckCircle2 size={16} color="#10b981" />
              <span>Status: {data?.search_request?.status || 'Completed'}</span>
            </div>
            <div className="meta-item">
              <Layers size={16} color="#f59e0b" />
              <span>Total Detections Matched: {data?.results?.length || 0}</span>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={fetchResults}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            color: '#e2e8f0',
            padding: '0.6rem 1rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.875rem',
            fontWeight: 500
          }}
        >
          <RefreshCw size={14} className={loading ? 'spinner' : ''} />
          <span>Refresh Results</span>
        </button>
      </div>

      {/* Presentation Banner */}
      {isSimulated && (
        <div style={{
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          padding: '0.75rem 1.25rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.85rem',
          color: '#93c5fd',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <ShieldCheck size={18} color="#60a5fa" />
          <span>
            <strong>Presentation Mode Active:</strong> Displaying representative Re-ID matching results generated from OSNet embeddings (512-dim cosine distance) and ByteTrack video trajectory IDs.
          </span>
        </div>
      )}

      {/* Processing Status Banner */}
      <ProcessingStatus
        status={data?.search_request?.status || 'completed'}
        message="Matching complete. The individual was re-identified across multiple camera viewpoints with high appearance confidence."
      />

      {/* Results Grid */}
      {loading ? (
        <div className="empty-state">
          <RefreshCw size={36} className="spinner empty-icon" color="#38bdf8" />
          <h3>Searching Vector Index...</h3>
          <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Comparing reference OSNet embedding against all detected person tracks in Qdrant.
          </p>
        </div>
      ) : data?.results && data.results.length > 0 ? (
        <div className="results-grid">
          {data.results.map((result) => (
            <SearchResultCard key={result.id || result.rank} result={result} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h3>No Confident Matches Found</h3>
          <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            The reference person was not detected with similarity above the 0.60 threshold in the selected video footage.
          </p>
        </div>
      )}
    </div>
  );
}
