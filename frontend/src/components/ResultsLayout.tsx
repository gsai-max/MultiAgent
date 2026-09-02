import React, { useState } from 'react';
import {
  Calendar, Clock, Check, Copy, Info, ShieldCheck,
  Hotel, Train, Tag
} from 'lucide-react';
import { FinalItinerary } from '../types/itinerary';

interface ResultsLayoutProps {
  itinerary: FinalItinerary;
  onReset: () => void;
}

export const ResultsLayout: React.FC<ResultsLayoutProps> = ({ itinerary, onReset }) => {
  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [copied, setCopied] = useState<boolean>(false);

  const {
    trace_id,
    constraints,
    day_by_day,
    lodging_plan,
    movement_plan,
    budget_summary,
    review_report,
    narrative_summary,
    disclaimer
  } = itinerary;

  const currentDayData = day_by_day.find((d) => d.day_number === selectedDay) || day_by_day[0];

  const handleCopyMarkdown = () => {
    let md = `# Trip Itinerary: ${constraints.destination_region} (${constraints.duration_days} Days)\n\n`;
    md += `**Cities:** ${constraints.cities.join(', ')}\n`;
    md += `**Budget:** ${constraints.currency} $${budget_summary.total_estimated_spend} / $${constraints.budget_total}\n\n`;
    md += `## Overview\n${narrative_summary}\n\n`;
    
    md += `## Day-by-Day Schedule\n`;
    day_by_day.forEach((d) => {
      md += `### Day ${d.day_number} (${d.city})\n`;
      d.slots.forEach((s) => {
        md += `- **${s.time_of_day.toUpperCase()}**: ${s.activity_name} (${s.travel_time_from_prev_minutes}m transit) ${s.notes ? `_(${s.notes})_` : ''}\n`;
      });
      md += `\n`;
    });

    md += `## Lodging Plan\n`;
    lodging_plan.options.forEach((opt) => {
      md += `- **${opt.city} (${opt.neighborhood})**: ${opt.name} — $${opt.estimated_cost_per_night}/night\n`;
    });

    md += `\n## Disclaimer\n${disclaimer}\n`;

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* 1. OVERVIEW BOARDING PASS HEADER */}
      <div className="perforated-card" style={{ padding: '2rem 2.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1.25rem', marginBottom: '1.25rem', borderBottom: '2px dashed var(--paper-border)', paddingBottom: '1.25rem' }}>
          <div>
            <div className="board-font" style={{ fontSize: '0.75rem', letterSpacing: '0.12em', color: 'var(--paper-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>
              OFFICIAL TRAVEL VOUCHER // TRACE: {trace_id.substring(0, 12)}
            </div>
            <h2 className="board-font" style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--paper-ink)', margin: 0 }}>
              {constraints.destination_region.toUpperCase()} — {constraints.duration_days} DAY ITINERARY
            </h2>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button type="button" onClick={handleCopyMarkdown} className="btn-terminal">
              {copied ? <Check size={14} color="var(--teal-500)" /> : <Copy size={14} />}
              <span>{copied ? 'COPIED MARKDOWN' : 'EXPORT MARKDOWN'}</span>
            </button>
            <button type="button" onClick={onReset} className="btn-amber" style={{ padding: '0.55rem 1.25rem', fontSize: '0.85rem' }}>
              NEW DISPATCH
            </button>
          </div>
        </div>

        {/* Executive Narrative Summary in Editorial Serif */}
        <p className="editorial-font" style={{ color: 'var(--paper-ink)', fontSize: '1.1rem', lineHeight: 1.7, marginBottom: '1.5rem' }}>
          {narrative_summary}
        </p>

        {/* Quick Ticket Stats Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          padding: '1rem 1.25rem',
          backgroundColor: '#FAF8F0',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--paper-border)'
        }}>
          <div>
            <div className="board-font" style={{ fontSize: '0.7rem', color: 'var(--paper-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              ROUTE CITIES
            </div>
            <div className="board-font" style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--paper-ink)', marginTop: '2px' }}>
              {constraints.cities.join(' → ')}
            </div>
          </div>

          <div>
            <div className="board-font" style={{ fontSize: '0.7rem', color: 'var(--paper-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              ESTIMATED SPEND
            </div>
            <div className="board-font" style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--paper-ink)', marginTop: '2px' }}>
              ${budget_summary.total_estimated_spend} {constraints.currency} / ${constraints.budget_total}
            </div>
          </div>

          <div>
            <div className="board-font" style={{ fontSize: '0.7rem', color: 'var(--paper-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              TRANSIT LOGISTICS
            </div>
            <div className="board-font" style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--paper-ink)', marginTop: '2px' }}>
              {movement_plan.inter_city_mode}
            </div>
          </div>

          <div>
            <div className="board-font" style={{ fontSize: '0.7rem', color: 'var(--paper-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              VALIDATION MARK
            </div>
            <div className="board-font" style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--paper-ink)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <ShieldCheck size={16} color="var(--paper-ink)" /> REVIEWER CLEARED
            </div>
          </div>
        </div>
      </div>

      {/* 2. MAIN ITINERARY SCHEDULE + SIDEBAR */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '2rem' }}>
        
        {/* DAY BY DAY TIMELINE */}
        <div className="boarding-pass-card" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem', borderBottom: '2px solid var(--paper-border)', paddingBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <Calendar size={20} color="var(--paper-ink)" />
              <h3 className="board-font" style={{ fontSize: '1.2rem', fontWeight: 700, margin: 0, color: 'var(--paper-ink)' }}>
                DAY-BY-DAY SCHEDULE
              </h3>
            </div>

            {/* Day Selector Tabs */}
            <div style={{ display: 'flex', gap: '0.35rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
              {day_by_day.map((day) => (
                <button
                  key={day.day_number}
                  type="button"
                  onClick={() => setSelectedDay(day.day_number)}
                  className="board-font"
                  style={{
                    padding: '0.4rem 0.85rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid',
                    borderColor: selectedDay === day.day_number ? 'var(--paper-ink)' : 'var(--paper-border)',
                    backgroundColor: selectedDay === day.day_number ? 'var(--paper-ink)' : '#FAF8F0',
                    color: selectedDay === day.day_number ? 'var(--paper)' : 'var(--paper-ink)',
                    fontWeight: 700,
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease',
                  }}
                >
                  DAY {day.day_number}
                </button>
              ))}
            </div>
          </div>

          {/* Selected Day View */}
          {currentDayData && (
            <div>
              <div className="board-font" style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.75rem 1rem',
                backgroundColor: '#FAF8F0',
                borderRadius: 'var(--radius-md)',
                marginBottom: '1.5rem',
                border: '1px solid var(--paper-border)'
              }}>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--paper-ink)' }}>
                  DAY {currentDayData.day_number} // CITY: {currentDayData.city.toUpperCase()}
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--paper-muted)', fontWeight: 600 }}>
                  {currentDayData.slots.length} SCHEDULED SLOTS
                </span>
              </div>

              {/* Slot Ticket Cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {currentDayData.slots.map((slot, idx) => (
                  <div
                    key={slot.slot_id || idx}
                    style={{
                      padding: '1.25rem',
                      backgroundColor: '#FAF8F0',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--paper-border)',
                      display: 'flex',
                      gap: '1.25rem',
                    }}
                  >
                    {/* Time Window Badge */}
                    <div style={{ minWidth: '95px', display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                      <span className="board-font" style={{
                        display: 'inline-block',
                        padding: '0.25rem 0.55rem',
                        backgroundColor: 'var(--paper-ink)',
                        color: 'var(--paper)',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        borderRadius: '3px',
                        letterSpacing: '0.05em',
                        textTransform: 'uppercase'
                      }}>
                        <Clock size={11} style={{ marginRight: '4px', verticalAlign: 'middle' }} />
                        {slot.time_of_day}
                      </span>
                      {slot.travel_time_from_prev_minutes > 0 && (
                        <div className="board-font" style={{ fontSize: '0.725rem', color: 'var(--paper-muted)', marginTop: '0.5rem' }}>
                          + {slot.travel_time_from_prev_minutes}m transit
                        </div>
                      )}
                    </div>

                    {/* Slot Details in Serif Editorial Font */}
                    <div style={{ flex: 1 }}>
                      <h4 className="board-font" style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--paper-ink)', marginBottom: '0.35rem' }}>
                        {slot.activity_name}
                      </h4>
                      {slot.notes && (
                        <p className="editorial-font" style={{ fontSize: '1rem', color: 'var(--paper-ink)', margin: 0, lineHeight: 1.5 }}>
                          {slot.notes}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT SIDEBAR: BUDGET & LODGING */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* BUDGET MANIFEST TICKET */}
          <div className="boarding-pass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1.5px solid var(--paper-border)', paddingBottom: '0.75rem' }}>
              <Tag size={18} color="var(--paper-ink)" />
              <h3 className="board-font" style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0, color: 'var(--paper-ink)' }}>
                BUDGET ALLOCATION
              </h3>
            </div>

            {/* Total Budget Progress Bar */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div className="board-font" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '0.35rem' }}>
                <span style={{ color: 'var(--paper-muted)' }}>SPEND VS CAP</span>
                <span style={{ fontWeight: 700, color: 'var(--paper-ink)' }}>
                  ${budget_summary.total_estimated_spend} / ${constraints.budget_total}
                </span>
              </div>

              <div style={{
                height: '8px',
                width: '100%',
                backgroundColor: '#FAF8F0',
                border: '1px solid var(--paper-border)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: `${Math.min(100, (budget_summary.total_estimated_spend / constraints.budget_total) * 100)}%`,
                  backgroundColor: 'var(--paper-ink)',
                  borderRadius: '4px',
                  transition: 'width 0.5s ease',
                }} />
              </div>
            </div>

            {/* Per Category breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
              {Object.entries(budget_summary.per_category_totals).map(([cat, amount]) => (
                <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                  <span className="editorial-font" style={{ textTransform: 'capitalize', color: 'var(--paper-muted)' }}>{cat}</span>
                  <span className="board-font" style={{ fontWeight: 700, color: 'var(--paper-ink)' }}>${amount} {constraints.currency}</span>
                </div>
              ))}
            </div>

            {/* Swaps / Suggestions */}
            {budget_summary.suggested_swaps.length > 0 && (
              <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px dashed var(--paper-border)' }}>
                <div className="board-font" style={{ fontSize: '0.75rem', color: 'var(--paper-ink)', fontWeight: 700, marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                  SAVINGS SUGGESTIONS:
                </div>
                {budget_summary.suggested_swaps.map((swap, idx) => (
                  <div key={idx} className="editorial-font" style={{ fontSize: '0.875rem', color: 'var(--paper-muted)', marginBottom: '0.25rem' }}>
                    • {typeof swap === 'string' ? swap : JSON.stringify(swap)}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* LODGING VOUCHER TICKET */}
          <div className="boarding-pass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1.5px solid var(--paper-border)', paddingBottom: '0.75rem' }}>
              <Hotel size={18} color="var(--paper-ink)" />
              <h3 className="board-font" style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0, color: 'var(--paper-ink)' }}>
                LODGING & TRANSIT
              </h3>
            </div>

            {/* Stay Options */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div className="board-font" style={{ fontSize: '0.72rem', color: 'var(--paper-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.5rem' }}>
                SUGGESTED ACCOMMODATIONS
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {lodging_plan.options.map((opt) => (
                  <div key={opt.id} style={{
                    padding: '0.75rem',
                    backgroundColor: '#FAF8F0',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--paper-border)'
                  }}>
                    <div className="board-font" style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--paper-ink)' }}>{opt.name}</div>
                    <div className="editorial-font" style={{ fontSize: '0.825rem', color: 'var(--paper-muted)' }}>{opt.city} • {opt.neighborhood}</div>
                    <div className="board-font" style={{ fontSize: '0.8rem', color: 'var(--paper-ink)', fontWeight: 700, marginTop: '2px' }}>
                      ${opt.estimated_cost_per_night} / night
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Inter-city Movement */}
            <div style={{ paddingTop: '1rem', borderTop: '1px dashed var(--paper-border)' }}>
              <div className="board-font" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem', color: 'var(--paper-muted)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '0.35rem' }}>
                <Train size={13} /> TRANSIT MODE
              </div>
              <div className="board-font" style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--paper-ink)' }}>
                {movement_plan.inter_city_mode}
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* 3. QUALITY GATE REVIEW REPORT WITH EXPLICIT PHYSICAL STAMP */}
      <div className="boarding-pass-card" style={{ padding: '2rem', position: 'relative' }}>
        
        {/* PHYSICAL VALIDATION STAMP MARK — USED EXACTLY ONCE */}
        <div style={{ position: 'absolute', top: '1.75rem', right: '2rem' }}>
          <div className="stamp-mark">
            REVIEWED & VERIFIED
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <ShieldCheck size={22} color="var(--paper-ink)" />
          <h3 className="board-font" style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--paper-ink)' }}>
            QUALITY GATE AUDIT REPORT
          </h3>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '0.85rem',
          marginBottom: '1.5rem',
          marginTop: '1rem'
        }}>
          {Object.entries(review_report.checklist).map(([rule, isPassed]) => (
            <div
              key={rule}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.75rem 0.9rem',
                backgroundColor: '#FAF8F0',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--paper-border)'
              }}
            >
              <span className="board-font" style={{ fontSize: '0.78rem', color: 'var(--paper-ink)', textTransform: 'uppercase', fontWeight: 600 }}>
                {rule.replace(/_/g, ' ')}
              </span>
              <span className="board-font" style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: isPassed ? 'var(--paper-ink)' : 'var(--stamp-600)'
              }}>
                {isPassed ? '✓ PASSED' : '⚠ FLAG'}
              </span>
            </div>
          ))}
        </div>

        {review_report.issues.length > 0 && (
          <div style={{ paddingTop: '1rem', borderTop: '1px dashed var(--paper-border)' }}>
            <h4 className="board-font" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--stamp-600)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
              REVIEW AUDIT ADVISORIES:
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {review_report.issues.map((issue) => (
                <div key={issue.issue_id} className="editorial-font" style={{ fontSize: '0.95rem', color: 'var(--paper-ink)', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                  <span className="board-font" style={{ color: 'var(--stamp-600)', fontWeight: 700, fontSize: '0.8rem' }}>[{issue.severity.toUpperCase()}]</span>
                  <span>{issue.description}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 4. MANDATORY DISCLAIMER TICKET */}
      <div className="boarding-pass-card" style={{ padding: '1.5rem', backgroundColor: '#EAE3D2' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
          <Info size={20} color="var(--paper-ink)" style={{ marginTop: '2px', flexShrink: 0 }} />
          <div>
            <h4 className="board-font" style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--paper-ink)', margin: '0 0 0.35rem 0', textTransform: 'uppercase' }}>
              TERMINAL DEMONSTRATION NOTICE & DISCLAIMER
            </h4>
            <p className="editorial-font" style={{ fontSize: '0.95rem', color: 'var(--paper-muted)', margin: 0, lineHeight: 1.6 }}>
              {disclaimer}
            </p>
          </div>
        </div>
      </div>

    </div>
  );
};

