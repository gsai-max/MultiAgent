import React, { useState } from 'react';
import { Ticket, PlaneTakeoff, Compass } from 'lucide-react';

interface RequestFormProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

const PRESETS = [
  {
    title: 'NRT / KIX — JAPAN TEMPLE & FOOD',
    prompt: '5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples, less crowded options preferred',
  },
  {
    title: 'FCO / FLR — ITALY ART & CULTURE',
    prompt: '7 day trip to Rome and Florence with $4500 budget focusing on renaissance art, walking tours, and authentic dining',
  },
  {
    title: 'CDG — PARIS BOUTIQUE & MUSEUMS',
    prompt: '4 day trip to Paris with $3500 budget focusing on art museums, fine dining, and boutique hotels',
  },
];

export const RequestForm: React.FC<RequestFormProps> = ({ onSubmit, isLoading }) => {
  const [requestText, setRequestText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (requestText.trim() && !isLoading) {
      onSubmit(requestText.trim());
    }
  };

  const handlePresetClick = (presetPrompt: string) => {
    setRequestText(presetPrompt);
  };

  return (
    <div className="perforated-card" style={{ padding: '2rem 2.25rem', marginBottom: '2.5rem' }}>
      {/* Boarding Pass Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', borderBottom: '2px solid var(--paper-border)', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Ticket size={22} color="var(--paper-ink)" />
          <div>
            <span className="board-font" style={{ fontSize: '0.75rem', letterSpacing: '0.12em', color: 'var(--paper-muted)', display: 'block', textTransform: 'uppercase' }}>
              BOARDING PASS REQUEST // FORM 01
            </span>
            <h2 className="board-font" style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--paper-ink)' }}>
              WHERE WOULD YOU LIKE TO TRAVEL?
            </h2>
          </div>
        </div>

        <div className="board-font" style={{ fontSize: '0.75rem', color: 'var(--paper-muted)', textAlign: 'right', letterSpacing: '0.05em' }}>
          <div>CLASS: REGULAR / SPECIALIST</div>
          <div>GATE: AUTOMATED</div>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ position: 'relative', marginBottom: '1.25rem' }}>
          <label className="board-font" style={{ display: 'block', fontSize: '0.75rem', letterSpacing: '0.08em', color: 'var(--paper-muted)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
            TRAVELER ITINERARY REQUEST & CONSTRAINTS
          </label>
          <textarea
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            disabled={isLoading}
            placeholder="Describe your trip requirements (e.g., '5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples')..."
            style={{
              width: '100%',
              minHeight: '120px',
              backgroundColor: '#FAF8F0',
              border: '1.5px solid var(--paper-border)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem 1.25rem',
              color: 'var(--paper-ink)',
              fontFamily: 'var(--font-editorial)',
              fontSize: '1.1rem',
              lineHeight: 1.6,
              resize: 'vertical',
              outline: 'none',
              transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = 'var(--paper-ink)';
              e.target.style.boxShadow = '0 0 0 2px rgba(26, 39, 64, 0.1)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'var(--paper-border)';
              e.target.style.boxShadow = 'none';
            }}
          />
          <div style={{
            position: 'absolute',
            bottom: '12px',
            right: '16px',
            fontSize: '0.75rem',
            color: 'var(--paper-muted)',
            fontFamily: 'var(--font-board)'
          }}>
            {requestText.length} CHARS
          </div>
        </div>

        {/* Preset chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          <div className="board-font" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--paper-muted)', fontWeight: 600, marginRight: '0.25rem', textTransform: 'uppercase' }}>
            <Compass size={14} color="var(--paper-ink)" />
            <span>SAMPLE ROUTES:</span>
          </div>
          {PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetClick(preset.prompt)}
              disabled={isLoading}
              className="preset-chip"
            >
              {preset.title}
            </button>
          ))}
        </div>

        <div className="perforated-divider" />

        {/* Action Button */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div className="board-font" style={{ fontSize: '0.75rem', color: 'var(--paper-muted)', letterSpacing: '0.05em' }}>
            PRESS DEPART TO DISPATCH SPECIALIST AGENTS
          </div>
          <button
            type="submit"
            disabled={isLoading || !requestText.trim()}
            className="btn-amber"
            style={{ width: '100%', maxWidth: '280px' }}
          >
            <PlaneTakeoff size={18} />
            <span>{isLoading ? 'DISPATCHING AGENTS...' : 'DEPART & DISPATCH'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

