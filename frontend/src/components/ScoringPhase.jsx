import ScoringBar from './ScoringBar';

export default function ScoringPhase({
  scoreData,
}) {
  const baseGrade = scoreData?.base_grade ?? 0;
  const baseScoreEffective = scoreData?.base_score_effective ?? 0;
  const positiveAdj = scoreData?.positive_adjustment ?? 0;
  const negativeAdj = scoreData?.negative_adjustment ?? 0;
  const netAdjustment = scoreData?.net_adjustment ?? 0;
  const finalGrade = scoreData?.final_grade ?? 0;
  const finalScore = scoreData?.final_score ?? 0;
  const maxPoints = scoreData?.max_points ?? 5.0;
  const isClippedUpper = scoreData?.is_clipped_upper || false;
  const isClippedLower = scoreData?.is_clipped_lower || false;
  const itemizedTrace = scoreData?.itemized_trace || [];
  const explanation = scoreData?.explanation || '';

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      <ScoringBar
        baseGrade={baseGrade}
        finalGrade={finalGrade}
        maxPoints={maxPoints}
        netAdjustment={netAdjustment}
      />

      <div className="flex-1 min-h-0 relative w-full overflow-y-auto p-6 md:p-8">
        <div className="max-w-5xl mx-auto flex flex-col gap-6 pb-12 w-full">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-5 md:p-6 rounded-2xl bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none">
              <div className="flex items-center justify-between gap-2 mb-2 font-mono">
                <span className="text-[12px] font-bold text-indigo-900 tracking-wider uppercase">
                  System 2 — Base ASAG
                </span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded border border-[#dfd8c8] bg-[#f7f4ed] text-[#555047]">
                  {Math.round(baseScoreEffective * 100)}% Coverage
                </span>
              </div>
              <div className="text-3xl font-extrabold text-[#1e1c19] tracking-tight my-2">
                {baseGrade.toFixed(2)}
                <span className="text-sm font-normal text-[#706b63]"> / {maxPoints.toFixed(1)}</span>
              </div>
              <p className="text-[12px] text-[#706b63] font-sans leading-relaxed">
                Score derived purely from reference answer requirement coverage and propositional textual entailment.
              </p>
            </div>

            <div className="p-5 md:p-6 rounded-2xl bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none">
              <div className="flex items-center justify-between gap-2 mb-2 font-mono">
                <span className="text-[12px] font-bold text-indigo-900 tracking-wider uppercase">
                  Proposition Modulation
                </span>
                <span
                  className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${
                    netAdjustment > 0
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : netAdjustment < 0
                      ? 'bg-rose-50 text-rose-800 border-rose-200'
                      : 'bg-[#f7f4ed] text-[#706b63] border-[#dfd8c8]'
                  }`}
                >
                  {netAdjustment >= 0 ? `+${netAdjustment.toFixed(2)}` : netAdjustment.toFixed(2)}
                </span>
              </div>
              <div
                className={`text-3xl font-extrabold tracking-tight my-2 ${
                  netAdjustment > 0
                    ? 'text-emerald-800'
                    : netAdjustment < 0
                    ? 'text-rose-800'
                    : 'text-[#1e1c19]'
                }`}
              >
                {netAdjustment >= 0 ? `+${netAdjustment.toFixed(2)}` : netAdjustment.toFixed(2)}
                <span className="text-sm font-normal text-[#706b63]"> pts</span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-mono text-[#555047] mb-2">
                <span className="bg-[#f7f4ed] px-2 py-0.5 rounded border border-[#dfd8c8] text-emerald-800 font-semibold">
                  +{positiveAdj.toFixed(2)} Bonus
                </span>
                <span className="bg-[#f7f4ed] px-2 py-0.5 rounded border border-[#dfd8c8] text-rose-800 font-semibold">
                  -{Math.abs(negativeAdj).toFixed(2)} Penalty
                </span>
              </div>
              <p className="text-[12px] text-[#706b63] font-sans leading-relaxed">
                Additive modulation from unmatched student proposition evaluations and domain contradiction guards.
              </p>
            </div>

            <div className="p-5 md:p-6 rounded-2xl bg-[#fdfcf9] border border-indigo-200 shadow-2xs select-none">
              <div className="flex items-center justify-between gap-2 mb-2 font-mono">
                <span className="text-[12px] font-bold text-indigo-950 tracking-wider uppercase">
                  System 3 — Proposed Final
                </span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded border border-indigo-200 bg-indigo-50 text-indigo-800">
                  {Math.round(finalScore * 100)}% Composite
                </span>
              </div>
              <div className="text-3xl font-extrabold text-indigo-950 tracking-tight my-2">
                {finalGrade.toFixed(2)}
                <span className="text-sm font-normal text-[#706b63]"> / {maxPoints.toFixed(1)}</span>
              </div>
              {isClippedUpper && (
                <div className="text-[11px] font-mono font-medium text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 inline-block mb-1">
                  Grade bounded at maximum score ({maxPoints.toFixed(1)})
                </div>
              )}
              {isClippedLower && (
                <div className="text-[11px] font-mono font-medium text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 inline-block mb-1">
                  Grade bounded at minimum score (0.0)
                </div>
              )}
              <p className="text-[12px] text-[#706b63] font-sans leading-relaxed">
                Final interpretable grade synthesizing base rubric compliance with extra knowledge evaluation.
              </p>
            </div>
          </div>

          <div className="p-4 md:p-5 rounded-2xl bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold block mb-2">
              Scoring Equation Trace
            </span>
            <div className="flex flex-wrap items-center gap-2 font-mono text-[13px] text-[#1e1c19]">
              <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8]">
                Base Grade: <strong className="text-indigo-900">{baseGrade.toFixed(2)}</strong>
              </div>
              <span className="text-[#a89e8f] text-base">+</span>
              <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8]">
                Positive Adj: <strong className="text-emerald-800">+{positiveAdj.toFixed(2)}</strong>
              </div>
              <span className="text-[#a89e8f] text-base">−</span>
              <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8]">
                Negative Adj: <strong className="text-rose-800">{Math.abs(negativeAdj).toFixed(2)}</strong>
              </div>
              <span className="text-[#a89e8f] text-base">=</span>
              <div className="px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-950 font-bold">
                Final Grade: {finalGrade.toFixed(2)} / {maxPoints.toFixed(1)}
              </div>
            </div>
          </div>

          {explanation && (
            <div className="p-5 rounded-2xl bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold block mb-1.5">
                Pedagogical Attribution & Explanation
              </span>
              <p className="text-[13.5px] font-sans text-[#1e1c19] leading-relaxed">
                {explanation}
              </p>
            </div>
          )}

          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 font-mono">
              <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                ITEMIZED PROPOSITION ADJUSTMENT TRACE ({itemizedTrace.length})
              </span>
              <span className="text-[#a89e8f] text-[12px] select-none">—</span>
              <span className="text-[11.5px] text-[#706b63] font-medium">
                Unmatched Proposition Attributions
              </span>
            </div>

            {itemizedTrace.length === 0 ? (
              <div className="p-8 text-center rounded-2xl bg-[#fdfcf9] border border-[#dfd8c8] text-xs font-mono text-[#706b63]">
                No proposition adjustments applied. All student assertions were covered by the base reference rubric with zero extra assertions.
              </div>
            ) : (
              itemizedTrace.map((item, idx) => (
                <div
                  key={idx}
                  className="rounded-2xl p-5 md:p-6 bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none"
                >
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                        ADJUSTMENT {idx + 1}
                      </span>
                      <span className="text-[#a89e8f] text-[12px] select-none">—</span>
                      <span className="text-[11.5px] text-[#706b63] font-medium">
                        {item.classification.replace(/_/g, ' ')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {item.severity_level && item.severity_level !== 'NONE' && (
                        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded border border-rose-200 bg-rose-50 text-rose-800">
                          Severity: {item.severity_level}
                        </span>
                      )}

                      <span
                        className={`text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded border ${
                          item.adjustment_value > 0
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : item.adjustment_value < 0
                            ? 'bg-rose-50 text-rose-800 border-rose-200'
                            : 'bg-[#f7f4ed] text-[#706b63] border-[#dfd8c8]'
                        }`}
                      >
                        {item.adjustment_value > 0
                          ? `+${item.adjustment_value.toFixed(2)} pts`
                          : `${item.adjustment_value.toFixed(2)} pts`}
                      </span>
                    </div>
                  </div>

                  <h5 className="text-[15px] font-bold text-[#1e1c19] tracking-tight mb-2">
                    &ldquo;{item.proposition_text}&rdquo;
                  </h5>

                  <div className="p-3.5 rounded-xl bg-[#f7f4ed] border border-[#dfd8c8] mt-2">
                    <span className="text-[10.5px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold block mb-1">
                      Adjustment Justification
                    </span>
                    <p className="text-[13px] text-[#1e1c19] font-sans leading-relaxed">
                      {item.rationale}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
