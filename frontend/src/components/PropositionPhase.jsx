import { useState, useEffect } from 'react';
import PropositionBar from './PropositionBar';

export default function PropositionPhase({
  relationsData,
  studentAnswer = '',
  referenceAnswer = '',
}) {
  const [propMode, setPropMode] = useState('student');
  const [selectedPropId, setSelectedPropId] = useState(null);

  const studentProps = relationsData?.student_propositions || [];
  const referenceProps = relationsData?.reference_propositions || [];

  const activeProps = propMode === 'student' ? studentProps : referenceProps;
  const fullText = propMode === 'student' ? studentAnswer : referenceAnswer;

  useEffect(() => {
    if (activeProps.length > 0) {
      setSelectedPropId(activeProps[0].id);
    } else {
      setSelectedPropId(null);
    }
  }, [propMode, relationsData]);

  const selectedProp = activeProps.find((p) => p.id === selectedPropId) || activeProps[0] || null;

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      <PropositionBar
        propMode={propMode}
        onSwitchPropMode={setPropMode}
        studentCount={studentProps.length}
        referenceCount={referenceProps.length}
        fullText={fullText}
        selectedProp={selectedProp}
      />

      <div className="flex-1 min-h-0 relative w-full overflow-y-auto p-6 md:p-8">
        <div className="max-w-5xl mx-auto flex flex-col gap-4 pb-12 w-full">
          {activeProps.length === 0 ? (
            <div className="py-16 text-center text-[#706b63] font-mono text-xs">
              No clausal propositions extracted for this text.
            </div>
          ) : (
            activeProps.map((prop, idx) => {
              const isSelected = selectedProp?.id === prop.id;

              return (
                <div
                  key={prop.id || idx}
                  onClick={() => setSelectedPropId(prop.id)}
                  className={`rounded-2xl p-5 md:p-6 transition-all cursor-pointer select-none ${
                    isSelected
                      ? 'bg-[#fdfcf9] border-2 border-indigo-700 shadow-sm'
                      : 'bg-[#fdfcf9] border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-2xs'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[13px] font-bold text-indigo-900 tracking-wide">
                        P{idx + 1}
                      </span>
                      <span className="text-[#a89e8f] text-[12px] select-none">—</span>
                      <span className="text-[11.5px] text-[#706b63] font-medium tracking-wide">
                        {prop.representation_type}
                      </span>
                    </div>

                    <span
                      className={`text-[10.5px] font-mono font-semibold px-2.5 py-0.5 rounded border ${
                        prop.polarity === 'NEGATIVE'
                          ? 'bg-rose-50 text-rose-800 border-rose-200'
                          : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      }`}
                    >
                      {prop.polarity}
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
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
