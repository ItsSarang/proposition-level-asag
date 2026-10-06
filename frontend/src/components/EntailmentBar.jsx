export default function EntailmentBar({
  entailmentFilter = 'ALL',
  onSwitchFilter,
  totalCount = 0,
  entailsCount = 0,
  uncertainCount = 0,
  contradictsCount = 0,
}) {
  return (
    <div className="w-full bg-[#f4f0e8]/95 border-b border-[#dfd8c8] px-6 py-3 select-none shrink-0 shadow-2xs">
      <div className="flex items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2.5">
          <div className="inline-flex items-center bg-[#e6e0d2] p-0.5 rounded-lg border border-[#d8d0bf] text-[13px] font-mono">
            <button
              type="button"
              onClick={() => onSwitchFilter('ALL')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                entailmentFilter === 'ALL'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              All Pairs ({totalCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('ENTAILS')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                entailmentFilter === 'ENTAILS'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Entails ({entailsCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('UNCERTAIN')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                entailmentFilter === 'UNCERTAIN'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Uncertain ({uncertainCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('CONTRADICTS')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                entailmentFilter === 'CONTRADICTS'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Contradicts ({contradictsCount})
            </button>
          </div>
        </div>
      </div>

      <div className="text-[13.5px] leading-relaxed text-[#706b63] font-sans">
        {entailmentFilter === 'ALL' && (
          <span>
            Semantic entailment verification evaluating whether aligned student propositions satisfy, leave uncertain, or contradict reference criteria.
          </span>
        )}
        {entailmentFilter === 'ENTAILS' && (
          <span>
            Aligned propositions where student assertions semantically satisfy and entail the reference requirements.
          </span>
        )}
        {entailmentFilter === 'UNCERTAIN' && (
          <span>
            Aligned propositions with partial lexical or semantic overlap where propositional entailment remains ambiguous.
          </span>
        )}
        {entailmentFilter === 'CONTRADICTS' && (
          <span>
            Aligned propositions demonstrating material divergence or semantic conflict against reference criteria.
          </span>
        )}
      </div>
    </div>
  );
}
