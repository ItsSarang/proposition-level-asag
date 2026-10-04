import React from 'react';

export default function Header({ currentTab, onTabChange, hasActiveAnalysis, onResetWorkbench }) {
  return (
    <header className="sticky top-0 z-50 w-full bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-8 py-3.5 flex items-center justify-between">
      {/* Brand */}
      <div 
        className="flex items-center gap-3 cursor-pointer"
        onClick={() => {
          onTabChange('workbench');
          if (onResetWorkbench) onResetWorkbench();
        }}
      >
        <span className="font-bold text-slate-900 tracking-tight text-base">
          ASAG Lab
        </span>
        <span className="text-xs font-mono text-slate-500">
          Semantic + Dependency Analysis
        </span>
      </div>

      {/* Primary Navigation */}
      <nav className="flex items-center gap-7 text-xs font-mono font-medium tracking-wider">
        <button
          onClick={() => onTabChange('workbench')}
          className={`pb-1 transition-colors cursor-pointer ${
            currentTab === 'workbench'
              ? 'text-slate-900 font-semibold border-b-2 border-slate-900'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          WORKBENCH
        </button>

        <button
          onClick={() => onTabChange('research')}
          className={`pb-1 transition-colors cursor-pointer ${
            currentTab === 'research'
              ? 'text-slate-900 font-semibold border-b-2 border-slate-900'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          RESEARCH
        </button>

        <button
          onClick={() => onTabChange('docs')}
          className={`pb-1 transition-colors cursor-pointer ${
            currentTab === 'docs'
              ? 'text-slate-900 font-semibold border-b-2 border-slate-900'
              : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          DOCS
        </button>
      </nav>
    </header>
  );
}
