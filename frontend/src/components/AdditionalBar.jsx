export default function AdditionalBar({
  additionalFilter = 'ALL',
  onSwitchFilter,
  totalCount = 0,
  correctCount = 0,
  irrelevantCount = 0,
  incorrectCount = 0,
  uncertainCount = 0,
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
                additionalFilter === 'ALL'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              All Unmatched ({totalCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('CORRECT_ADDITIONAL')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                additionalFilter === 'CORRECT_ADDITIONAL'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Correct Additional ({correctCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('IRRELEVANT')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                additionalFilter === 'IRRELEVANT'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Irrelevant ({irrelevantCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('INCORRECT')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                additionalFilter === 'INCORRECT'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Incorrect ({incorrectCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('UNCERTAIN')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                additionalFilter === 'UNCERTAIN'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Uncertain ({uncertainCount})
            </button>
          </div>
        </div>
      </div>

      <div className="text-[13.5px] leading-relaxed text-[#706b63] font-sans">
        {additionalFilter === 'ALL' && (
          <span>
            Proposition-level evaluation of unmatched student information assessing domain validity, enrichment, and misconceptions.
          </span>
        )}
        {additionalFilter === 'CORRECT_ADDITIONAL' && (
          <span>
            Accurate domain assertions that extend beyond the reference rubric requirements.
          </span>
        )}
        {additionalFilter === 'IRRELEVANT' && (
          <span>
            Extraneous assertions with no material domain bearing, evaluated neutrally with zero penalty.
          </span>
        )}
        {additionalFilter === 'INCORRECT' && (
          <span>
            Misconceptions or erroneous claims that contradict verified domain principles.
          </span>
        )}
        {additionalFilter === 'UNCERTAIN' && (
          <span>
            Plausible assertions that cannot be conclusively verified against the domain knowledge base.
          </span>
        )}
      </div>
    </div>
  );
}
