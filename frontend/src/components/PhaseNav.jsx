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
    <div className="w-full py-2.5 px-6 flex items-center justify-center">
      <div className="inline-flex items-center gap-1.5 sm:gap-2.5 px-4 py-1.5 rounded-full border border-slate-200/80 bg-white/90 shadow-xs text-xs font-mono backdrop-blur-sm">
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
                    ? phase.id === '01'
                      ? 'bg-indigo-100 text-indigo-700 font-semibold'
                      : 'bg-indigo-700 text-white font-medium shadow-xs'
                    : isAvailable
                    ? 'text-slate-500 hover:text-slate-800 cursor-pointer'
                    : 'text-slate-400 cursor-not-allowed opacity-60'
                }`}
              >
                {isActive && (
                  <span className={`w-1.5 h-1.5 rounded-full ${phase.id === '01' ? 'bg-indigo-600' : 'bg-white'}`} />
                )}
                <span>{phase.label}</span>
              </button>

              {index < PHASES.length - 1 && (
                <span className="text-slate-300 select-none text-[11px]">→</span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
