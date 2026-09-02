import React, { useState } from 'react';
import {
  Calendar, MapPin, DollarSign, Clock, CheckCircle, AlertTriangle,
  Hotel, Train, ShieldCheck, Copy, Check, ArrowRight, Info, Award
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
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      
      {/* 1. OVERVIEW BANNER */}
      <div className="glass-card" style={{ padding: '2rem', position: 'relative', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute',
          top: 0,
          right: 0,
          width: '300px',
          height: '100%',
          background: 'linear-gradient(270deg, rgba(56, 189, 248, 0.08) 0%, transparent 100%)',
          pointerEvents: 'none'
        }} />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <span className="badge badge-cyan">
                <MapPin size={12} /> {constraints.destination_region}
              </span>
              <span className="badge badge-purple">
                <Calendar size={12} /> {constraints.duration_days} Days
              </span>
              <span className="badge badge-emerald">
                <DollarSign size={12} /> ${constraints.budget_total} {constraints.currency} Cap
              </span>
            </div>
            <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
              Your Custom Multi-Agent Itinerary
            </h2>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button type="button" onClick={handleCopyMarkdown} className="btn-secondary">
              {copied ? <Check size={16} color="var(--accent-emerald)" /> : <Copy size={16} />}
              <span>{copied ? 'Copied Markdown!' : 'Copy Markdown'}</span>
            </button>
            <button type="button" onClick={onReset} className="btn-primary" style={{ padding: '0.6rem 1.25rem', fontSize: '0.9rem' }}>
              New Plan
            </button>
          </div>
        </div>

        {/* Narrative Summary */}
        <p style={{ color: 'var(--text-secondary)', fontSize: '1rem', lineHeight: 1.7, marginBottom: '1.5rem' }}>
          {narrative_summary}
        </p>

        {/* Quick Stats Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          padding: '1.25rem',
          backgroundColor: 'rgba(9, 13, 22, 0.5)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(255, 255, 255, 0.05)'
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Cities Visited
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
              {constraints.cities.join(' → ')}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Estimated Total Spend
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: budget_summary.within_budget ? 'var(--accent-emerald)' : 'var(--accent-rose)', marginTop: '2px' }}>
              ${budget_summary.total_estimated_spend} {constraints.currency}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Quality Gate Status
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: review_report.passed ? 'var(--accent-emerald)' : 'var(--accent-amber)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <ShieldCheck size={18} /> {review_report.passed ? 'Verified & Passed' : 'Advisory Notes'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Request Trace ID
            </div>
            <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '4px', fontFamily: 'monospace' }}>
              {trace_id.substring(0, 16)}...
            </div>
          </div>
        </div>
      </div>

      {/* 2. MAIN ITINERARY SCHEDULE + SIDEBAR */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: '2rem' }}>
        
        {/* DAY BY DAY TIMELINE */}
        <div className="glass-card" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              <Calendar size={22} color="var(--accent-blue)" />
              <h3 style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0 }}>
                Day-by-Day Itinerary
              </h3>
            </div>

            {/* Day Selector Tabs */}
            <div style={{ display: 'flex', gap: '0.35rem', overflowX: 'auto', paddingBottom: '0.25rem' }}>
              {day_by_day.map((day) => (
                <button
                  key={day.day_number}
                  type="button"
                  onClick={() => setSelectedDay(day.day_number)}
                  style={{
                    padding: '0.45rem 0.9rem',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid',
                    borderColor: selectedDay === day.day_number ? 'var(--accent-blue)' : 'rgba(255, 255, 255, 0.08)',
                    backgroundColor: selectedDay === day.day_number ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    color: selectedDay === day.day_number ? 'var(--accent-blue)' : 'var(--text-secondary)',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.2s ease',
                  }}
                >
                  Day {day.day_number}
                </button>
              ))}
            </div>
          </div>

          {/* Selected Day View */}
          {currentDayData && (
            <div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.85rem 1.25rem',
                backgroundColor: 'rgba(56, 189, 248, 0.06)',
                borderRadius: 'var(--radius-md)',
                marginBottom: '1.5rem',
                border: '1px solid rgba(56, 189, 248, 0.15)'
              }}>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                  Day {currentDayData.day_number} — {currentDayData.city}
                </div>
                <span className="badge badge-cyan">
                  {currentDayData.slots.length} Activities Scheduled
                </span>
              </div>

              {/* Slot Cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {currentDayData.slots.map((slot, idx) => (
                  <div
                    key={slot.slot_id || idx}
                    style={{
                      position: 'relative',
                      padding: '1.25rem',
                      backgroundColor: 'rgba(9, 13, 22, 0.5)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      display: 'flex',
                      gap: '1.25rem',
                    }}
                  >
                    {/* Time Window Badge */}
                    <div style={{ minWidth: '100px', display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                      <span className={`badge ${
                        slot.time_of_day === 'morning' ? 'badge-amber' :
                        slot.time_of_day === 'afternoon' ? 'badge-cyan' : 'badge-purple'
                      }`}>
                        <Clock size={12} /> {slot.time_of_day}
                      </span>
                      {slot.travel_time_from_prev_minutes > 0 && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <ArrowRight size={12} /> {slot.travel_time_from_prev_minutes}m transit
                        </div>
                      )}
                    </div>

                    {/* Slot Details */}
                    <div style={{ flex: 1 }}>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                        {slot.activity_name}
                      </h4>
                      {slot.notes && (
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                          {slot.notes}
                        </p>
                      )}
                      {slot.activity_id && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', fontFamily: 'monospace' }}>
                          ID: {slot.activity_id}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT SIDEBAR: BUDGET & LOGISTICS */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* BUDGET BREAKDOWN CARD */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <DollarSign size={20} color="var(--accent-emerald)" />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>
                Budget Allocation
              </h3>
            </div>

            {/* Total Budget Progress Bar */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '0.35rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Spend vs Cap</span>
                <span style={{ fontWeight: 600, color: budget_summary.within_budget ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  ${budget_summary.total_estimated_spend} / ${constraints.budget_total}
                </span>
              </div>

              <div style={{
                height: '8px',
                width: '100%',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: `${Math.min(100, (budget_summary.total_estimated_spend / constraints.budget_total) * 100)}%`,
                  backgroundColor: budget_summary.within_budget ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                  borderRadius: '4px',
                  transition: 'width 0.5s ease',
                }} />
              </div>
            </div>

            {/* Per Category breakdown */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {Object.entries(budget_summary.per_category_totals).map(([cat, amount]) => (
                <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.875rem' }}>
                  <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{cat}</span>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>${amount} {constraints.currency}</span>
                </div>
              ))}
            </div>

            {/* Swaps / Suggestions */}
            {budget_summary.suggested_swaps.length > 0 && (
              <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--accent-amber)', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Cost Saving Suggestions:
                </div>
                {budget_summary.suggested_swaps.map((swap, idx) => (
                  <div key={idx} style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
                    • {typeof swap === 'string' ? swap : JSON.stringify(swap)}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* LODGING & TRANSIT CARD */}
          <div className="glass-card" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
              <Hotel size={20} color="var(--accent-purple)" />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>
                Lodging & Logistics
              </h3>
            </div>

            {/* Stay Options */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '0.5rem' }}>
                Accommodation Suggestions
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {lodging_plan.options.map((opt) => (
                  <div key={opt.id} style={{
                    padding: '0.75rem',
                    backgroundColor: 'rgba(9, 13, 22, 0.5)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(255, 255, 255, 0.05)'
                  }}>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>{opt.name}</div>
                    <div style={{ fontSize: '0.775rem', color: 'var(--text-secondary)' }}>{opt.city} • {opt.neighborhood}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 600, marginTop: '2px' }}>
                      ${opt.estimated_cost_per_night} / night
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Inter-city Movement */}
            <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '0.5rem' }}>
                <Train size={14} /> Transit Mode
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--accent-blue)' }}>
                {movement_plan.inter_city_mode}
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* 3. QUALITY GATE REVIEW REPORT */}
      <div className="glass-card" style={{ padding: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
          <Award size={22} color="var(--accent-indigo)" />
          <h3 style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0 }}>
            Quality Gate Verification Report
          </h3>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem'
        }}>
          {Object.entries(review_report.checklist).map(([rule, isPassed]) => (
            <div
              key={rule}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.85rem 1rem',
                backgroundColor: 'rgba(9, 13, 22, 0.5)',
                borderRadius: 'var(--radius-md)',
                border: `1px solid ${isPassed ? 'rgba(16, 185, 129, 0.2)' : 'rgba(244, 63, 94, 0.2)'}`
              }}
            >
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                {rule.replace(/_/g, ' ')}
              </span>
              {isPassed ? (
                <span className="badge badge-emerald"><CheckCircle size={12} /> Passed</span>
              ) : (
                <span className="badge badge-rose"><AlertTriangle size={12} /> Flagged</span>
              )}
            </div>
          ))}
        </div>

        {review_report.issues.length > 0 && (
          <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--accent-amber)', marginBottom: '0.5rem' }}>
              Flagged Review Notes & Advisories:
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {review_report.issues.map((issue) => (
                <div key={issue.issue_id} style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                  <AlertTriangle size={15} color="var(--accent-amber)" style={{ marginTop: '2px', flexShrink: 0 }} />
                  <div>
                    <strong style={{ color: 'var(--text-primary)' }}>[{issue.severity.toUpperCase()}]</strong> {issue.description}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 4. PROMINENT MANDATORY DISCLAIMER BOX */}
      <div className="glass-card" style={{
        padding: '1.5rem',
        backgroundColor: 'rgba(2, 132, 199, 0.08)',
        borderColor: 'rgba(56, 189, 248, 0.25)'
      }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem' }}>
          <Info size={22} color="var(--accent-blue)" style={{ marginTop: '2px', flexShrink: 0 }} />
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-blue)', margin: '0 0 0.35rem 0' }}>
              AI Travel Planner Demonstration Disclaimer
            </h4>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.6 }}>
              {disclaimer}
            </p>
          </div>
        </div>
      </div>

    </div>
  );
};
