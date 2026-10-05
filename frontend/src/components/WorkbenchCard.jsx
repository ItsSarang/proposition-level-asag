import { useState, useEffect } from 'react';
import { PRESETS } from '../data/presets';

export default function WorkbenchCard({ onAnalyze, loading = false, statusMessage = '' }) {
  const [selectedPresetId, setSelectedPresetId] = useState(PRESETS[0]?.id || 'primary_key');
  const [question, setQuestion] = useState('');
  const [referenceAnswer, setReferenceAnswer] = useState('');
  const [studentAnswer, setStudentAnswer] = useState('');
  const [activeSection, setActiveSection] = useState('student');

  useEffect(() => {
    loadPreset(PRESETS[0]?.id || 'primary_key');
  }, []);

  function loadPreset(id) {
    const p = PRESETS.find((x) => x.id === id) || PRESETS[0];
    if (!p) return;
    setSelectedPresetId(p.id);
    setQuestion(p.question);
    setReferenceAnswer(p.referenceAnswer);
    setStudentAnswer(p.studentAnswer);
  }

  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      if (onAnalyze) {
        onAnalyze({ question, referenceAnswer, studentAnswer });
      }
    }
  }

  function handleSubmit() {
    if (onAnalyze) {
      onAnalyze({ question, referenceAnswer, studentAnswer });
    }
  }

  return (
    <div className="w-full flex flex-col items-center">
      <div className="flex items-center gap-3.5 px-5 py-3 bg-[#fdfcf9] border border-[#dfd8c8] rounded-xl shadow-2xs mb-5 w-full">
        <span className="text-[11px] font-mono uppercase tracking-wider text-[#8c8477] font-medium whitespace-nowrap">
          Evaluation Preset:
        </span>
        <div className="relative flex-1 max-w-lg">
          <select
            value={selectedPresetId}
            onChange={(e) => loadPreset(e.target.value)}
            className="w-full appearance-none pl-3.5 pr-8 py-2 bg-[#faf8f4] hover:bg-[#f4f0e8] border border-[#dfd8c8] rounded-lg text-[12.5px] font-sans text-[#1e1c19] font-medium focus:outline-none focus:ring-1 focus:ring-indigo-600 transition-all cursor-pointer"
          >
            {PRESETS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#8c8477]">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>

      <section className="bg-[#fdfcf9] rounded-2xl border border-[#dfd8c8] shadow-[0_4px_24px_-4px_rgba(50,40,30,0.06)] overflow-hidden w-full transition-all">
        <div className="p-8 sm:p-10 flex flex-col gap-7">
          <div
            className={`relative pl-6 border-l-2 transition-colors duration-200 ${
              activeSection === 'question'
                ? 'border-indigo-700'
                : 'border-[#dfd8c8]'
            }`}
          >
            <div className="mb-2.5">
              <span
                className={`text-[11.5px] font-mono uppercase tracking-wider font-semibold transition-colors duration-200 ${
                  activeSection === 'question'
                    ? 'text-indigo-800'
                    : 'text-[#706b63]'
                }`}
              >
                Question
              </span>
            </div>
            <div
              className={`rounded-xl p-4 sm:p-5 transition-all duration-200 border ${
                activeSection === 'question'
                  ? 'border-indigo-500 bg-[#faf8f4] ring-2 ring-indigo-100 shadow-xs'
                  : 'bg-[#f7f4ed] border-[#dcd5c5] hover:border-[#b8af9f]'
              }`}
            >
              <textarea
                rows={2}
                value={question}
                onFocus={() => setActiveSection('question')}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter evaluation question or prompt..."
                className="w-full bg-transparent text-[16px] sm:text-[17px] text-[#1e1c19] leading-relaxed placeholder:text-[#9e9484] focus:outline-none resize-none border-none p-0 font-sans"
              />
            </div>
          </div>

          <div className="h-px w-full bg-[#dfd8c8]" />

          <div
            className={`relative pl-6 border-l-2 transition-colors duration-200 ${
              activeSection === 'reference'
                ? 'border-indigo-700'
                : 'border-[#dfd8c8]'
            }`}
          >
            <div className="mb-2.5">
              <span
                className={`text-[11.5px] font-mono uppercase tracking-wider font-semibold transition-colors duration-200 ${
                  activeSection === 'reference'
                    ? 'text-indigo-800'
                    : 'text-[#706b63]'
                }`}
              >
                Reference Answer
              </span>
            </div>
            <div
              className={`rounded-xl p-4 sm:p-5 transition-all duration-200 border ${
                activeSection === 'reference'
                  ? 'border-indigo-500 bg-[#faf8f4] ring-2 ring-indigo-100 shadow-xs'
                  : 'bg-[#f7f4ed] border-[#dcd5c5] hover:border-[#b8af9f]'
              }`}
            >
              <textarea
                rows={3}
                value={referenceAnswer}
                onFocus={() => setActiveSection('reference')}
                onChange={(e) => setReferenceAnswer(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter reference answer for ground truth semantic comparison..."
                className="w-full bg-transparent text-[14px] sm:text-[14.5px] text-[#2c2925] leading-relaxed placeholder:text-[#9e9484] focus:outline-none resize-none border-none p-0 font-sans"
              />
            </div>
          </div>

          <div className="h-px w-full bg-[#dfd8c8]" />

          <div
            className={`relative pl-6 border-l-2 transition-colors duration-200 ${
              activeSection === 'student'
                ? 'border-indigo-700'
                : 'border-[#dfd8c8]'
            }`}
          >
            <div className="mb-2.5">
              <span
                className={`text-[11.5px] font-mono uppercase tracking-wider font-semibold transition-colors duration-200 ${
                  activeSection === 'student'
                    ? 'text-indigo-800'
                    : 'text-[#706b63]'
                }`}
              >
                Student Answer
              </span>
            </div>
            <div
              className={`rounded-xl p-4 sm:p-5 transition-all duration-200 border ${
                activeSection === 'student'
                  ? 'border-indigo-500 bg-[#faf8f4] ring-2 ring-indigo-100 shadow-xs'
                  : 'bg-[#f7f4ed] border-[#dcd5c5] hover:border-[#b8af9f]'
              }`}
            >
              <textarea
                rows={4}
                value={studentAnswer}
                onFocus={() => setActiveSection('student')}
                onChange={(e) => setStudentAnswer(e.target.value)}
                onKeyDown={handleKeyDown}
                spellCheck="false"
                placeholder="Enter candidate student response to evaluate against reference ground truth..."
                className="w-full bg-transparent text-[14px] sm:text-[14.5px] text-[#1e1c19] leading-relaxed placeholder:text-[#9e9484] focus:outline-none resize-none border-none p-0 font-sans min-h-[96px]"
              />
            </div>
          </div>

          <div className="pt-2 flex flex-col items-center gap-3">
            <button
              type="button"
              onClick={handleSubmit}
              className="inline-flex items-center justify-center px-10 py-3.5 rounded-xl bg-[#1e1c19] hover:bg-[#343029] text-[#f7f4ed] font-mono text-[12px] uppercase tracking-wider font-semibold shadow-md transition-all duration-200 cursor-pointer active:scale-[0.98]"
            >
              Analyze Answer
            </button>

            {loading && statusMessage && (
              <div className="w-full pt-3 mt-1 border-t border-[#dfd8c8] flex items-center justify-center text-xs font-mono text-[#706b63] gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-700 animate-pulse" />
                <span>{statusMessage}</span>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
