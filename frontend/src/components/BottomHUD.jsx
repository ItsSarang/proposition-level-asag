import { ChevronRight } from 'lucide-react';
import CanvasControls from './CanvasControls';

const PHASES = [
  { id: '01', name: 'Input', question: 'What was asked?' },
  { id: '02', name: 'Dependencies', question: 'How is the answer structured?' },
  { id: '03', name: 'Propositions', question: 'What information was extracted?' },
  { id: '04', name: 'Alignment', question: 'What matches the reference?' },
  { id: '05', name: 'Assessment', question: 'Does it entail, contradict, or add information?' },
  { id: '06', name: 'Result', question: 'How did this produce the grade?' },
];

export default function BottomHUD({
  activePhase,
  onPhaseChange,
  hasAnalysis = false,
  hasCanvas = false,
  zoom = 1,
  onZoomIn,
  onZoomOut,
  onResetFit,
}) {
  return (
    <div className="absolute bottom-5 inset-x-6 z-40 flex items-center pointer-events-none select-none">
      <div className="flex items-center pointer-events-auto">
        {hasCanvas && (
          <CanvasControls
            zoom={zoom}
            onZoomIn={onZoomIn}
            onZoomOut={onZoomOut}
            onResetFit={onResetFit}
          />
        )}
      </div>

      <div className="absolute left-1/2 -translate-x-1/2 flex items-center pointer-events-auto">
        <div className="h-9 p-[3px] flex items-center gap-0.5 sm:gap-1 bg-[#f4f0e8]/95 backdrop-blur-md rounded-xl border border-[#dfd8c8] shadow-xs text-xs font-mono">
          {PHASES.map((phase, idx) => {
            const isActive = activePhase === phase.id;
            const isClickable = phase.id === '01' || hasAnalysis;

            return (
              <div key={phase.id} className="relative group flex items-center">
                <div className="absolute bottom-full mb-2.5 left-1/2 -translate-x-1/2 hidden group-hover:flex flex-col items-center pointer-events-none z-50">
                  <div className="bg-[#1e1c19] text-[#f7f4ed] px-3 py-1.5 rounded-lg shadow-lg text-center whitespace-nowrap">
                    <div className="text-[10px] font-mono text-indigo-300 font-bold uppercase tracking-wider">
                      {phase.id} {phase.name}
                    </div>
                    <div className="text-[11.5px] font-sans font-medium text-[#fdfcf9]">
                      {phase.question}
                    </div>
                  </div>
                  <div className="w-2 h-2 bg-[#1e1c19] rotate-45 -mt-1" />
                </div>

                {isActive ? (
                  <button
                    type="button"
                    onClick={() => onPhaseChange && onPhaseChange(phase.id)}
                    className="h-7 px-3 inline-flex items-center justify-center rounded-lg bg-[#fdfcf9] border border-[#d8d0bf] shadow-2xs cursor-pointer transition-all"
                  >
                    <span className="font-mono text-[11px] font-semibold text-indigo-900/80 mr-1.5 leading-none">
                      {phase.id}
                    </span>
                    <span className="font-sans text-[12px] font-semibold text-[#1e1c19] tracking-normal leading-none">
                      {phase.name}
                    </span>
                  </button>
                ) : isClickable ? (
                  <button
                    type="button"
                    onClick={() => onPhaseChange && onPhaseChange(phase.id)}
                    className="h-7 px-2.5 inline-flex items-center justify-center rounded-lg border border-transparent text-[#706b63] hover:text-[#1e1c19] hover:bg-[#eae4d6]/70 transition-all cursor-pointer font-medium"
                  >
                    <span className="font-mono text-[11px] text-[#8c8477] mr-1.5 leading-none">
                      {phase.id}
                    </span>
                    <span className="font-sans text-[12px] font-medium leading-none">
                      {phase.name}
                    </span>
                  </button>
                ) : (
                  <span className="h-7 px-2.5 inline-flex items-center justify-center rounded-lg text-[#b5ab9b] select-none cursor-not-allowed font-normal">
                    <span className="font-mono text-[11px] mr-1.5 leading-none">
                      {phase.id}
                    </span>
                    <span className="font-sans text-[12px] font-normal leading-none">
                      {phase.name}
                    </span>
                  </span>
                )}

                {idx < PHASES.length - 1 && (
                  <ChevronRight size={14} className="text-[#a89e8f] shrink-0 select-none mx-0.5" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
