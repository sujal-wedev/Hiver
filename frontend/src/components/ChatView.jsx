import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';

const PRESETS = [
  { label: 'Delayed package', text: 'Where is my package? The tracking has been stuck on carrier facility for 3 days!', thread: 1 },
  { label: 'Missing refund', text: "I returned my item 2 weeks ago via UPS drop-off and still haven't received my refund!", thread: 1 },
  { label: 'Double charge', text: 'You charged my credit card twice for order #112-98421! Please issue a refund immediately.', thread: 1 },
  { label: 'Account locked', text: 'I am locked out of my Amazon account and not receiving the 2FA verification code on my phone.', thread: 1 },
  { label: 'Damaged item', text: 'The box arrived today but the glass blender inside was completely shattered. I need a replacement!', thread: 1 },
  { label: 'Legal threat', text: 'I am contacting my attorney and filing a lawsuit against Amazon for fraudulent charges!', thread: 1 },
];

/* ── Typing dots indicator ── */
function TypingIndicator() {
  return (
    <div className="flex items-start gap-2.5 animate-fade-up">
      <div className="w-7 h-7 rounded-full bg-amber-500 flex items-center justify-center text-neutral-950 text-[10px] font-bold shrink-0">
        AH
      </div>
      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-neutral-400 dot-1" />
        <span className="w-1.5 h-1.5 rounded-full bg-neutral-400 dot-2" />
        <span className="w-1.5 h-1.5 rounded-full bg-neutral-400 dot-3" />
      </div>
    </div>
  );
}

/* ── Single agent message ── */
function AgentBubble({ data }) {
  const [open, setOpen] = useState(false);
  const isEscalate = data.decision === 'escalate';

  return (
    <div className="flex items-start gap-2.5 animate-fade-up max-w-[85%]">
      <div className="w-7 h-7 rounded-full bg-amber-500 flex items-center justify-center text-neutral-950 text-[10px] font-bold shrink-0 mt-0.5">
        AH
      </div>

      <div className="space-y-1.5 min-w-0">
        {/* Reply text */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-2xl rounded-tl-sm px-4 py-3 text-[13px] leading-relaxed text-neutral-200">
          {data.reply}
        </div>

        {/* Compact badges row */}
        <div className="flex items-center gap-2 flex-wrap px-1">
          <span className="text-[11px] font-medium text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full">
            {data.intent} · {((data.confidence || 0.85) * 100).toFixed(0)}%
          </span>
          <span
            className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${
              isEscalate
                ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
                : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
            }`}
          >
            {isEscalate ? 'Escalate' : 'Auto-handle'}
          </span>

          <button
            onClick={() => setOpen((v) => !v)}
            className="ml-auto text-[11px] text-neutral-500 hover:text-neutral-300 flex items-center gap-0.5 transition-colors"
          >
            {open ? (
              <>Hide details <ChevronUp className="w-3 h-3" /></>
            ) : (
              <>Details <ChevronDown className="w-3 h-3" /></>
            )}
          </button>
        </div>

        {/* Collapsible details */}
        {open && (
          <div className="animate-fade-up bg-neutral-900/60 border border-neutral-800 rounded-xl px-4 py-3 space-y-2.5 text-[11px] text-neutral-400">
            <div>
              <span className="text-neutral-500 uppercase tracking-wider text-[10px]">Decision reason</span>
              <p className="text-neutral-300 mt-0.5">{data.reason}</p>
            </div>
            <div>
              <span className="text-neutral-500 uppercase tracking-wider text-[10px]">Hallucination check</span>
              <p className={`mt-0.5 ${data.hallucination_detected ? 'text-rose-400' : 'text-emerald-400'}`}>
                {data.hallucination_detected ? 'Flagged' : 'Clean — no fabricated entities'}
              </p>
            </div>
            {data.retrieved_context && (
              <div>
                <span className="text-neutral-500 uppercase tracking-wider text-[10px]">Retrieved context</span>
                <pre className="mt-1 text-[10px] text-neutral-400 bg-neutral-950 border border-neutral-800 rounded-lg p-2.5 max-h-28 overflow-y-auto whitespace-pre-wrap font-mono">
                  {data.retrieved_context}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── User message ── */
function UserBubble({ text, thread }) {
  return (
    <div className="flex justify-end animate-fade-up">
      <div className="max-w-[75%] space-y-1">
        <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-[13px] leading-relaxed">
          {text}
        </div>
        {thread > 1 && (
          <p className="text-[10px] text-neutral-600 text-right pr-1">thread turn {thread}</p>
        )}
      </div>
    </div>
  );
}

/* ── Main ChatView ── */
export default function ChatView({ onProcess, loading }) {
  const [input, setInput] = useState('');
  const [thread, setThread] = useState(1);
  const [messages, setMessages] = useState([]);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  /* ── Send handler: push user msg, call API, push agent msg ── */
  const send = useCallback(
    async (text, threadLen) => {
      const trimmed = (text || input).trim();
      const tl = threadLen ?? thread;
      if (!trimmed || loading) return;

      const userMsg = { id: Date.now(), role: 'user', text: trimmed, thread: tl };

      setMessages((prev) => [...prev, userMsg]);
      setInput('');

      try {
        const result = await onProcess(trimmed, tl);
        if (result) {
          setMessages((prev) => [
            ...prev,
            { id: Date.now() + 1, role: 'agent', data: result },
          ]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            role: 'agent',
            data: {
              reply: 'Something went wrong. Please try again.',
              intent: 'error',
              confidence: 0,
              decision: 'escalate',
              reason: 'Pipeline error',
              hallucination_detected: false,
              hallucination_flags: [],
              retrieved_context: '',
            },
          },
        ]);
      }
    },
    [input, thread, loading, onProcess]
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    send();
  };

  const handlePreset = (p) => {
    setInput(p.text);
    setThread(p.thread);
    send(p.text, p.thread);
  };

  const clearChat = () => setMessages([]);

  return (
    <div className="flex flex-col h-full">
      {/* ── Messages area ── */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-5 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-5 py-16">
            <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 text-sm font-bold">
              AH
            </div>
            <div className="space-y-1.5">
              <h2 className="text-base font-semibold text-neutral-200">AmazonHelp AI Agent</h2>
              <p className="text-xs text-neutral-500 max-w-xs">
                Type a customer message or pick a preset below to see the AI support pipeline in action.
              </p>
            </div>
            {/* Preset chips */}
            <div className="flex flex-wrap justify-center gap-2 max-w-lg">
              {PRESETS.map((p) => (
                <button
                  key={p.label}
                  onClick={() => handlePreset(p)}
                  className="text-[11px] px-3 py-1.5 rounded-full border border-neutral-800 text-neutral-400 hover:text-neutral-200 hover:border-neutral-600 transition-colors"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) =>
          msg.role === 'user' ? (
            <UserBubble key={msg.id} text={msg.text} thread={msg.thread} />
          ) : (
            <AgentBubble key={msg.id} data={msg.data} />
          )
        )}

        {loading && <TypingIndicator />}
        <div ref={endRef} />
      </div>

      {/* ── Bottom input bar ── */}
      <div className="border-t border-neutral-800/60 bg-neutral-950 px-4 sm:px-6 py-3">
        {/* Preset chips — show when there's a conversation */}
        {messages.length > 0 && (
          <div className="flex items-center gap-2 mb-2.5 overflow-x-auto pb-1">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => handlePreset(p)}
                className="text-[10px] px-2.5 py-1 rounded-full border border-neutral-800 text-neutral-500 hover:text-neutral-300 hover:border-neutral-600 transition-colors whitespace-nowrap shrink-0"
              >
                {p.label}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a customer message…"
              className="w-full bg-neutral-900 border border-neutral-800 rounded-xl px-4 py-2.5 text-sm text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-neutral-600 resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
          </div>

          {/* Thread selector */}
          <select
            value={thread}
            onChange={(e) => setThread(Number(e.target.value))}
            className="bg-neutral-900 border border-neutral-800 rounded-lg px-2 py-2.5 text-[11px] text-neutral-400 focus:outline-none"
          >
            <option value={1}>Turn 1</option>
            <option value={2}>Turn 2</option>
            <option value={3}>Turn 3</option>
            <option value={4}>Turn 4+</option>
          </select>

          {/* Send */}
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-800 disabled:text-neutral-600 text-white rounded-xl p-2.5 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>

          {/* Clear */}
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearChat}
              className="text-neutral-600 hover:text-neutral-400 p-2.5 transition-colors"
              title="Clear chat"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
