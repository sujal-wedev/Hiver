import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Sparkles, RefreshCw, AlertTriangle, CheckCircle2, MessageSquare, 
  ShieldAlert, BookOpen, Layers, Zap, User, Bot, ChevronDown, ChevronUp, 
  Check, ArrowRight, CornerDownLeft, ShieldCheck, FileText, Search
} from 'lucide-react';

export default function SandboxTab({ samples, onProcess, loading, result }) {
  const [inputMessage, setInputMessage] = useState(
    "Where is my package? The tracking has been stuck on carrier facility for 3 days!"
  );
  const [threadLength, setThreadLength] = useState(1);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'system',
      text: 'Welcome to the AmazonHelp AI Support Agent Live Sandbox. Pick a preset inquiry from the sidebar or type a customer tweet below to watch the 4-stage RAG triage pipeline execute in real time.',
      timestamp: 'Just now'
    }
  ]);
  const [showInspectionMap, setShowInspectionMap] = useState({});

  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // When a new result comes from props, append user message and agent message
  useEffect(() => {
    if (result && !loading) {
      const userMsgId = `user-${Date.now()}`;
      const agentMsgId = `agent-${Date.now()}`;
      
      const newMessages = [
        ...messages,
        {
          id: agentMsgId,
          sender: 'agent',
          data: result,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ];
      setMessages(newMessages);
      // Default auto-expand inspection drawer for newest message
      setShowInspectionMap(prev => ({ ...prev, [agentMsgId]: true }));
    }
  }, [result]);

  const handleSelectSample = (sample) => {
    setInputMessage(sample.text);
    setThreadLength(sample.thread_length || 1);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || loading) return;

    const userMsgId = `user-${Date.now()}`;
    const newMsg = {
      id: userMsgId,
      sender: 'user',
      text: inputMessage,
      threadLength,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, newMsg]);
    onProcess(inputMessage, threadLength);
  };

  const toggleInspection = (id) => {
    setShowInspectionMap(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in">
      
      {/* LEFT SIDEBAR: Preset Customer Inquiries & Presets */}
      <div className="lg:col-span-4 space-y-4">
        
        {/* Sidebar Card Header */}
        <div className="glass-card bg-slate-900/90 border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-blue-400" />
              Customer Scenarios
            </h3>
            <span className="badge badge-blue">{samples.length} Presets</span>
          </div>
          <p className="text-xs text-slate-400">
            Click any real-world inquiry scenario to load it into the support chatbot interface:
          </p>
        </div>

        {/* Preset Cards List */}
        <div className="space-y-2 max-h-[620px] overflow-y-auto pr-1">
          {samples.map((sample) => {
            const isEscalationProne = sample.badge.includes('Human') || sample.badge.includes('Billing') || sample.badge.includes('Security');
            return (
              <button
                key={sample.id}
                onClick={() => handleSelectSample(sample)}
                className="w-full text-left p-3.5 rounded-xl bg-slate-900/70 hover:bg-slate-850 border border-slate-800 hover:border-blue-500/40 transition-all group shadow-sm"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-slate-200 group-hover:text-blue-400 transition-colors truncate">
                    {sample.title}
                  </span>
                  <span className={`badge ${isEscalationProne ? 'badge-amber' : 'badge-blue'} text-[10px]`}>
                    {sample.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2 leading-snug font-sans">
                  "{sample.text}"
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* RIGHT MAIN WORKSPACE: Chatbot Interface */}
      <div className="lg:col-span-8 flex flex-col h-[740px] glass-card border-slate-800 p-0 overflow-hidden bg-slate-950/90 shadow-2xl">
        
        {/* Chat Header Bar */}
        <div className="px-6 py-4 border-b border-slate-800/80 bg-slate-900/90 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center font-bold text-slate-950 text-sm shadow-md">
                AH
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-500 border-2 border-slate-900 rounded-full"></span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-sm text-white">@AmazonHelp AI Agent</h3>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full border border-blue-500/20">
                  <CheckCircle2 className="w-3 h-3 text-blue-400" />
                  Verified Brand
                </span>
              </div>
              <p className="text-xs text-slate-400">Autonomous Intent Triage • RAG Retrieval • Escalation Policy</p>
            </div>
          </div>

          <button
            onClick={() => setMessages([messages[0]])}
            className="text-xs text-slate-400 hover:text-slate-200 px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/50 transition-all flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reset Chat
          </button>
        </div>

        {/* Chat Messages Stream Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => {
            if (msg.sender === 'system') {
              return (
                <div key={msg.id} className="flex justify-center my-2">
                  <div className="bg-slate-900/80 border border-slate-800/80 px-4 py-2.5 rounded-2xl text-xs text-slate-400 text-center max-w-lg shadow-sm">
                    {msg.text}
                  </div>
                </div>
              );
            }

            if (msg.sender === 'user') {
              return (
                <div key={msg.id} className="flex justify-end gap-3 items-start animate-fade-in">
                  <div className="space-y-1 max-w-xl">
                    <div className="flex items-center justify-end gap-2 text-xs text-slate-400">
                      <span className="font-mono">Customer (@user)</span>
                      <span>•</span>
                      <span>Thread turn: {msg.threadLength}</span>
                    </div>
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 rounded-2xl rounded-tr-none shadow-lg text-sm leading-relaxed">
                      {msg.text}
                    </div>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 font-bold text-xs shrink-0 mt-5">
                    <User className="w-4 h-4" />
                  </div>
                </div>
              );
            }

            // Agent Message Bubble
            if (msg.sender === 'agent') {
              const data = msg.data || {};
              const isEscalate = data.decision === 'escalate';
              const showDetails = showInspectionMap[msg.id];

              return (
                <div key={msg.id} className="flex gap-3 items-start animate-fade-in">
                  {/* Brand Avatar */}
                  <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center font-bold text-slate-950 text-xs shrink-0 mt-1 shadow-md">
                    AH
                  </div>

                  <div className="space-y-3 max-w-2xl flex-1">
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span className="font-bold text-slate-200">@AmazonHelp Official Agent</span>
                      <span>•</span>
                      <span className="font-mono">{msg.timestamp}</span>
                    </div>

                    {/* Agent Reply Box */}
                    <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl rounded-tl-none shadow-xl space-y-3">
                      <div className="text-sm font-medium text-slate-100 leading-relaxed">
                        {data.reply}
                      </div>

                      {/* Summary Badges Bar */}
                      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80">
                        <span className="badge badge-blue text-[11px]">
                          Intent: {data.intent} ({((data.confidence || 0.85)*100).toFixed(0)}%)
                        </span>
                        <span className={`badge ${isEscalate ? 'badge-amber' : 'badge-emerald'} text-[11px]`}>
                          {isEscalate ? 'ESCALATE TO HUMAN' : 'AUTO-HANDLE'}
                        </span>
                        <span className={`badge ${data.hallucination_detected ? 'badge-rose' : 'badge-purple'} text-[11px]`}>
                          {data.hallucination_detected ? 'Hallucination Flagged' : 'Zero Hallucinations Verified'}
                        </span>

                        <button
                          onClick={() => toggleInspection(msg.id)}
                          className="ml-auto text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 transition-colors"
                        >
                          {showDetails ? (
                            <>Hide RAG Pipeline Inspection <ChevronUp className="w-3.5 h-3.5" /></>
                          ) : (
                            <>Inspect 4-Stage RAG Pipeline <ChevronDown className="w-3.5 h-3.5" /></>
                          )}
                        </button>
                      </div>

                      {/* Expandable 4-Stage RAG Inspection Card */}
                      {showDetails && (
                        <div className="mt-3 pt-3 border-t border-slate-800 space-y-3 animate-fade-in bg-slate-950/80 p-4 rounded-xl border border-slate-800">
                          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                            <Layers className="w-4 h-4 text-blue-400" />
                            4-Stage Autonomous Pipeline Diagnostic Breakdown
                          </h4>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            {/* Stage 1: Intent Triage */}
                            <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 space-y-1">
                              <span className="font-bold text-blue-400 block">1. Intent Classification</span>
                              <p className="text-slate-300 font-mono">`{data.intent}`</p>
                              <p className="text-[11px] text-slate-400">Confidence: {((data.confidence || 0.85)*100).toFixed(0)}%</p>
                            </div>

                            {/* Stage 2: Escalation Guardrail */}
                            <div className={`p-3 rounded-lg border space-y-1 ${isEscalate ? 'bg-amber-950/20 border-amber-500/40' : 'bg-emerald-950/20 border-emerald-500/40'}`}>
                              <span className={`font-bold block ${isEscalate ? 'text-amber-400' : 'text-emerald-400'}`}>
                                2. Escalation Policy Rationale
                              </span>
                              <p className="text-slate-200 text-[11px] leading-snug">{data.reason}</p>
                            </div>
                          </div>

                          {/* Stage 3: RAG Few-Shot Context */}
                          <div className="space-y-1">
                            <span className="font-bold text-indigo-400 text-xs block">3. Grounded Few-Shot Retrieval Context (MiniLM Cosine Similarity)</span>
                            <pre className="text-[11px] text-slate-300 bg-slate-950 p-2.5 rounded-lg border border-slate-800 max-h-28 overflow-y-auto whitespace-pre-wrap font-mono">
                              {data.retrieved_context || "No historical resolution context available."}
                            </pre>
                          </div>

                          {/* Stage 4: Hallucination Verification */}
                          <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800">
                            <span className="text-slate-400">4. Hallucination Safeguard Check:</span>
                            <span className={`font-bold ${data.hallucination_detected ? 'text-rose-400' : 'text-emerald-400'}`}>
                              {data.hallucination_detected ? 'Entity Fabrications Detected' : 'Clean (No Fabricated IDs/Amounts)'}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            }

            return null;
          })}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex gap-3 items-start animate-fade-in">
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center font-bold text-slate-950 text-xs shrink-0">
                AH
              </div>
              <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl rounded-tl-none text-xs text-slate-400 flex items-center gap-3">
                <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
                <span>@AmazonHelp AI Agent is executing intent triage & retrieving grounded resolution context...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Bottom Interactive Chat Input Bar */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/90">
          <form onSubmit={handleSubmit} className="space-y-3">
            
            <div className="flex items-center justify-between gap-3 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-3.5 h-3.5 text-blue-400" />
                <span className="font-semibold text-slate-300">Customer Tweet Prompt</span>
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5">
                  <span>Thread Turn:</span>
                  <select
                    value={threadLength}
                    onChange={(e) => setThreadLength(Number(e.target.value))}
                    className="bg-slate-950 border border-slate-700 rounded px-2 py-0.5 text-xs text-blue-400 font-semibold focus:outline-none"
                  >
                    <option value={1}>1 (First Contact)</option>
                    <option value={2}>2 (Follow Up)</option>
                    <option value={3}>3 (3rd Attempt)</option>
                    <option value={4}>4+ (Repeat Fatigue)</option>
                  </select>
                </label>
                <span>{inputMessage.length} chars</span>
              </div>
            </div>

            <div className="flex gap-2 items-center">
              <textarea
                rows={2}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type a customer support message (e.g. 'Where is my order?')..."
                className="flex-1 bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none font-sans"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="btn-primary h-full px-6 rounded-xl flex items-center justify-center shrink-0"
              >
                {loading ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Send
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

      </div>

    </div>
  );
}
