import React from 'react';

export const PHASES = [
  { id: '01', key: 'phase_01_input', label: '01 Input', shortTitle: 'Input' },
  { id: '02', key: 'phase_02_parse', label: '02 Parse', shortTitle: 'Dependency Parse' },
  { id: '03', key: 'phase_03_relations', label: '03 Relations', shortTitle: 'Semantic Relations' },
  { id: '04', key: 'phase_04_match', label: '04 Match', shortTitle: 'Bipartite Match' },
  { id: '05', key: 'phase_05_entailment', label: '05 Entailment', shortTitle: 'Textual Entailment' },
  { id: '06', key: 'phase_06_additional', label: '06 Additional', shortTitle: 'Unmatched Info' },
  { id: '07', key: 'phase_07_score', label: '07 Score', shortTitle: 'Scoring & Trace' },
];

export default function PhaseNav({ activePhase, onSelectPhase, isAnalysisActive }) {
  return (
    <div className="w-full py-2 px-6 flex items-center justify-center border-b border-slate-200/60 bg-white/70 backdrop-blur-xs">
      <div className="flex items-center gap-1 sm:gap-2 flex-wrap justify-center text-xs font-mono">
        {PHASES.map((phase, index) => {
          const isActive = activePhase === phase.id;
          const isAvailable = isAnalysisActive || phase.id === '01';

          return (
            <React.Fragment key={phase.id}>
              <button
                onClick={() => isAvailable && onSelectPhase(phase.id)}
                disabled={!isAvailable}
                className={`px-3 py-1 rounded-full transition-all flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-indigo-600 text-white font-medium shadow-xs ring-2 ring-indigo-200/50'
                    : isAvailable
                    ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 cursor-pointer'
                    : 'text-slate-300 cursor-not-allowed'
                }`}
              >
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                )}
                <span>{phase.label}</span>
              </button>

              {index < PHASES.length - 1 && (
                <span className="text-slate-300 select-none text-[10px]">→</span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
