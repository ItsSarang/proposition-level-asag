export default function AssessmentBar({
  activeView = 'entailment',
  onSwitchView,
  entailmentFilter = 'ALL',
  onSwitchEntailmentFilter,
  additionalFilter = 'ALL',
  onSwitchAdditionalFilter,
  totalEntailments = 0,
  entailsCount = 0,
  uncertainEntailCount = 0,
  contradictsCount = 0,
  totalUnmatched = 0,
  correctCount = 0,
  irrelevantCount = 0,
  incorrectCount = 0,
  uncertainAddCount = 0,
}) {
  return (
    <div className="w-full bg-[#f4f0e8]/95 border-b border-[#dfd8c8] px-6 py-3 select-none shrink-0 shadow-2xs">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-1.5 p-0.5 bg-[#e6e0d2] rounded-xl border border-[#d8d0bf] w-fit">
          <button
            type="button"
            onClick={() => onSwitchView && onSwitchView('entailment')}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer ${
              activeView === 'entailment'
                ? 'bg-[#faf8f4] text-[#1e1c19] font-bold shadow-xs'
                : 'text-[#706b63] hover:text-[#1e1c19]'
            }`}
          >
            Matched Entailment ({totalEntailments})
          </button>
          <button
            type="button"
            onClick={() => onSwitchView && onSwitchView('additional')}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-medium transition-all cursor-pointer ${
              activeView === 'additional'
                ? 'bg-[#faf8f4] text-[#1e1c19] font-bold shadow-xs'
                : 'text-[#706b63] hover:text-[#1e1c19]'
            }`}
          >
            Additional Information ({totalUnmatched})
          </button>
        </div>

        {activeView === 'entailment' ? (
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => onSwitchEntailmentFilter('ALL')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                entailmentFilter === 'ALL'
                  ? 'bg-[#1e1c19] text-[#f7f4ed] font-semibold'
                  : 'bg-[#faf8f4] text-[#706b63] hover:text-[#1e1c19] border border-[#dfd8c8]'
              }`}
            >
              All ({totalEntailments})
            </button>
            <button
              type="button"
              onClick={() => onSwitchEntailmentFilter('ENTAILS')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                entailmentFilter === 'ENTAILS'
                  ? 'bg-emerald-800 text-white font-semibold'
                  : 'bg-[#faf8f4] text-emerald-800 hover:bg-emerald-50 border border-emerald-200'
              }`}
            >
              Entails ({entailsCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchEntailmentFilter('UNCERTAIN')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                entailmentFilter === 'UNCERTAIN'
                  ? 'bg-amber-800 text-white font-semibold'
                  : 'bg-[#faf8f4] text-amber-900 hover:bg-amber-50 border border-amber-200'
              }`}
            >
              Uncertain ({uncertainEntailCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchEntailmentFilter('CONTRADICTS')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                entailmentFilter === 'CONTRADICTS'
                  ? 'bg-rose-800 text-white font-semibold'
                  : 'bg-[#faf8f4] text-rose-800 hover:bg-rose-50 border border-rose-200'
              }`}
            >
              Contradicts ({contradictsCount})
            </button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={() => onSwitchAdditionalFilter('ALL')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                additionalFilter === 'ALL'
                  ? 'bg-[#1e1c19] text-[#f7f4ed] font-semibold'
                  : 'bg-[#faf8f4] text-[#706b63] hover:text-[#1e1c19] border border-[#dfd8c8]'
              }`}
            >
              All ({totalUnmatched})
            </button>
            <button
              type="button"
              onClick={() => onSwitchAdditionalFilter('CORRECT_ADDITIONAL')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                additionalFilter === 'CORRECT_ADDITIONAL'
                  ? 'bg-emerald-800 text-white font-semibold'
                  : 'bg-[#faf8f4] text-emerald-800 hover:bg-emerald-50 border border-emerald-200'
              }`}
            >
              Correct ({correctCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchAdditionalFilter('IRRELEVANT')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                additionalFilter === 'IRRELEVANT'
                  ? 'bg-[#555047] text-white font-semibold'
                  : 'bg-[#faf8f4] text-[#555047] hover:bg-[#ede8dc] border border-[#dfd8c8]'
              }`}
            >
              Irrelevant ({irrelevantCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchAdditionalFilter('INCORRECT')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                additionalFilter === 'INCORRECT'
                  ? 'bg-rose-800 text-white font-semibold'
                  : 'bg-[#faf8f4] text-rose-800 hover:bg-rose-50 border border-rose-200'
              }`}
            >
              Incorrect ({incorrectCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchAdditionalFilter('UNCERTAIN')}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                additionalFilter === 'UNCERTAIN'
                  ? 'bg-amber-800 text-white font-semibold'
                  : 'bg-[#faf8f4] text-amber-900 hover:bg-amber-50 border border-amber-200'
              }`}
            >
              Uncertain ({uncertainAddCount})
            </button>
          </div>
        )}
      </div>

      <div className="text-[13px] leading-relaxed text-[#706b63] font-sans">
        {activeView === 'entailment'
          ? 'Propositional textual entailment evaluates whether matched student propositions entail, contradict, or remain uncertain relative to reference criteria.'
          : 'Proposition-level classification evaluates unmatched student assertions as correct additional information, irrelevant facts, or domain misconceptions.'}
      </div>
    </div>
  );
}
