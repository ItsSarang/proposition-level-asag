export default function ScoringBar({
  baseGrade = 0,
  finalGrade = 0,
  maxPoints = 5.0,
  netAdjustment = 0,
}) {
  return (
    <div className="w-full bg-[#f4f0e8]/95 border-b border-[#dfd8c8] px-6 py-3 select-none shrink-0 shadow-2xs">
      <div className="flex items-center justify-between gap-3 mb-2.5">
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="inline-flex items-center gap-2 bg-[#e6e0d2] px-3 py-1.5 rounded-lg border border-[#d8d0bf] text-[12.5px] font-mono">
            <span className="text-[#706b63]">Base ASAG:</span>
            <strong className="text-[#1e1c19]">
              {baseGrade.toFixed(2)} / {maxPoints.toFixed(1)}
            </strong>
          </div>

          <div className="inline-flex items-center gap-2 bg-[#e6e0d2] px-3 py-1.5 rounded-lg border border-[#d8d0bf] text-[12.5px] font-mono">
            <span className="text-[#706b63]">Proposition Adjustment:</span>
            <strong
              className={
                netAdjustment > 0
                  ? 'text-emerald-800'
                  : netAdjustment < 0
                  ? 'text-rose-800'
                  : 'text-[#555047]'
              }
            >
              {netAdjustment >= 0 ? `+${netAdjustment.toFixed(2)}` : netAdjustment.toFixed(2)} pts
            </strong>
          </div>

          <div className="inline-flex items-center gap-2 bg-[#faf8f4] px-3.5 py-1.5 rounded-lg border border-[#d2c9b6] text-[12.5px] font-mono shadow-xs">
            <span className="text-indigo-950 font-medium">Final Proposed Grade:</span>
            <strong className="text-indigo-900 text-[13.5px]">
              {finalGrade.toFixed(2)} / {maxPoints.toFixed(1)}
            </strong>
          </div>
        </div>
      </div>

      <div className="text-[13.5px] leading-relaxed text-[#706b63] font-sans">
        Final ASAG evaluation synthesizing Base ASAG reference coverage with proposition-level adjustments for additional student assertions.
      </div>
    </div>
  );
}
