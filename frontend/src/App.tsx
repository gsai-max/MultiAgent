import React, { useState, useRef } from 'react';
import { Header } from './components/Header';
import { RequestForm } from './components/RequestForm';
import { LoadingState } from './components/LoadingState';
import { ErrorAlert } from './components/ErrorAlert';
import { ResultsLayout } from './components/ResultsLayout';
import { generatePlan } from './services/api';
import { FinalItinerary, PlanApiError } from './types/itinerary';

export const App: React.FC = () => {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [itinerary, setItinerary] = useState<FinalItinerary | null>(null);
  const [error, setError] = useState<PlanApiError | null>(null);
  const [lastRequestPrompt, setLastRequestPrompt] = useState<string>('');
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleGeneratePlan = async (prompt: string) => {
    setLastRequestPrompt(prompt);
    setStatus('loading');
    setError(null);
    setItinerary(null);

    // Setup abort controller for cancel capability
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await generatePlan(prompt, controller.signal);
      setItinerary(response.final_itinerary);
      setStatus('success');
    } catch (err: any) {
      if (err.status_code === 0) {
        // User cancelled
        setStatus('idle');
      } else {
        setError(err as PlanApiError);
        setStatus('error');
      }
    } finally {
      abortControllerRef.current = null;
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setStatus('idle');
  };

  const handleReset = () => {
    setStatus('idle');
    setItinerary(null);
    setError(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />

      <main style={{ flex: 1, paddingBottom: '4rem' }}>
        <div className="container">
          {/* Always show request form when idle, error, or loading */}
          {status !== 'success' && (
            <RequestForm onSubmit={handleGeneratePlan} isLoading={status === 'loading'} />
          )}

          {/* Loading state visualizer */}
          {status === 'loading' && (
            <LoadingState onCancel={handleCancel} />
          )}

          {/* Error Alert */}
          {status === 'error' && error && (
            <ErrorAlert error={error} onRetry={() => handleGeneratePlan(lastRequestPrompt)} />
          )}

          {/* Results Layout */}
          {status === 'success' && itinerary && (
            <ResultsLayout itinerary={itinerary} onReset={handleReset} />
          )}
        </div>
      </main>

      <footer style={{
        borderTop: '1px solid var(--border-color)',
        padding: '1.5rem 0',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '0.85rem'
      }}>
        <div className="container">
          AI Travel Planner &copy; {new Date().getFullYear()} — Multi-Agent Travel Orchestration Engine (Phase 9 Active)
        </div>
      </footer>
    </div>
  );
};

export default App;
