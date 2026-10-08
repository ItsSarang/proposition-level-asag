import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function DetailPanel({
  selectedNode,
  nodes = [],
  onSelectNodeIndex,
}) {
  if (!selectedNode) {
    return (
      <aside className="hidden lg:flex flex-col h-full w-80 min-w-80 shrink-0 bg-[#f4f0e8] border-l border-[#dfd8c8] p-6 text-[#7a7266] text-xs font-mono">
        Select any dependency node to inspect syntactic and lexical details.
      </aside>
    );
  }

  const currentIndex = nodes.findIndex((n) => n.id === selectedNode.id);
  const totalNodes = nodes.length;

  return (
    <aside className="hidden lg:flex flex-col h-full w-80 min-w-80 shrink-0 bg-[#f4f0e8] border-l border-[#dfd8c8] select-none">
      <div className="p-6 flex-1 overflow-y-auto flex flex-col">
        <div>
          <div className="mb-1.5">
            <span className="text-[12px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold">
              SYNTACTIC NODE
            </span>
          </div>
          <h3 className="text-[26px] font-bold text-[#1e1c19] tracking-tight">
            {selectedNode.text}
          </h3>
          <div className="text-[13px] font-mono text-[#706b63] mt-1">
            Lemma: <span className="text-indigo-800 font-medium">{selectedNode.lemma || selectedNode.text.toLowerCase()}</span>
          </div>
        </div>

        <div className="border-t border-[#dfd8c8] my-4" />

        <div>
          <div className="text-[12px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold mb-2.5">
            LINGUISTIC PROPERTIES
          </div>
          <div className="space-y-2 text-[13px] font-mono">
            <div className="flex items-center justify-between">
              <span className="text-[#706b63]">POS Tag</span>
              <span className="text-[#1e1c19] font-semibold">{selectedNode.pos}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#706b63]">Dependency</span>
              <span className="text-indigo-800 font-semibold">{selectedNode.dep}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#706b63]">Governor</span>
              <span className="text-[#1e1c19] font-medium">{selectedNode.headText || 'ROOT'}</span>
            </div>
          </div>
        </div>

        <div className="border-t border-[#dfd8c8] my-4" />

        <div>
          <div className="text-[12px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold mb-2">
            RELATION
          </div>
          <div className="font-mono text-[14px] text-indigo-900 font-semibold">
            {selectedNode.pathTrace || `${selectedNode.dep}(${selectedNode.headText || 'ROOT'}, ${selectedNode.text})`}
          </div>
        </div>

        <div className="border-t border-[#dfd8c8] my-4" />

        <div>
          <div className="text-[12px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold mb-2">
            MEANING
          </div>
          <p className="text-[14px] text-[#343029] leading-relaxed font-sans">
            {selectedNode.meaning || selectedNode.description}
          </p>
        </div>
      </div>

      <div className="border-t border-[#dfd8c8] px-5 py-3 flex items-center justify-between text-[12px] font-mono text-[#706b63] bg-[#ede8dc]/60">
        <button
          type="button"
          disabled={currentIndex <= 0}
          onClick={() => currentIndex > 0 && onSelectNodeIndex(currentIndex - 1)}
          className="flex items-center gap-1 hover:text-[#1e1c19] transition-colors disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
        >
          <ChevronLeft size={14} />
          <span>Prev</span>
        </button>

        <span className="text-[#7a7266]">
          {currentIndex >= 0 ? currentIndex + 1 : 1} of {totalNodes} Nodes
        </span>

        <button
          type="button"
          disabled={currentIndex >= totalNodes - 1}
          onClick={() => currentIndex < totalNodes - 1 && onSelectNodeIndex(currentIndex + 1)}
          className="flex items-center gap-1 hover:text-[#1e1c19] transition-colors disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
        >
          <span>Next</span>
          <ChevronRight size={14} />
        </button>
      </div>
    </aside>
  );
}
