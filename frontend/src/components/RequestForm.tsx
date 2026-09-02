import React, { useState } from 'react';
import { Send, Lightbulb, Sparkles } from 'lucide-react';

interface RequestFormProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

const PRESETS = [
  {
    title: 'Japan Food & Temples',
    prompt: '5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples, less crowded options preferred',
  },
  {
    title: 'Italy Art & Culture',
    prompt: '7 day trip to Rome and Florence with $4500 budget focusing on renaissance art, walking tours, and authentic dining',
  },
  {
    title: 'Paris Luxury & Museums',
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
    <div className="glass-card animate-fade-in" style={{ padding: '2rem', marginBottom: '2.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <Sparkles size={20} color="var(--accent-blue)" />
        <h2 style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0 }}>
          Where would you like to travel?
        </h2>
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ position: 'relative', marginBottom: '1.25rem' }}>
          <textarea
            value={requestText}
            onChange={(e) => setRequestText(e.target.value)}
            disabled={isLoading}
            placeholder="Describe your trip requirements (destination, duration, cities, budget, interests, avoidances)... e.g., '5 day trip to Tokyo and Kyoto with $3000 budget focusing on food and temples'"
            style={{
              width: '100%',
              minHeight: '130px',
              backgroundColor: 'rgba(9, 13, 22, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-body)',
              fontSize: '1rem',
              lineHeight: 1.6,
              resize: 'vertical',
              outline: 'none',
              transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = 'var(--accent-blue)';
              e.target.style.boxShadow = '0 0 0 3px rgba(56, 189, 248, 0.15)';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = 'rgba(255, 255, 255, 0.12)';
              e.target.style.boxShadow = 'none';
            }}
          />
          <div style={{
            position: 'absolute',
            bottom: '12px',
            right: '16px',
            fontSize: '0.75rem',
            color: 'var(--text-muted)'
          }}>
            {requestText.length} chars
          </div>
        </div>

        {/* Preset chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500, marginRight: '0.25rem' }}>
            <Lightbulb size={15} color="var(--accent-amber)" />
            <span>Try example:</span>
          </div>
          {PRESETS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetClick(preset.prompt)}
              disabled={isLoading}
              className="btn-secondary"
              style={{ fontSize: '0.8rem', padding: '0.35rem 0.85rem' }}
            >
              {preset.title}
            </button>
          ))}
        </div>

        {/* Action Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            disabled={isLoading || !requestText.trim()}
            className="btn-primary"
            style={{ width: '100%', maxWidth: '280px' }}
          >
            <Send size={18} />
            <span>{isLoading ? 'Orchestrating Plan...' : 'Generate Itinerary'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
