import { useState, useEffect } from 'react';
import { PRESETS } from '../data/presets';

export default function WorkbenchCard({
  onAnalyze,
  loading = false,
  statusMessage = '',
  initialInput = null,
}) {
  const [selectedPresetId, setSelectedPresetId] = useState(
    initialInput?.presetId || 'none'
  );
  const [question, setQuestion] = useState(initialInput?.question || '');
  const [referenceAnswer, setReferenceAnswer] = useState(
    initialInput?.referenceAnswer || ''
  );
  const [studentAnswer, setStudentAnswer] = useState(
    initialInput?.studentAnswer || ''
  );
  const [customInputs, setCustomInputs] = useState({
    question: initialInput?.question || '',
    referenceAnswer: initialInput?.referenceAnswer || '',
    studentAnswer: initialInput?.studentAnswer || '',
  });

  useEffect(() => {
    if (initialInput) {
      if (initialInput.presetId) {
        setSelectedPresetId(initialInput.presetId);
      }
      if (initialInput.question !== undefined) {
        setQuestion(initialInput.question);
      }
      if (initialInput.referenceAnswer !== undefined) {
        setReferenceAnswer(initialInput.referenceAnswer);
      }
      if (initialInput.studentAnswer !== undefined) {
        setStudentAnswer(initialInput.studentAnswer);
      }
      if (initialInput.presetId === 'none' || !initialInput.presetId) {
        setCustomInputs({
          question: initialInput.question || '',
          referenceAnswer: initialInput.referenceAnswer || '',
          studentAnswer: initialInput.studentAnswer || '',
        });
      }
    }
  }, [initialInput]);

  function handleSelectPreset(presetId) {
    setSelectedPresetId(presetId);
    if (presetId === 'none') {
      setQuestion(customInputs.question);
      setReferenceAnswer(customInputs.referenceAnswer);
      setStudentAnswer(customInputs.studentAnswer);
      return;
    }

    const preset = PRESETS.find((p) => p.id === presetId);
    if (preset) {
      setQuestion(preset.question);
      setReferenceAnswer(preset.referenceAnswer);
      setStudentAnswer(preset.studentAnswer);
    }
  }

  function handleQuestionChange(val) {
    setQuestion(val);
    if (selectedPresetId === 'none') {
      setCustomInputs((prev) => ({ ...prev, question: val }));
    }
  }

  function handleRefChange(val) {
    setReferenceAnswer(val);
    if (selectedPresetId === 'none') {
      setCustomInputs((prev) => ({ ...prev, referenceAnswer: val }));
    }
  }

  function handleStudentChange(val) {
    setStudentAnswer(val);
    if (selectedPresetId === 'none') {
      setCustomInputs((prev) => ({ ...prev, studentAnswer: val }));
    }
  }

  function handleKeyDown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleSubmit() {
    if (loading || !question.trim() || !studentAnswer.trim()) return;
    if (onAnalyze) {
      onAnalyze({
        question,
        referenceAnswer,
        studentAnswer,
        presetId: selectedPresetId,
      });
    }
  }

  const isSubmitDisabled =
    loading || !question.trim() || !studentAnswer.trim();

  return (
    <div className="w-full flex flex-col items-center select-none">
      <div className="bg-[#fdfcf9] rounded-2xl border border-[#dfd8c8] shadow-[0_4px_24px_-4px_rgba(50,40,30,0.06)] overflow-hidden w-full max-w-[880px] p-7 sm:p-9 flex flex-col gap-5">
        <div className="flex flex-col gap-1.5">
          <label className="text-[11px] font-mono uppercase tracking-wider text-[#706b63] font-semibold">
            Evaluation Preset
          </label>
          <div className="relative w-full">
            <select
              value={selectedPresetId}
              onChange={(e) => handleSelectPreset(e.target.value)}
              className="w-full appearance-none pl-3.5 pr-10 py-2.5 bg-[#faf8f4] hover:bg-[#f4f0e8] border border-[#dfd8c8] rounded-xl text-[13px] font-sans text-[#1e1c19] font-medium focus:outline-none focus:ring-2 focus:ring-indigo-600/20 focus:border-indigo-600 transition-all cursor-pointer"
            >
              {PRESETS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-[#8c8477]">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-[11px] font-mono uppercase tracking-wider text-[#706b63] font-semibold">
            QUESTION
          </label>
          <div className="rounded-xl p-3.5 sm:p-4 bg-[#faf8f4] border border-[#dfd8c8] focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
            <textarea
              rows={2}
              value={question}
              onChange={(e) => handleQuestionChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter evaluation question or prompt..."
              className="w-full bg-transparent text-[15px] sm:text-[15.5px] text-[#1e1c19] leading-relaxed placeholder:text-[#9e9484] focus:outline-none resize-none border-none p-0 font-sans"
            />
          </div>
        </div>

        <div className="w-full h-px bg-[#dfd8c8]" />

        <div className="flex flex-col gap-1.5">
          <label className="text-[11px] font-mono uppercase tracking-wider text-[#706b63] font-semibold">
            REFERENCE ANSWER
          </label>
          <div className="rounded-xl p-3.5 sm:p-4 bg-[#faf8f4] border border-[#dfd8c8] focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
            <textarea
              rows={3}
              value={referenceAnswer}
              onChange={(e) => handleRefChange(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter reference answer for ground truth semantic comparison..."
              className="w-full bg-transparent text-[14px] sm:text-[14.5px] text-[#2c2925] leading-relaxed placeholder:text-[#9e9484] focus:outline-none resize-none border-none p-0 font-sans"
            />
          </div>
        </div>

        <div className="w-full h-px bg-[#dfd8c8]" />

        <div className="flex flex-col gap-1.5">
          <label className="text-[11px] font-mono uppercase tracking-wider text-[#706b63] font-semibold">
            STUDENT ANSWER
          </label>
          <div className="rounded-xl p-3.5 sm:p-4 bg-[#faf8f4] border border-[#dfd8c8] focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
            <textarea
              rows={4}
              value={studentAnswer}
              onChange={(e) => handleStudentChange(e.target.value)}
              onKeyDown={handleKeyDown}
              spellCheck="false"
              placeholder="Enter candidate student response to evaluate against reference ground truth..."
              className="w-full bg-transparent text-[14px] sm:text-[14.5px] text-[#1e1c19] leading-relaxed placeholder:text-[#9e9484] focus:outline-none resize-none border-none p-0 font-sans"
            />
          </div>
        </div>

        <div className="flex items-center justify-end pt-1">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitDisabled}
            className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-mono text-[12.5px] font-semibold shadow-xs transition-all duration-200 ${
              isSubmitDisabled
                ? 'bg-[#ded7c7] text-[#8c8477] cursor-not-allowed'
                : 'bg-[#1e1c19] hover:bg-[#343029] text-[#f7f4ed] cursor-pointer active:scale-[0.98]'
            }`}
          >
            <span>Analyze Answer</span>
            <span>→</span>
          </button>
        </div>

        {loading && statusMessage && (
          <div className="pt-2 border-t border-[#dfd8c8] flex items-center justify-center text-xs font-mono text-[#706b63] gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-700 animate-pulse" />
            <span>{statusMessage}</span>
          </div>
        )}
      </div>
    </div>
  );
}
