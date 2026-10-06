import { useState } from 'react';
import AlignmentBar from './AlignmentBar';

export default function AlignmentPhase({
  matchData,
  relationsData,
}) {
  const [alignmentFilter, setAlignmentFilter] = useState('matched');

  const matchedPairs = matchData?.matched_pairs || [];
  const unmatchedStudentIds = matchData?.unmatched_student_ids || [];
  const unmatchedReferenceIds = matchData?.unmatched_reference_ids || [];

  const studentProps = relationsData?.student_propositions || [];
  const referenceProps = relationsData?.reference_propositions || [];

  const unmatchedStudentProps = unmatchedStudentIds
    .map((id) => studentProps.find((p) => p.id === id))
    .filter(Boolean);

  const unmatchedReferenceProps = unmatchedReferenceIds
    .map((id) => referenceProps.find((p) => p.id === id))
    .filter(Boolean);

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      <AlignmentBar
        alignmentFilter={alignmentFilter}
        onSwitchFilter={setAlignmentFilter}
        matchedCount={matchedPairs.length}
        unmatchedStudentCount={unmatchedStudentProps.length}
        unmatchedReferenceCount={unmatchedReferenceProps.length}
      />

      <div className="flex-1 min-h-0 relative w-full overflow-y-auto p-6 md:p-8">
        <div className="max-w-5xl mx-auto flex flex-col gap-4 pb-12 w-full">
          {alignmentFilter === 'matched' && (
            matchedPairs.length === 0 ? (
              <div className="py-16 text-center text-[#706b63] font-mono text-xs">
                No proposition alignments identified.
              </div>
            ) : (
              matchedPairs.map((pair, idx) => {
                const refProp = referenceProps.find((p) => p.id === pair.reference_id);
                const stuProp = studentProps.find((p) => p.id === pair.student_id);

                return (
                  <div
                    key={pair.id || idx}
                    className="rounded-2xl p-5 md:p-6 bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none"
                  >
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <div className="flex items-center gap-2 font-mono">
                        <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                          ALIGNMENT {idx + 1}
                        </span>
                        <span className="text-[#a89e8f] text-[12px] select-none">—</span>
                        <span className="text-[11.5px] text-[#706b63] font-medium">
                          {pair.match_method}
                        </span>
                      </div>

                      <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded border border-emerald-200 bg-emerald-50 text-emerald-800">
                        {Math.round(pair.triple_score * 100)}% Match
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-3">
                      <div className="p-4 rounded-xl bg-[#f7f4ed] border border-[#dfd8c8]">
                        <span className="text-[10.5px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold block mb-1.5">
                          Reference Ground Truth
                        </span>
                        <h5 className="text-[15px] font-bold text-[#1e1c19] tracking-tight mb-3">
                          &ldquo;{pair.reference_text}&rdquo;
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
                          Student Candidate
                        </span>
                        <h5 className="text-[15px] font-bold text-[#1e1c19] tracking-tight mb-3">
                          &ldquo;{pair.student_text}&rdquo;
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

                    <div className="mt-3 pt-3 border-t border-[#dfd8c8]/70 flex flex-wrap items-center justify-between gap-2 text-[11.5px] font-mono text-[#706b63]">
                      <div className="flex flex-wrap items-center gap-3">
                        <span>
                          Subject Sim:{' '}
                          <strong className="text-[#1e1c19]">
                            {Math.round(pair.subject_similarity * 100)}%
                          </strong>
                        </span>
                        <span className="text-[#dfd8c8]">|</span>
                        <span>
                          Predicate Sim:{' '}
                          <strong className="text-[#1e1c19]">
                            {Math.round(pair.predicate_similarity * 100)}%
                          </strong>
                        </span>
                        <span className="text-[#dfd8c8]">|</span>
                        <span>
                          Object Sim:{' '}
                          <strong className="text-[#1e1c19]">
                            {pair.object_similarity !== null
                              ? `${Math.round(pair.object_similarity * 100)}%`
                              : '—'}
                          </strong>
                        </span>
                      </div>

                      <div>
                        Composite Score:{' '}
                        <span className="font-semibold text-indigo-900">
                          {pair.triple_score.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )
          )}

          {alignmentFilter === 'unmatched_student' && (
            unmatchedStudentProps.length === 0 ? (
              <div className="py-16 text-center text-[#706b63] font-mono text-xs">
                No unmatched student propositions. All student assertions were aligned with reference concepts.
              </div>
            ) : (
              unmatchedStudentProps.map((prop, idx) => (
                <div
                  key={prop.id || idx}
                  className="rounded-2xl p-5 md:p-6 bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none"
                >
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                        P{prop.index + 1}
                      </span>
                      <span className="text-[#a89e8f] text-[12px] select-none">—</span>
                      <span className="text-[11.5px] text-[#706b63] font-medium">
                        {prop.representation_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10.5px] font-mono font-semibold px-2.5 py-0.5 rounded border ${
                          prop.polarity === 'NEGATIVE'
                            ? 'bg-rose-50 text-rose-800 border-rose-200'
                            : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        }`}
                      >
                        {prop.polarity}
                      </span>

                      <span className="text-[10.5px] font-mono font-semibold px-2.5 py-0.5 rounded border border-amber-200 bg-amber-50 text-amber-900">
                        UNMATCHED (ADDITIONAL CANDIDATE)
                      </span>
                    </div>
                  </div>

                  <h4 className="text-[16px] md:text-[17px] font-bold text-[#1e1c19] tracking-tight mb-4">
                    &ldquo;{prop.text}&rdquo;
                  </h4>

                  <div className="flex flex-wrap items-center gap-2 pt-1 pb-3">
                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">SUBJECT:</span>
                      <span className="text-[#1e1c19] font-semibold">
                        {prop.subject || '— (elliptical)'}
                      </span>
                    </div>

                    <span className="text-[#b5ab9b] font-mono text-sm">→</span>

                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">PREDICATE:</span>
                      <span className="text-indigo-800 font-semibold">
                        {prop.predicate || '—'}
                      </span>
                    </div>

                    <span className="text-[#b5ab9b] font-mono text-sm">→</span>

                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">OBJECT:</span>
                      <span className="text-[#1e1c19] font-medium">
                        {prop.object || '—'}
                      </span>
                    </div>
                  </div>

                  <div className="mt-2 pt-3 border-t border-[#dfd8c8]/60 text-[12.5px] text-[#706b63] font-sans">
                    This candidate assertion was not matched to the reference answer. In Phase 06, it will be classified as Correct Additional, Irrelevant, or Incorrect information.
                  </div>
                </div>
              ))
            )
          )}

          {alignmentFilter === 'unmatched_reference' && (
            unmatchedReferenceProps.length === 0 ? (
              <div className="py-16 text-center text-[#706b63] font-sans text-[13.5px]">
                All reference propositions were covered by the student response. No ground truth requirements were omitted.
              </div>
            ) : (
              unmatchedReferenceProps.map((prop, idx) => (
                <div
                  key={prop.id || idx}
                  className="rounded-2xl p-5 md:p-6 bg-[#fdfcf9] border border-[#dfd8c8] shadow-2xs select-none"
                >
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                        REF {prop.index + 1}
                      </span>
                      <span className="text-[#a89e8f] text-[12px] select-none">—</span>
                      <span className="text-[11.5px] text-[#706b63] font-medium">
                        {prop.representation_type}
                      </span>
                    </div>

                    <span className="text-[10.5px] font-mono font-semibold px-2.5 py-0.5 rounded border border-rose-200 bg-rose-50 text-rose-800">
                      OMITTED REQUIREMENT
                    </span>
                  </div>

                  <h4 className="text-[16px] md:text-[17px] font-bold text-[#1e1c19] tracking-tight mb-4">
                    &ldquo;{prop.text}&rdquo;
                  </h4>

                  <div className="flex flex-wrap items-center gap-2 pt-1 pb-1">
                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">SUBJECT:</span>
                      <span className="text-[#1e1c19] font-semibold">
                        {prop.subject || '— (elliptical)'}
                      </span>
                    </div>

                    <span className="text-[#b5ab9b] font-mono text-sm">→</span>

                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">PREDICATE:</span>
                      <span className="text-indigo-800 font-semibold">
                        {prop.predicate || '—'}
                      </span>
                    </div>

                    <span className="text-[#b5ab9b] font-mono text-sm">→</span>

                    <div className="px-3 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8] text-xs font-mono">
                      <span className="text-[#706b63] mr-1.5">OBJECT:</span>
                      <span className="text-[#1e1c19] font-medium">
                        {prop.object || '—'}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )
          )}
        </div>
      </div>
    </div>
  );
}
