import React from 'react';
import { AlertTriangle, RefreshCw, Hash } from 'lucide-react';
import { PlanApiError } from '../types/itinerary';

interface ErrorAlertProps {
  error: PlanApiError;
  onRetry: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({ error, onRetry }) => {
  return (
    <div className="glass-card animate-fade-in" style={{
      padding: '2rem',
      marginBottom: '2.5rem',
      borderColor: 'rgba(244, 63, 94, 0.3)',
      backgroundColor: 'rgba(244, 63, 94, 0.05)',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
        <div style={{
          padding: '0.65rem',
          backgroundColor: 'rgba(244, 63, 94, 0.15)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--accent-rose)',
        }}>
          <AlertTriangle size={24} />
        </div>

        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-rose)', margin: '0 0 0.5rem 0' }}>
            Plan Generation Failed
          </h3>
          <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem', marginBottom: '1rem' }}>
            {error.message}
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
            {error.status_code !== undefined && error.status_code > 0 && (
              <span className="badge badge-rose">
                HTTP {error.status_code}
              </span>
            )}

            {error.trace_id && (
              <span className="badge badge-purple" style={{ textTransform: 'none' }}>
                <Hash size={12} /> trace: {error.trace_id}
              </span>
            )}
          </div>

          <button type="button" onClick={onRetry} className="btn-primary" style={{ background: 'var(--accent-rose)', boxShadow: '0 4px 15px rgba(244, 63, 94, 0.3)' }}>
            <RefreshCw size={16} /> Try Again
          </button>
        </div>
      </div>
    </div>
  );
};
