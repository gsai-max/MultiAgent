import { PlanFinalResponse, PlanApiError } from '../types/itinerary';

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

export async function generatePlan(
  requestText: string,
  signal?: AbortSignal
): Promise<PlanFinalResponse> {
  const url = `${API_BASE}/api/plan`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ request: requestText }),
      signal,
    });

    let data: any = {};
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        data = await response.json();
      } catch (jsonErr) {
        data = {};
      }
    } else {
      const textResponse = await response.text();
      data = { message: textResponse || response.statusText };
    }

    if (!response.ok) {
      const errorDetail = data?.detail || data?.message || `API server returned status ${response.status}`;
      const apiError: PlanApiError = {
        message: typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail),
        status_code: response.status,
        trace_id: data?.trace_id,
      };
      throw apiError;
    }

    return data as PlanFinalResponse;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw { message: 'Plan generation request was cancelled by user.', status_code: 0 };
    }
    if (err.message && err.status_code !== undefined) {
      throw err;
    }
    throw {
      message: err.message || 'Unable to connect to AI Travel Planner API server.',
      status_code: 500,
    } as PlanApiError;
  }
}
