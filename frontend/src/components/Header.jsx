import React from 'react';

export default function Header({ currentTab, onTabChange, hasActiveAnalysis, onResetWorkbench }) {
  return (
    <header className="sticky top-0 z-50 w-full bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-6 py-3.5 flex items-center justify-between">
      {/* Brand */}
      <div 
        className="flex items-center gap-3 cursor-pointer group"
        onClick={() => {
          onTabChange('workbench');
          if (onResetWorkbench) onResetWorkbench();
        }}
      >
        <div className="w-8 h-8 rounded-lg bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-600 font-semibold shadow-xs">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 3v18" />
            <path d="M3 12h18" />
            <circle cx="12" cy="12" r="3" fill="currentColor" />
          </svg>
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-900 tracking-tight text-base group-hover:text-indigo-600 transition-colors">
              ASAG Lab
            </span>
            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              V5 Final
            </span>
          </div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400">
            Semantic + Dependency Analysis
          </span>
        </div>
      </div>

      {/* Primary Navigation */}
      <nav className="flex items-center gap-8 text-xs font-mono font-medium tracking-wide">
        <button
          onClick={() => onTabChange('workbench')}
          className={`py-1 relative transition-colors ${
            currentTab === 'workbench'
              ? 'text-slate-900 font-semibold'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          WORKBENCH
          {currentTab === 'workbench' && (
            <span className="absolute -bottom-4 left-0 right-0 h-0.5 bg-indigo-600 rounded-full" />
          )}
        </button>

        <button
          onClick={() => onTabChange('research')}
          className={`py-1 relative transition-colors ${
            currentTab === 'research'
              ? 'text-slate-900 font-semibold'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          RESEARCH
          {currentTab === 'research' && (
            <span className="absolute -bottom-4 left-0 right-0 h-0.5 bg-indigo-600 rounded-full" />
          )}
        </button>

        <button
          onClick={() => onTabChange('docs')}
          className={`py-1 relative transition-colors ${
            currentTab === 'docs'
              ? 'text-slate-900 font-semibold'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          DOCS
          {currentTab === 'docs' && (
            <span className="absolute -bottom-4 left-0 right-0 h-0.5 bg-indigo-600 rounded-full" />
          )}
        </button>
      </nav>
    </header>
  );
}
