export default function AnswerBar({
  parseMode,
  onSwitchParseMode,
  sentenceCount,
  activeSentenceIndex,
  onSwitchSentence,
  textTokens = [],
  nodes = [],
  selectedNode,
  onSelectNode,
}) {
  return (
    <div className="w-full bg-[#f4f0e8]/95 border-b border-[#dfd8c8] px-6 py-3 select-none shrink-0 shadow-2xs">
      <div className="flex items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2.5">
          <div className="inline-flex items-center bg-[#e6e0d2] p-0.5 rounded-lg border border-[#d8d0bf] text-[13px] font-mono">
            <button
              type="button"
              onClick={() => onSwitchParseMode('student')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                parseMode === 'student'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Student Answer
            </button>
            <button
              type="button"
              onClick={() => onSwitchParseMode('reference')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                parseMode === 'reference'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Reference Answer
            </button>
          </div>

          {sentenceCount > 1 && (
            <div className="inline-flex items-center bg-[#e6e0d2] p-0.5 rounded-lg border border-[#d8d0bf] text-[12px] font-mono">
              {Array.from({ length: sentenceCount }, (_, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => onSwitchSentence(i)}
                  className={`px-2.5 py-1 rounded-md transition-all cursor-pointer ${
                    activeSentenceIndex === i
                      ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                      : 'text-[#706b63] hover:text-[#1e1c19]'
                  }`}
                >
                  S{i + 1}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="hidden sm:flex items-center gap-1.5 text-[11.5px] font-mono text-[#706b63]">
          <span className="font-semibold text-indigo-900">STRUCTURE</span>
          <span className="text-[#a89e8f]">—</span>
          <span>Parse the answer into syntactic relationships</span>
        </div>
      </div>

      <div className="text-[14px] leading-relaxed text-[#1e1c19] font-sans max-h-20 overflow-y-auto">
        {textTokens.map((tok) => {
          if (!tok.isWord) {
            return (
              <span key={tok.id} className="text-[#423e38] font-normal">
                {tok.raw}
              </span>
            );
          }

          const matchedNode = nodes.find((n) => n.id === tok.nodeId);
          const isSelected = selectedNode?.id === tok.nodeId;

          if (matchedNode) {
            return (
              <button
                key={tok.id}
                type="button"
                onClick={() => onSelectNode(matchedNode)}
                className={`inline-block px-1.5 py-0.5 mx-0.5 rounded text-[13.5px] font-medium transition-colors cursor-pointer border ${
                  isSelected
                    ? 'bg-[#3730a3] border-[#3730a3] text-white font-semibold shadow-xs'
                    : 'bg-[#faf8f4] border-[#dfd8c8] text-[#1e1c19] hover:border-indigo-400 hover:bg-indigo-50/70 hover:text-indigo-900'
                }`}
              >
                {tok.raw}
              </button>
            );
          }

          return (
            <span key={tok.id} className="text-[#423e38]">
              {tok.raw}
            </span>
          );
        })}
      </div>
    </div>
  );
}
