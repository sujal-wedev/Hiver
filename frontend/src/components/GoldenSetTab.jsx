import React from 'react';
import { Database, CheckCircle2, Layers, Tag, BookOpen } from 'lucide-react';

export default function GoldenSetTab() {
  const taxonomy = [
    { intent: "order_status_delivery", desc: "Package tracking, shipment status, delayed delivery, or lost in transit." },
    { intent: "refund_return", desc: "Return item requests, return label status, refund timeline or status." },
    { intent: "billing_dispute", desc: "Double charges, unauthorized transactions, or billing errors." },
    { intent: "account_access", desc: "2FA SMS code failures, password reset problems, account lockouts." },
    { intent: "product_issue", desc: "Damaged, broken glass, defective items, missing parts, wrong item delivered." },
    { intent: "app_website_bug", desc: "App crashes, checkout HTTP 500 errors, cart glitches, website bugs." },
    { intent: "cancellation", desc: "Cancel order before dispatch, cancel Prime subscription membership." },
    { intent: "general_complaint_vent", desc: "Anger, frustration, or venting without specific actionable request." },
    { intent: "other_unclear", desc: "Vague, incomplete, or off-topic customer messages requiring clarification." }
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Banner */}
      <div className="glass-card bg-gradient-to-r from-slate-900 via-emerald-950/40 to-slate-900 border-emerald-500/20">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-emerald-400" />
              Golden Evaluation Dataset & Taxonomy Strategy
            </h2>
            <p className="text-sm text-slate-300 mt-1">
              Hand-labeled evaluation dataset (N=170) built to benchmark intent classification & escalation policy safety.
            </p>
          </div>
          <div className="badge badge-emerald px-3 py-1.5 text-xs">
            170 Hand-Labeled Items
          </div>
        </div>
      </div>

      {/* Sampling Strategy Overview */}
      <div className="glass-card">
        <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-400" />
          Sampling & Labeling Methodology
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed space-y-2">
          The golden dataset was constructed by stratified random sampling of 170 single-turn <code>AmazonHelp</code> customer messages from the reconstructed Twitter dataset (<code>twcs.csv</code>). 
          Each sample was individually annotated with a ground-truth intent label based on our 9-intent taxonomy, ideal escalation decision (<code>auto_handle</code> vs <code>escalate</code>), and evaluated across groundedness, tone, and actionability to calibrate the automated LLM Judge.
        </p>
      </div>

      {/* Taxonomy Definitions Table */}
      <div className="glass-card">
        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <Tag className="w-5 h-5 text-indigo-400" />
          Defined Intent Taxonomy (9 Intent Categories)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {taxonomy.map((item, idx) => (
            <div key={idx} className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-1">
              <span className="text-xs font-mono font-bold text-blue-300 block">
                `{item.intent}`
              </span>
              <p className="text-xs text-slate-300">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
