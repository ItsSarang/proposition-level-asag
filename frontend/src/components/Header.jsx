const PHASES = [
  { id: '01', shortName: 'Input', label: '01 Input' },
  { id: '02', shortName: 'Dependencies', label: '02 Dependencies' },
  { id: '03', shortName: 'Propositions', label: '03 Propositions' },
  { id: '04', shortName: 'Alignment', label: '04 Alignment' },
  { id: '05', shortName: 'Entailment', label: '05 Entailment' },
  { id: '06', shortName: 'Additional', label: '06 Additional' },
  { id: '07', shortName: 'Scoring', label: '07 Scoring' },
];

export default function Header({
  activeTab = 'workbench',
  onTabChange,
  activePhase = '01',
  onPhaseChange,
  hasAnalysis = false,
}) {
  return (
    <header className="sticky top-0 z-50 w-full bg-[#f2eee5]/95 backdrop-blur-md border-b border-[#dfd8c8] select-none">
      <div className="w-full px-6 h-13 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5 shrink-0">
          <span className="font-bold text-[#1e1c19] text-[16px] tracking-tight">
            ASAG Lab
          </span>
        </div>

        {activeTab === 'workbench' && (
          <nav className="flex items-center justify-center gap-x-1.5 sm:gap-x-2 text-[12px] font-mono select-none overflow-x-auto py-1">
            {PHASES.map((phase, idx) => {
              const isActive = activePhase === phase.id;
              const isClickable = phase.id === '01' || phase.id === '02' || hasAnalysis;

              return (
                <div key={phase.id} className="flex items-center gap-x-1.5 sm:gap-x-2 shrink-0">
                  {isActive ? (
                    <button
                      type="button"
                      onClick={() => onPhaseChange && onPhaseChange(phase.id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#e6e0d2] border border-[#d2c9b6] text-indigo-900 font-semibold tracking-tight shadow-xs cursor-pointer"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-700 animate-pulse" />
                      <span>{phase.label}</span>
                    </button>
                  ) : isClickable ? (
                    <button
                      type="button"
                      onClick={() => onPhaseChange && onPhaseChange(phase.id)}
                      className="px-2 py-0.5 rounded text-[#706b63] hover:text-[#1e1c19] transition-colors cursor-pointer"
                    >
                      {phase.label}
                    </button>
                  ) : (
                    <span className="px-2 py-0.5 text-[#b5ab9b] select-none cursor-default">
                      {phase.label}
                    </span>
                  )}

                  {idx < PHASES.length - 1 && (
                    <span className="text-[#b5ab9b] font-mono text-[11px] select-none mx-0.5">
                      →
                    </span>
                  )}
                </div>
              );
            })}
          </nav>
        )}

        <nav className="flex items-center shrink-0">
          <div className="inline-flex items-center bg-[#e6e0d2] p-0.5 rounded-xl border border-[#d8d0bf]">
            <button
              type="button"
              onClick={() => onTabChange && onTabChange('workbench')}
              className={`px-3.5 py-1 rounded-lg text-[12px] font-mono tracking-wide transition-all cursor-pointer ${
                activeTab === 'workbench'
                  ? 'bg-[#faf8f4] text-[#1e1c19] font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19] font-normal'
              }`}
            >
              Workbench
            </button>
            <button
              type="button"
              onClick={() => onTabChange && onTabChange('research')}
              className={`px-3.5 py-1 rounded-lg text-[12px] font-mono tracking-wide transition-all cursor-pointer ${
                activeTab === 'research'
                  ? 'bg-[#faf8f4] text-[#1e1c19] font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19] font-normal'
              }`}
            >
              Research
            </button>
          </div>
        </nav>
      </div>
    </header>
  );
}
