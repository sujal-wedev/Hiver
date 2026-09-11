import React from 'react';

export default function Header({ isBackendLive }) {
  return (
    <header className="border-b border-neutral-800/60 bg-neutral-950 px-5 py-3 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center text-neutral-950 text-xs font-bold">
          AH
        </div>
        <span className="text-sm font-semibold text-neutral-100 tracking-tight">
          AmazonHelp AI
        </span>
      </div>

      {/* Status */}
      <div className="flex items-center gap-2 text-xs text-neutral-500">
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            isBackendLive ? 'bg-emerald-400' : 'bg-neutral-600'
          }`}
        />
        <span>{isBackendLive ? 'Connected' : 'Offline'}</span>
      </div>
    </header>
  );
}
