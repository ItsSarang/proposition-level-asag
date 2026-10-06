export default function AlignmentBar({
  alignmentFilter = 'matched',
  onSwitchFilter,
  matchedCount = 0,
  unmatchedStudentCount = 0,
  unmatchedReferenceCount = 0,
}) {
  return (
    <div className="w-full bg-[#f4f0e8]/95 border-b border-[#dfd8c8] px-6 py-3 select-none shrink-0 shadow-2xs">
      <div className="flex items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2.5">
          <div className="inline-flex items-center bg-[#e6e0d2] p-0.5 rounded-lg border border-[#d8d0bf] text-[13px] font-mono">
            <button
              type="button"
              onClick={() => onSwitchFilter('matched')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                alignmentFilter === 'matched'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Matched Pairs ({matchedCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('unmatched_student')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                alignmentFilter === 'unmatched_student'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Unmatched Student ({unmatchedStudentCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchFilter('unmatched_reference')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                alignmentFilter === 'unmatched_reference'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Unmatched Reference ({unmatchedReferenceCount})
            </button>
          </div>
        </div>
      </div>

      <div className="text-[13.5px] leading-relaxed text-[#706b63] font-sans">
        {alignmentFilter === 'matched' && (
          <span>
            Bipartite proposition pairs aligned between student response and reference criteria via lexical-semantic similarity.
          </span>
        )}
        {alignmentFilter === 'unmatched_student' && (
          <span>
            Candidate propositions asserted by the student with no partner in the reference answer (evaluated in Phase 06).
          </span>
        )}
        {alignmentFilter === 'unmatched_reference' && (
          <span>
            Reference ground truth concepts omitted from the student response (missing requirements).
          </span>
        )}
      </div>
    </div>
  );
}
