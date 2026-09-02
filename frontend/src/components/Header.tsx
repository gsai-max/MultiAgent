import React from 'react';
import { Compass, Sparkles, ShieldCheck } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header style={{ padding: '1.75rem 0', borderBottom: '1px solid var(--border-color)', marginBottom: '2.5rem' }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-indigo))',
            padding: '0.65rem',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 15px rgba(56, 189, 248, 0.3)'
          }}>
            <Compass size={28} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.65rem', fontWeight: 800, margin: 0, background: 'linear-gradient(90deg, #ffffff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              AI Travel Planner
            </h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
              Multi-Agent Autonomous Itinerary Orchestration Engine
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="badge badge-cyan">
            <Sparkles size={13} /> Multi-Agent Engine v1.0
          </span>
          <span className="badge badge-emerald">
            <ShieldCheck size={13} /> Quality Gate Active
          </span>
        </div>
      </div>
    </header>
  );
};
