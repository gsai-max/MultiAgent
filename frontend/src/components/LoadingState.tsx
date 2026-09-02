import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, XCircle, Bot, Cpu, GitMerge, ShieldCheck } from 'lucide-react';

interface LoadingStateProps {
  onCancel?: () => void;
}

const PIPELINE_STEPS = [
  {
    icon: Bot,
    label: 'Extracting Travel Constraints',
    desc: 'Parsing natural language into structured target region, duration, budget, and preference tags.',
    duration: 1500,
  },
  {
    icon: Cpu,
    label: 'Parallel Specialist Agents',
    desc: 'Destination, Logistics, and Budget agents executing specialist sub-tasks concurrently.',
    duration: 3000,
  },
  {
    icon: GitMerge,
    label: 'Orchestrator Synthesis & Merge',
    desc: 'Resolving destination slots, lodging night allocations, and cost totals into a cohesive draft.',
    duration: 2000,
  },
  {
    icon: ShieldCheck,
    label: 'Quality Gate Review & Repair Loop',
    desc: 'Verifying time realism, budget bounds, city coverage, and applying automated repairs if needed.',
    duration: 2500,
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
    <div className="glass-card animate-fade-in" style={{ padding: '3rem 2rem', textAlign: 'center', marginBottom: '2.5rem' }}>
      <div style={{ display: 'inline-flex', padding: '1rem', background: 'rgba(56, 189, 248, 0.1)', borderRadius: '50%', marginBottom: '1.5rem' }}>
        <Loader2 size={36} color="var(--accent-blue)" style={{ animation: 'spin 1.5s linear infinite' }} />
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        Orchestrating Multi-Agent Travel Plan
      </h3>
      <p style={{ color: 'var(--text-secondary)', maxWidth: '520px', margin: '0 auto 2.5rem', fontSize: '0.95rem' }}>
        Specialist agents are analyzing destination catalogs, optimizing inter-city logistics, calculating budget breakdowns, and validating quality rules.
      </p>

      {/* Pipeline Steps */}
      <div style={{ maxWidth: '640px', margin: '0 auto', textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {PIPELINE_STEPS.map((step, idx) => {
          const StepIcon = step.icon;
          const isDone = idx < currentStepIndex;
          const isActive = idx === currentStepIndex;

          return (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                padding: '1rem 1.25rem',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isActive
                  ? 'rgba(56, 189, 248, 0.08)'
                  : isDone
                  ? 'rgba(16, 185, 129, 0.05)'
                  : 'rgba(255, 255, 255, 0.02)',
                border: `1px solid ${
                  isActive
                    ? 'rgba(56, 189, 248, 0.3)'
                    : isDone
                    ? 'rgba(16, 185, 129, 0.2)'
                    : 'rgba(255, 255, 255, 0.05)'
                }`,
                transition: 'all 0.3s ease',
              }}
            >
              <div style={{ marginTop: '2px' }}>
                {isDone ? (
                  <CheckCircle2 size={20} color="var(--accent-emerald)" />
                ) : isActive ? (
                  <Loader2 size={20} color="var(--accent-blue)" style={{ animation: 'spin 1.5s linear infinite' }} />
                ) : (
                  <StepIcon size={20} color="var(--text-muted)" />
                )}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  color: isActive ? 'var(--accent-blue)' : isDone ? 'var(--text-primary)' : 'var(--text-muted)'
                }}>
                  Step {idx + 1}: {step.label}
                </div>
                <div style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {step.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {onCancel && (
        <div style={{ marginTop: '2rem' }}>
          <button type="button" onClick={onCancel} className="btn-secondary">
            <XCircle size={16} /> Cancel Generation
          </button>
        </div>
      )}
    </div>
  );
};
