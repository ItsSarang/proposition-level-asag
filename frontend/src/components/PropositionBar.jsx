export default function PropositionBar({
  propMode = 'student',
  onSwitchPropMode,
  studentCount = 0,
  referenceCount = 0,
  fullText = '',
  selectedProp,
}) {
  const charStart = selectedProp?.char_start;
  const charEnd = selectedProp?.char_end;

  let before = fullText;
  let highlighted = '';
  let after = '';

  if (
    typeof charStart === 'number' &&
    typeof charEnd === 'number' &&
    charStart >= 0 &&
    charEnd > charStart &&
    charEnd <= fullText.length
  ) {
    before = fullText.slice(0, charStart);
    highlighted = fullText.slice(charStart, charEnd);
    after = fullText.slice(charEnd);
  } else if (selectedProp?.text) {
    const idx = fullText.toLowerCase().indexOf(selectedProp.text.toLowerCase());
    if (idx >= 0) {
      before = fullText.slice(0, idx);
      highlighted = fullText.slice(idx, idx + selectedProp.text.length);
      after = fullText.slice(idx + selectedProp.text.length);
    }
  }

  return (
    <div className="w-full bg-[#f4f0e8]/95 border-b border-[#dfd8c8] px-6 py-3 select-none shrink-0 shadow-2xs">
      <div className="flex items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2.5">
          <div className="inline-flex items-center bg-[#e6e0d2] p-0.5 rounded-lg border border-[#d8d0bf] text-[13px] font-mono">
            <button
              type="button"
              onClick={() => onSwitchPropMode('student')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                propMode === 'student'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Student Propositions ({studentCount})
            </button>
            <button
              type="button"
              onClick={() => onSwitchPropMode('reference')}
              className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
                propMode === 'reference'
                  ? 'bg-[#faf8f4] text-indigo-900 font-semibold shadow-xs'
                  : 'text-[#706b63] hover:text-[#1e1c19]'
              }`}
            >
              Reference Propositions ({referenceCount})
            </button>
          </div>
        </div>
      </div>

      <div className="text-[14px] leading-relaxed text-[#1e1c19] font-sans max-h-20 overflow-y-auto">
        {highlighted ? (
          <>
            <span className="text-[#423e38]">{before}</span>
            <span className="inline-block px-1.5 py-0.5 mx-0.5 rounded text-[13.5px] font-semibold border border-[#3730a3] bg-[#3730a3] text-white shadow-xs">
              {highlighted}
            </span>
            <span className="text-[#423e38]">{after}</span>
          </>
        ) : (
          <span className="text-[#1e1c19]">{fullText}</span>
        )}
      </div>
    </div>
  );
}
