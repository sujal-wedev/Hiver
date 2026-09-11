import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatView from './components/ChatView';

export default function App() {
  const [isBackendLive, setIsBackendLive] = useState(false);
  const [loading, setLoading] = useState(false);

  /* Check backend health on mount */
  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => { if (d.status === 'healthy') setIsBackendLive(true); })
      .catch(() => setIsBackendLive(false));
  }, []);

  /**
   * Process a customer message through the pipeline.
   * RETURNS the result so ChatView can append it in the same async flow
   * — no stale-closure race condition.
   */
  const handleProcess = async (text, threadLength = 1) => {
    setLoading(true);
    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, thread_length: threadLength }),
      });
      const data = await res.json();
      if (data.status === 'success' && data.data) {
        return data.data;
      }
      if (data.error) {
        throw new Error(data.error);
      }
      return null;
    } catch (e) {
      console.error('Pipeline error:', e);
      // Fallback mock for when backend isn't running
      const lower = text.toLowerCase();
      let intent = 'order_status_delivery';
      let decision = 'auto_handle';
      let reason = 'Auto-handled: Procedural request with zero risk signals';

      if (lower.includes('refund') || lower.includes('return')) {
        intent = 'refund_return';
      } else if (lower.includes('charge') || lower.includes('card') || lower.includes('lawyer') || lower.includes('attorney')) {
        intent = 'billing_dispute';
        decision = 'escalate';
        reason = 'Escalated: High-risk intent + legal keyword detected';
      } else if (lower.includes('locked') || lower.includes('password') || lower.includes('2fa')) {
        intent = 'account_access';
        decision = 'escalate';
        reason = 'Escalated: Account security concern';
      } else if (lower.includes('broken') || lower.includes('damaged') || lower.includes('shattered')) {
        intent = 'product_issue';
      } else if (lower.includes('cancel')) {
        intent = 'cancellation';
      } else if (lower.includes('worst') || lower.includes('terrible') || lower.includes('scam')) {
        intent = 'general_complaint_vent';
      }

      return {
        intent,
        confidence: 0.88,
        reply: 'Thanks for reaching out! Please send us a DM with your details so we can help. ^AH',
        decision,
        reason,
        retrieved_context: `[Fallback] No backend connected — showing mock response.`,
        hallucination_detected: false,
        hallucination_flags: [],
      };
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-neutral-950 text-neutral-200">
      <Header isBackendLive={isBackendLive} />
      <main className="flex-1 overflow-hidden max-w-3xl w-full mx-auto">
        <ChatView onProcess={handleProcess} loading={loading} />
      </main>
    </div>
  );
}
