import React, { useEffect, useState } from 'react';
import { Loader2, Check, X, FileText, Cpu, GitMerge, ShieldCheck } from 'lucide-react';

interface LoadingStateProps {
  onCancel?: () => void;
}

const PIPELINE_STEPS = [
  {
    icon: FileText,
    label: 'EXTRACT',
    title: 'Extracting Travel Constraints',
    desc: 'Parsing natural language into target region, duration, budget, and preference tags.',
  },
  {
    icon: Cpu,
    label: 'SPECIALISTS',
    title: 'Parallel Specialist Agents',
    desc: 'Destination, Logistics, and Budget agents executing specialist sub-tasks concurrently.',
  },
  {
    icon: GitMerge,
    label: 'SYNTHESIS',
    title: 'Orchestrator Synthesis & Merge',
    desc: 'Resolving destination slots, lodging night allocations, and cost totals into a cohesive draft.',
  },
  {
    icon: ShieldCheck,
    label: 'REVIEW',
    title: 'Quality Gate & Repair Loop',
    desc: 'Verifying time realism, budget bounds, city coverage, and executing bounded repairs if needed.',
  },
];

export const LoadingState: React.FC<LoadingStateProps> = ({ onCancel }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStepIndex((prevIndex) => {
        if (prevIndex < PIPELINE_STEPS.length - 1) {
          return prevIndex + 1;
        }
        return prevIndex;
      });
    }, 2800);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="board-housing" style={{ padding: '2.5rem 2rem', marginBottom: '2.5rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <div style={{
          display: 'inline-flex',
          padding: '0.85rem',
          background: '#080C14',
          border: '1px solid var(--amber-500)',
          borderRadius: '50%',
          marginBottom: '1rem'
        }}>
          <Loader2 size={32} color="var(--amber-500)" style={{ animation: 'spin 1.5s linear infinite' }} />
        </div>

        <style>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>

        <h3 className="board-font" style={{ fontSize: '1.35rem', fontWeight: 700, color: '#F8FAFC', marginBottom: '0.35rem' }}>
          STATION PIPELINE IN PROGRESS
        </h3>
        <p style={{ color: '#94A3B8', maxWidth: '520px', margin: '0 auto', fontSize: '0.95rem' }}>
          Specialist agents are routing through station nodes: analyzing catalogs, building transit matrices, and auditing quality rules.
        </p>
      </div>

      {/* Station Line Pipeline Diagram */}
      <div className="station-pipeline" style={{ maxWidth: '680px', margin: '0 auto' }}>
        {PIPELINE_STEPS.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isActive = idx === currentStepIndex;

          return (
            <div
              key={idx}
              className={`station-track ${isActive || isDone ? 'active' : ''}`}
            >
              <div className={`station-node ${isDone ? 'done' : isActive ? 'active' : ''}`}>
                {isDone ? (
                  <Check size={12} color="#0E1524" strokeWidth={3} />
                ) : isActive ? (
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#0E1524' }} />
                ) : null}
              </div>

              <div style={{
                background: '#080C14',
                border: `1px solid ${isActive ? 'var(--teal-500)' : isDone ? 'rgba(63, 167, 160, 0.4)' : 'var(--ink-600)'}`,
                borderRadius: 'var(--radius-md)',
                padding: '1rem 1.25rem',
                transition: 'all 0.3s ease'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                  <div className="board-font" style={{
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    color: isActive ? 'var(--amber-500)' : isDone ? 'var(--teal-500)' : '#64748B',
                    letterSpacing: '0.08em'
                  }}>
                    STATION {idx + 1} // {step.label}
                  </div>
                  {isActive && (
                    <span className="board-flap" style={{ fontSize: '0.7rem' }}>
                      PROCESSING
                    </span>
                  )}
                  {isDone && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--teal-500)', fontFamily: 'var(--font-board)', fontWeight: 600 }}>
                      CLEARED
                    </span>
                  )}
                </div>

                <div className="board-font" style={{ fontSize: '1rem', fontWeight: 600, color: '#F8FAFC', marginBottom: '0.25rem' }}>
                  {step.title}
                </div>
                <div style={{ fontSize: '0.875rem', color: '#94A3B8' }}>
                  {step.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {onCancel && (
        <div style={{ textAlign: 'center', marginTop: '2.25rem' }}>
          <button type="button" onClick={onCancel} className="btn-terminal">
            <X size={15} /> ABORT DISPATCH
          </button>
        </div>
      )}
    </div>
  );
};

