import React, { useState } from 'react';
import { AlertTriangle, ChevronRight, CheckCircle2, ShieldAlert, Sparkles, HelpCircle } from 'lucide-react';

export default function FailureAnalysisTab() {
  const [activeFailure, setActiveFailure] = useState(0);

  const failureCases = [
    {
      id: 1,
      title: "Boundary Overlap — Delayed Refund vs. Order Delivery",
      error_type: "Intent Misclassification",
      tweet_id: "TW-1042",
      text: "I returned my package 2 weeks ago but tracking still hasn't updated and no refund yet!",
      true_intent: "refund_return",
      pred_intent: "order_status_delivery",
      true_action: "auto_handle",
      pred_action: "auto_handle",
      pred_reason: "Auto-handled: Procedural/informational request with zero risk signals detected",
      reply: "We're sorry to hear about the delay with your return! Please send us a DM with your tracking number so we can check on your refund status. ^AH",
      hypothesis: "Customer message contains semantic markers for both 'package tracking' and 'refund'. The LLM classifier prioritized the tracking keyword.",
      mitigation: "Enhance taxonomy prompt definition to explicitly prioritize intent mapping by primary requested resolution (e.g. monetary refund vs shipping status)."
    },
    {
      id: 2,
      title: "Implicit Frustration without Explicit Escalation Keywords",
      error_type: "Escalation Policy Under-Escalation (False Negative)",
      tweet_id: "TW-1089",
      text: "Is there anyone alive in customer service or is everyone just sleeping today?",
      true_intent: "general_complaint_vent",
      pred_intent: "general_complaint_vent",
      true_action: "escalate",
      pred_action: "auto_handle",
      pred_reason: "Auto-handled: Procedural/informational request with zero risk signals detected",
      reply: "We're here and ready to help! Please send us a direct message with your order details so we can assist you right away. ^AH",
      hypothesis: "Sarcastic customer vent lacked explicit financial, legal, or explicit supervisor keywords (e.g. 'lawyer', '$', 'manager').",
      mitigation: "Incorporate an LLM-based sentiment/sarcasm score threshold into the deterministic policy for subtle customer agitation."
    },
    {
      id: 3,
      title: "Over-Escalation on Procedural Dollar Inquiries",
      error_type: "Escalation Policy Over-Escalation (False Positive)",
      tweet_id: "TW-1115",
      text: "How much is the return shipping fee for a $15 book?",
      true_intent: "refund_return",
      pred_intent: "refund_return",
      true_action: "auto_handle",
      pred_action: "escalate",
      pred_reason: "Escalated due to: Monetary value involved ($15)",
      reply: "Please send us a direct message with your order details so we can assist you with your return. ^AH",
      hypothesis: "Regex rule fired on '$15', triggering monetary value policy even though it was an informational inquiry.",
      mitigation: "Refine monetary regex signal to distinguish active monetary dispute claims from passive price inquiry contexts."
    },
    {
      id: 4,
      title: "Subtle 2FA Account Access vs App Website Bug",
      error_type: "Taxonomy Boundary Ambiguity",
      tweet_id: "TW-1140",
      text: "App keeps saying invalid OTP when entering the code received via SMS.",
      true_intent: "account_access",
      pred_intent: "app_website_bug",
      true_action: "escalate",
      pred_action: "auto_handle",
      pred_reason: "Auto-handled: Procedural/informational request with zero risk signals detected",
      reply: "Thanks for reporting this app issue! Please try clearing your app cache and try again. ^AH",
      hypothesis: "Customer framed authentication failure as an app technical error ('App keeps saying...'), leading model to classify under website bug.",
      mitigation: "Include few-shot disambiguation examples in intent classification prompt for authentication errors occurring within mobile apps."
    },
    {
      id: 5,
      title: "Multi-turn Thread Fatigue Missed on Single Text View",
      error_type: "Contextual Thread Length Misalignment",
      tweet_id: "TW-1192",
      text: "Day 5 of waiting for a resolution to my ticket.",
      true_intent: "order_status_delivery",
      pred_intent: "order_status_delivery",
      true_action: "escalate",
      pred_action: "auto_handle",
      pred_reason: "Auto-handled: Procedural/informational request with zero risk signals detected",
      reply: "We apologize for the wait! Please DM us your order number so we can investigate. ^AH",
      hypothesis: "When thread_length parameter defaults to 1, single-turn text view misses prior agent commitments without explicit keyword match.",
      mitigation: "Expose multi-turn thread length tracking directly in API payload and add temporal delay phrases ('Day X of waiting') to repeat-contact regex patterns."
    }
  ];

  const current = failureCases[activeFailure];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Banner */}
      <div className="glass-card bg-gradient-to-r from-slate-900 via-rose-950/40 to-slate-900 border-rose-500/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-400" />
              Systematic Failure Analysis — Top 5 Failure Modes
            </h2>
            <p className="text-sm text-slate-300 mt-1">
              Rigorous diagnostic breakdown of real representative failure cases encountered during golden evaluation.
            </p>
          </div>
          <div className="badge badge-rose px-3 py-1.5 text-xs">
            Empirical Error Audit
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left List Selector */}
        <div className="lg:col-span-4 space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Select Failure Case:
          </h3>
          {failureCases.map((fc, idx) => (
            <button
              key={fc.id}
              onClick={() => setActiveFailure(idx)}
              className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                activeFailure === idx
                  ? 'bg-rose-950/30 border-rose-500/50 text-white shadow-lg'
                  : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:bg-slate-800/40'
              }`}
            >
              <div>
                <span className="text-xs font-mono text-rose-400 block font-semibold">
                  Case #{fc.id}: {fc.error_type}
                </span>
                <span className="text-sm font-medium line-clamp-1 mt-0.5">
                  {fc.title}
                </span>
              </div>
              <ChevronRight className={`w-4 h-4 shrink-0 ${activeFailure === idx ? 'text-rose-400' : 'text-slate-600'}`} />
            </button>
          ))}
        </div>

        {/* Right Detail Inspection */}
        <div className="lg:col-span-8">
          <div className="glass-card border-rose-500/30 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="badge badge-rose text-xs mb-1">
                  Tweet ID: {current.tweet_id} • {current.error_type}
                </span>
                <h3 className="text-base font-bold text-white">{current.title}</h3>
              </div>
            </div>

            {/* Input Message */}
            <div className="space-y-1">
              <span className="text-xs font-semibold text-slate-400">Customer Tweet Message:</span>
              <p className="text-sm text-slate-100 bg-slate-950 p-3 rounded-lg border border-slate-800 font-medium">
                "{current.text}"
              </p>
            </div>

            {/* Ground Truth vs System Output Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-slate-950/80 p-3 rounded-lg border border-emerald-500/30 space-y-1">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">
                  Ground Truth (Human Label)
                </span>
                <div className="text-xs text-slate-300 space-y-0.5 font-mono">
                  <p>Intent: <span className="text-emerald-300 font-semibold">{current.true_intent}</span></p>
                  <p>Ideal Action: <span className="text-emerald-300 font-semibold uppercase">{current.true_action}</span></p>
                </div>
              </div>

              <div className="bg-slate-950/80 p-3 rounded-lg border border-rose-500/30 space-y-1">
                <span className="text-xs font-bold text-rose-400 uppercase tracking-wider block">
                  System Prediction
                </span>
                <div className="text-xs text-slate-300 space-y-0.5 font-mono">
                  <p>Predicted Intent: <span className="text-rose-300 font-semibold">{current.pred_intent}</span></p>
                  <p>Predicted Action: <span className="text-rose-300 font-semibold uppercase">{current.pred_action}</span></p>
                </div>
              </div>
            </div>

            {/* Root Cause Hypothesis */}
            <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider block">
                Root Cause Hypothesis
              </span>
              <p className="text-xs text-slate-300 leading-relaxed">
                {current.hypothesis}
              </p>
            </div>

            {/* Proposed Mitigation */}
            <div className="bg-slate-950 p-3.5 rounded-lg border border-blue-500/30 space-y-1">
              <span className="text-xs font-bold text-blue-400 uppercase tracking-wider block">
                Proposed Mitigation Strategy
              </span>
              <p className="text-xs text-slate-300 leading-relaxed">
                {current.mitigation}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
