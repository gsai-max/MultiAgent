import React from 'react';
import { Compass, Radio, ShieldCheck } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header style={{
      background: 'var(--ink-700)',
      borderBottom: '1px solid var(--ink-600)',
      padding: '1.25rem 0',
      marginBottom: '2rem'
    }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            background: 'var(--ink-900)',
            border: '1px solid var(--amber-500)',
            padding: '0.5rem',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Compass size={24} color="var(--amber-500)" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.35rem', fontWeight: 700, margin: 0, color: '#F8FAFC', fontFamily: 'var(--font-board)' }}>
              AI TRAVEL TERMINAL
            </h1>
            <p style={{ fontSize: '0.8rem', color: '#94A3B8', margin: 0, fontFamily: 'var(--font-board)', letterSpacing: '0.04em' }}>
              MULTI-AGENT DEPARTURE & ITINERARY ORCHESTRATOR
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontFamily: 'var(--font-board)', fontSize: '0.8rem' }}>
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: '#080C14',
            color: 'var(--teal-500)',
            border: '1px solid rgba(63, 167, 160, 0.4)',
            padding: '0.3rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            fontWeight: 600
          }}>
            <Radio size={12} /> ENGINE v1.0 ONLINE
          </span>

          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: '#080C14',
            color: 'var(--amber-500)',
            border: '1px solid rgba(232, 162, 61, 0.4)',
            padding: '0.3rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            fontWeight: 600
          }}>
            <ShieldCheck size={12} /> QUALITY GATE ACTIVE
          </span>
        </div>
      </div>
    </header>
  );
};

