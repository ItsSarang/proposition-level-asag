import { useState } from 'react';
import AdditionalBar from './AdditionalBar';

export default function AdditionalPhase({
  additionalData,
  relationsData,
}) {
  const [additionalFilter, setAdditionalFilter] = useState('ALL');

  const unmatchedProps = additionalData?.unmatched_propositions || [];
  const recoveredCore = additionalData?.recovered_core_items || [];
  const studentProps = relationsData?.student_propositions || [];

  const correctCount = unmatchedProps.filter((p) => p.classification === 'CORRECT_ADDITIONAL').length;
  const irrelevantCount = unmatchedProps.filter((p) => p.classification === 'IRRELEVANT').length;
  const incorrectCount = unmatchedProps.filter((p) => p.classification === 'INCORRECT').length;
  const uncertainCount = unmatchedProps.filter((p) => p.classification === 'UNCERTAIN').length;

  const filteredProps = unmatchedProps.filter((item) => {
    if (additionalFilter === 'ALL') return true;
    return item.classification === additionalFilter;
  });

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      <AdditionalBar
        additionalFilter={additionalFilter}
        onSwitchFilter={setAdditionalFilter}
        totalCount={unmatchedProps.length}
        correctCount={correctCount}
        irrelevantCount={irrelevantCount}
        incorrectCount={incorrectCount}
        uncertainCount={uncertainCount}
      />

      <div className="flex-1 min-h-0 relative w-full overflow-y-auto p-6 md:p-8">
        <div className="max-w-5xl mx-auto flex flex-col gap-4 pb-12 w-full">
          {filteredProps.length === 0 ? (
            <div className="py-16 text-center text-[#706b63] font-mono text-xs">
              No unmatched propositions found for the selected filter.
            </div>
          ) : (
            filteredProps.map((item, idx) => {
              const stuProp = studentProps.find((p) => p.id === item.student_prop_id);
              const propIndex = stuProp ? stuProp.index + 1 : idx + 1;

              return (
                <div
                  key={item.id || idx}
                  className="rounded-2xl p-5 md:p-6 bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none"
                >
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                        P{propIndex}
                      </span>
                      <span className="text-[#a89e8f] text-[12px] select-none">—</span>
                      <span className="text-[11.5px] text-[#706b63] font-medium">
                        UNMATCHED ASSERTION
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10.5px] font-mono font-semibold px-2.5 py-0.5 rounded border ${
                          (stuProp?.polarity || 'POSITIVE') === 'NEGATIVE'
                            ? 'bg-rose-50 text-rose-800 border-rose-200'
                            : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        }`}
                      >
                        {stuProp?.polarity || 'POSITIVE'}
                      </span>

                      <span
                        className={`text-[10.5px] font-mono font-semibold px-2.5 py-0.5 rounded border ${
                          item.classification === 'CORRECT_ADDITIONAL'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : item.classification === 'INCORRECT'
                            ? 'bg-rose-50 text-rose-800 border-rose-200'
                            : item.classification === 'UNCERTAIN'
                            ? 'bg-amber-50 text-amber-900 border-amber-200'
                            : 'bg-[#ede8dc] text-[#555047] border-[#dfd8c8]'
                        }`}
                      >
                        {item.classification.replace(/_/g, ' ')}
                      </span>

                      <span
                        className={`text-[10.5px] font-mono font-semibold px-2.5 py-0.5 rounded border ${
                          item.score_effect > 0
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : item.score_effect < 0
                            ? 'bg-rose-50 text-rose-800 border-rose-200'
                            : 'bg-[#f7f4ed] text-[#706b63] border-[#dfd8c8]'
                        }`}
                      >
                        {item.score_effect > 0
                          ? `+${item.score_effect.toFixed(2)} pts`
                          : `${item.score_effect.toFixed(2)} pts`}
                      </span>
                    </div>
                  </div>

                  <h4 className="text-[16px] md:text-[17px] font-bold text-[#1e1c19] tracking-tight mb-4">
                    &ldquo;{item.text}&rdquo;
                  </h4>

                  <div className="flex flex-wrap items-center gap-2 pt-1 pb-3">
                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">SUBJECT:</span>
                      <span className="text-[#1e1c19] font-semibold">
                        {stuProp?.subject || '— (elliptical)'}
                      </span>
                    </div>

                    <span className="text-[#b5ab9b] font-mono text-sm">→</span>

                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">PREDICATE:</span>
                      <span className="text-indigo-800 font-semibold">
                        {stuProp?.predicate || '—'}
                      </span>
                    </div>

                    <span className="text-[#b5ab9b] font-mono text-sm">→</span>

                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">OBJECT:</span>
                      <span className="text-[#1e1c19] font-medium">
                        {stuProp?.object || '—'}
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#f7f4ed] border border-[#dfd8c8] mt-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10.5px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold">
                        Classification Rationale
                      </span>
                      {item.severity_level && item.severity_level !== 'NONE' && (
                        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded border border-rose-200 bg-rose-50 text-rose-800">
                          Severity: {item.severity_level}
                        </span>
                      )}
                    </div>
                    <p className="text-[13px] text-[#1e1c19] font-sans leading-relaxed">
                      {item.rationale}
                    </p>
                  </div>
                </div>
              );
            })
          )}

          {recoveredCore.length > 0 && (
            <div className="mt-6 pt-6 border-t border-[#dfd8c8]">
              <div className="flex items-center gap-2 font-mono mb-4">
                <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                  RECOVERED CORE CONCEPTS ({recoveredCore.length})
                </span>
                <span className="text-[#a89e8f] text-[12px] select-none">—</span>
                <span className="text-[11.5px] text-[#706b63] font-medium">
                  Semantic Fallback Recovery
                </span>
              </div>

              <div className="flex flex-col gap-3">
                {recoveredCore.map((rec, rIdx) => (
                  <div
                    key={rIdx}
                    className="p-4 rounded-xl bg-[#fdfcf9] border border-indigo-200 shadow-2xs"
                  >
                    <div className="flex items-center justify-between gap-2 mb-2 font-mono text-xs">
                      <span className="font-semibold text-indigo-950">
                        Candidate: &ldquo;{rec.student_text}&rdquo;
                      </span>
                      <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-800 border border-indigo-200 font-semibold text-[11px]">
                        {Math.round(rec.confidence * 100)}% Confidence
                      </span>
                    </div>
                    <div className="text-xs text-[#555047] font-sans mb-1">
                      Recovered to match: &ldquo;{rec.reference_text}&rdquo;
                    </div>
                    <div className="text-[11.5px] text-[#706b63] font-mono">
                      {rec.rationale}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
