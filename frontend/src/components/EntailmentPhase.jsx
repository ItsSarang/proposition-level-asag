import { useState } from 'react';
import EntailmentBar from './EntailmentBar';

export default function EntailmentPhase({
  entailmentData,
  relationsData,
}) {
  const [entailmentFilter, setEntailmentFilter] = useState('ALL');

  const evaluations = entailmentData?.entailment_evaluations || [];
  const referenceProps = relationsData?.reference_propositions || [];
  const studentProps = relationsData?.student_propositions || [];

  const entailsCount = evaluations.filter((e) => e.status === 'ENTAILS').length;
  const uncertainCount = evaluations.filter((e) => e.status === 'UNCERTAIN').length;
  const contradictsCount = evaluations.filter((e) => e.status === 'CONTRADICTS').length;

  const filteredEvaluations = evaluations.filter((item) => {
    if (entailmentFilter === 'ALL') return true;
    return item.status === entailmentFilter;
  });

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      <EntailmentBar
        entailmentFilter={entailmentFilter}
        onSwitchFilter={setEntailmentFilter}
        totalCount={evaluations.length}
        entailsCount={entailsCount}
        uncertainCount={uncertainCount}
        contradictsCount={contradictsCount}
      />

      <div className="flex-1 min-h-0 relative w-full overflow-y-auto p-6 md:p-8">
        <div className="max-w-5xl mx-auto flex flex-col gap-4 pb-12 w-full">
          {filteredEvaluations.length === 0 ? (
            <div className="py-16 text-center text-[#706b63] font-mono text-xs">
              No proposition evaluations found for the selected filter.
            </div>
          ) : (
            filteredEvaluations.map((item, idx) => {
              const refProp = referenceProps.find((p) => p.id === item.reference_id);
              const stuProp = studentProps.find((p) => p.id === item.student_id);

              return (
                <div
                  key={item.match_id || idx}
                  className="rounded-2xl p-5 md:p-6 bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none"
                >
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                        PAIR {idx + 1}
                      </span>
                      <span className="text-[#a89e8f] text-[12px] select-none">—</span>
                      <span className="text-[11.5px] text-[#706b63] font-medium">
                        ENTAILMENT EVALUATION
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded border ${
                          item.status === 'ENTAILS'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : item.status === 'UNCERTAIN'
                            ? 'bg-amber-50 text-amber-900 border-amber-200'
                            : 'bg-rose-50 text-rose-800 border-rose-200'
                        }`}
                      >
                        {item.status}
                      </span>

                      <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded border border-[#dfd8c8] bg-[#f7f4ed] text-[#555047]">
                        {Math.round(item.confidence * 100)}% Confidence
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-3">
                    <div className="p-4 rounded-xl bg-[#f7f4ed] border border-[#dfd8c8]">
                      <span className="text-[10.5px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold block mb-1.5">
                        Reference Ground Truth
                      </span>
                      <h5 className="text-[15px] font-bold text-[#1e1c19] tracking-tight mb-3">
                        &ldquo;{item.reference_text}&rdquo;
                      </h5>
                      <div className="flex flex-wrap items-center gap-1.5 text-[11.5px] font-mono text-[#555047]">
                        <span className="bg-[#ede8dc] px-2 py-0.5 rounded border border-[#dfd8c8]">
                          SUBJ: {refProp?.subject || '—'}
                        </span>
                        <span className="text-[#a89e8f]">→</span>
                        <span className="bg-[#ede8dc] px-2 py-0.5 rounded border border-[#dfd8c8] text-indigo-900 font-semibold">
                          PRED: {refProp?.predicate || '—'}
                        </span>
                        <span className="text-[#a89e8f]">→</span>
                        <span className="bg-[#ede8dc] px-2 py-0.5 rounded border border-[#dfd8c8]">
                          OBJ: {refProp?.object || '—'}
                        </span>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-[#f7f4ed] border border-[#dfd8c8]">
                      <span className="text-[10.5px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold block mb-1.5">
                        Student Assertion
                      </span>
                      <h5 className="text-[15px] font-bold text-[#1e1c19] tracking-tight mb-3">
                        &ldquo;{item.student_text}&rdquo;
                      </h5>
                      <div className="flex flex-wrap items-center gap-1.5 text-[11.5px] font-mono text-[#555047]">
                        <span className="bg-[#ede8dc] px-2 py-0.5 rounded border border-[#dfd8c8]">
                          SUBJ: {stuProp?.subject || '—'}
                        </span>
                        <span className="text-[#a89e8f]">→</span>
                        <span className="bg-[#ede8dc] px-2 py-0.5 rounded border border-[#dfd8c8] text-indigo-900 font-semibold">
                          PRED: {stuProp?.predicate || '—'}
                        </span>
                        <span className="text-[#a89e8f]">→</span>
                        <span className="bg-[#ede8dc] px-2 py-0.5 rounded border border-[#dfd8c8]">
                          OBJ: {stuProp?.object || '—'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-[#f7f4ed] border border-[#dfd8c8] my-3">
                    <span className="text-[10.5px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold block mb-1">
                      Verification Evidence
                    </span>
                    <p className="text-[13px] text-[#1e1c19] font-sans leading-relaxed">
                      {item.evidence}
                    </p>
                  </div>

                  <div className="mt-3 pt-3 border-t border-[#dfd8c8]/70 flex flex-wrap items-center justify-between gap-2 text-[11.5px] font-mono text-[#706b63]">
                    <div className="flex flex-wrap items-center gap-3">
                      <span>
                        Subject Sim:{' '}
                        <strong className="text-[#1e1c19]">
                          {Math.round(item.subject_similarity * 100)}%
                        </strong>
                      </span>
                      <span className="text-[#dfd8c8]">|</span>
                      <span>
                        Predicate Sim:{' '}
                        <strong className="text-[#1e1c19]">
                          {Math.round(item.predicate_similarity * 100)}%
                        </strong>
                      </span>
                    </div>

                    <div>
                      Composite Score:{' '}
                      <span className="font-semibold text-indigo-900">
                        {item.confidence.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
