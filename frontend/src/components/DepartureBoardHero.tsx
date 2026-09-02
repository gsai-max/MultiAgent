import React, { useEffect, useState } from 'react';
import { Plane, Radio, Clock, Cpu } from 'lucide-react';

interface FlightRow {
  flight: string;
  destination: string;
  agent: string;
  status: string;
  time: string;
}

const INITIAL_ROWS: FlightRow[] = [
  { flight: 'MA-101', destination: 'TOKYO & KYOTO', agent: 'DESTINATION SPECS', status: 'READY FOR DEPARTURE', time: '09:00' },
  { flight: 'MA-204', destination: 'ROME & FLORENCE', agent: 'LOGISTICS ENGINE', status: 'ROUTE OPTIMIZED', time: '11:30' },
  { flight: 'MA-308', destination: 'PARIS BOUTIQUE', agent: 'BUDGET AUDITOR', status: 'QUALITY CHECKED', time: '14:15' },
];

export const DepartureBoardHero: React.FC = () => {
  const [rows] = useState<FlightRow[]>(INITIAL_ROWS);
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setPulse(true);
      setTimeout(() => setPulse(false), 500);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  return (
    <section style={{ marginBottom: '2rem' }}>
      <div className="board-housing">
        {/* Terminal Housing Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <Plane size={20} color="var(--amber-500)" />
            <span className="board-font" style={{ fontSize: '0.85rem', letterSpacing: '0.12em', color: 'var(--amber-500)', fontWeight: 700 }}>
              TERMINAL 09 // AGENT DISPATCH BOARD
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.8rem', color: '#94A3B8', fontFamily: 'var(--font-board)' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
              <Radio size={14} color="var(--teal-500)" />
              <span style={{ color: 'var(--teal-500)', fontWeight: 600 }}>SYSTEM ONLINE</span>
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
              <Clock size={14} color="var(--amber-500)" />
              <span>LIVE REFRESH</span>
            </span>
          </div>
        </div>

        {/* Board Flap Table Readout */}
        <div className="board-readout">
          <div style={{
            display: 'grid',
            gridTemplateColumns: '100px 1fr 160px 180px',
            gap: '1rem',
            paddingBottom: '0.5rem',
            borderBottom: '1px solid rgba(232, 162, 61, 0.3)',
            fontSize: '0.75rem',
            color: 'rgba(232, 162, 61, 0.7)',
            letterSpacing: '0.08em'
          }}>
            <div>FLIGHT</div>
            <div>DESTINATION ROUTE</div>
            <div>ASSIGNED AGENT</div>
            <div>GATE STATUS</div>
          </div>

          {rows.map((row, idx) => (
            <div key={idx} className="board-row">
              <div className="board-cell">
                <span className={`board-flap ${pulse ? 'animate-flap' : ''}`}>{row.flight}</span>
              </div>
              <div className="board-cell" style={{ fontWeight: 600 }}>
                {row.destination}
              </div>
              <div className="board-cell" style={{ fontSize: '0.8rem', color: 'var(--teal-500)' }}>
                <Cpu size={12} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                {row.agent}
              </div>
              <div className="board-cell" style={{ fontSize: '0.8rem', color: 'var(--amber-500)' }}>
                {row.status}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
