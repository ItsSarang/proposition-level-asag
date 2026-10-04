import React, { useState, useEffect } from 'react';
import { PRESETS } from '../data/presets';

export default function WorkbenchInput({
  question,
  setQuestion,
  referenceAnswer,
  setReferenceAnswer,
  studentAnswer,
  setStudentAnswer,
  onAnalyze,
  isLoading,
  error,
}) {
  const [selectedPresetId, setSelectedPresetId] = useState('polymorphism');
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [copiedField, setCopiedField] = useState(null);

  // Set initial preset on load
  useEffect(() => {
    if (!question && !referenceAnswer && !studentAnswer) {
      const initial = PRESETS.find((p) => p.id === 'polymorphism') || PRESETS[0];
      setQuestion(initial.question);
      setReferenceAnswer(initial.referenceAnswer);
      setStudentAnswer(initial.studentAnswer);
    }
  }, []);

  const handleSelectPreset = (presetId) => {
    setSelectedPresetId(presetId);
    setIsCustomMode(false);
    const preset = PRESETS.find((p) => p.id === presetId);
    if (preset) {
      setQuestion(preset.question);
      setReferenceAnswer(preset.referenceAnswer);
      setStudentAnswer(preset.studentAnswer);
    }
  };

  const handleCustomModeToggle = () => {
    setIsCustomMode(true);
  };

  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      onAnalyze();
    }
  };

  const copyToClipboard = (text, fieldName) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 1800);
  };

  const appendCondition = (snippet) => {
    const trimmed = studentAnswer.trim();
    if (!trimmed) {
      setStudentAnswer(snippet.trim());
    } else if (trimmed.endsWith('.')) {
      setStudentAnswer(`${trimmed.slice(0, -1)} ${snippet}.`);
    } else {
      setStudentAnswer(`${trimmed} ${snippet}`);
    }
    setIsCustomMode(true);
  };

  const currentPreset = PRESETS.find((p) => p.id === selectedPresetId);

  // Live text metrics
  const qWords = question.trim() ? question.trim().split(/\s+/).length : 0;
  const rWords = referenceAnswer.trim() ? referenceAnswer.trim().split(/\s+/).length : 0;
  const sWords = studentAnswer.trim() ? studentAnswer.trim().split(/\s+/).length : 0;
  const sClauses = studentAnswer.trim()
    ? Math.max(1, (studentAnswer.match(/\b(and|or|but|because|which|that|who|while|where|although)\b/gi) || []).length + 1)
    : 0;

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-5 flex flex-col items-center">
      {/* Preset / Input Controls Bar */}
      <div className="w-full mb-3 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5">
        <div className="inline-flex rounded-xl bg-slate-100/90 p-1 border border-slate-200/80 shadow-2xs">
          <button
            type="button"
            onClick={() => handleSelectPreset(selectedPresetId)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium flex items-center gap-1.5 transition-all cursor-pointer ${
              !isCustomMode
                ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <svg className="w-3.5 h-3.5 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect width="7" height="7" x="3" y="3" rx="1" />
              <rect width="7" height="7" x="14" y="3" rx="1" />
              <rect width="7" height="7" x="14" y="14" rx="1" />
              <rect width="7" height="7" x="3" y="14" rx="1" />
            </svg>
            Sample Presets
          </button>
          <button
            type="button"
            onClick={handleCustomModeToggle}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium flex items-center gap-1.5 transition-all cursor-pointer ${
              isCustomMode
                ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <svg className="w-3.5 h-3.5 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
            </svg>
            Custom Input
          </button>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            {!isCustomMode ? 'Benchmark Preset Loaded' : 'Custom Query Mode'}
          </span>
        </div>
      </div>

      {/* Preset Selector Dropdown Bar & Quick Preset Chips */}
      {!isCustomMode && (
        <div className="w-full mb-4 space-y-2">
          {/* Dropdown Select Bar */}
          <div className="w-full p-2.5 px-3.5 rounded-xl bg-white border border-slate-200/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
            <div className="flex items-center gap-2.5 text-slate-500 flex-1">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">BENCHMARK CORPUS:</span>
              <select
                value={selectedPresetId}
                onChange={(e) => handleSelectPreset(e.target.value)}
                className="bg-slate-50 border border-slate-200/90 rounded-lg px-3 py-1.5 text-slate-800 font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500 text-xs flex-1 max-w-md"
              >
                {PRESETS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </select>
            </div>
            <span className="text-slate-400 text-[11px] hidden sm:inline">Standard NLP Reference Set</span>
          </div>

          {/* Quick Preset Badges */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider shrink-0 mr-1">Quick Select:</span>
            {PRESETS.map((p) => {
              const isSelected = selectedPresetId === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleSelectPreset(p.id)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all shrink-0 cursor-pointer border ${
                    isSelected
                      ? 'bg-indigo-600 text-white border-indigo-700 shadow-xs'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:text-slate-900'
                  }`}
                >
                  {p.title}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Error / Validation Notification */}
      {error && (
        <div className="w-full mb-4 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-mono flex items-center gap-2.5 shadow-2xs">
          <svg className="w-4 h-4 text-rose-500 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" x2="12" y1="8" y2="12" />
            <line x1="12" x2="12.01" y1="16" y2="16" />
          </svg>
          <span className="flex-1">{error}</span>
        </div>
      )}

      {/* Central Input Document Card */}
      <div className="w-full bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden divide-y divide-slate-100">
        {/* 01 // QUESTION */}
        <div className="p-5 sm:p-6 transition-colors focus-within:bg-slate-50/30">
          <div className="flex items-center justify-between text-xs font-mono mb-2">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">01 //</span>
              <span className="font-semibold text-slate-700 uppercase tracking-wide">QUESTION</span>
            </div>
            <div className="flex items-center gap-3 text-slate-400 text-[11px]">
              <span>Prompt / Query</span>
              <button
                type="button"
                onClick={() => copyToClipboard(question, 'question')}
                className="hover:text-slate-600 cursor-pointer transition-colors"
                title="Copy Question"
              >
                {copiedField === 'question' ? '✓ Copied' : 'Copy'}
              </button>
            </div>
          </div>
          <div className="relative pl-4 border-l-2 border-slate-200 focus-within:border-slate-400 transition-colors">
            <textarea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter the question prompt..."
              className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none resize-y leading-relaxed font-sans"
            />
            <div className="text-[10px] font-mono text-slate-400 mt-1 flex justify-between">
              <span>Length: {qWords} words • {question.length} chars</span>
            </div>
          </div>
        </div>

        {/* 02 // REFERENCE ANSWER */}
        <div className="p-5 sm:p-6 transition-colors focus-within:bg-slate-50/30">
          <div className="flex items-center justify-between text-xs font-mono mb-2">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">02 //</span>
              <span className="font-semibold text-slate-700 uppercase tracking-wide">REFERENCE ANSWER</span>
            </div>
            <div className="flex items-center gap-3 text-slate-400 text-[11px]">
              <span>Gold Ground Truth</span>
              <button
                type="button"
                onClick={() => copyToClipboard(referenceAnswer, 'ref')}
                className="hover:text-slate-600 cursor-pointer transition-colors"
                title="Copy Reference"
              >
                {copiedField === 'ref' ? '✓ Copied' : 'Copy'}
              </button>
            </div>
          </div>
          <div className="relative pl-4 border-l-2 border-slate-200 focus-within:border-slate-400 transition-colors">
            <textarea
              rows={3}
              value={referenceAnswer}
              onChange={(e) => setReferenceAnswer(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter the instructor reference answer..."
              className="w-full bg-transparent text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none resize-y leading-relaxed font-sans"
            />
            <div className="text-[10px] font-mono text-slate-400 mt-1 flex justify-between">
              <span>Instructor Target: {rWords} words • {referenceAnswer.length} chars</span>
            </div>
          </div>
        </div>

        {/* 03 // STUDENT ANSWER */}
        <div className="p-5 sm:p-6 transition-colors">
          <div className="flex items-center justify-between text-xs font-mono mb-2">
            <div className="flex items-center gap-2">
              <span className="text-indigo-600 font-medium">03 //</span>
              <span className="font-semibold text-indigo-900 uppercase tracking-wide">STUDENT ANSWER</span>
              <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] font-mono font-medium">
                Primary Subject
              </span>
            </div>
            <div className="flex items-center gap-3 text-slate-400 text-[11px]">
              <span>Candidate Text Area</span>
              <button
                type="button"
                onClick={() => setStudentAnswer('')}
                className="hover:text-rose-600 cursor-pointer transition-colors"
                title="Clear input"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="relative pl-4 border-l-2 border-indigo-600 transition-colors">
            <div className="bg-[#fafaf9]/90 border border-slate-200/80 rounded-xl p-3.5 focus-within:border-indigo-400 focus-within:bg-white focus-within:shadow-xs transition-all">
              <textarea
                rows={4}
                value={studentAnswer}
                onChange={(e) => setStudentAnswer(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter the student's answer to inspect..."
                className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none resize-y leading-relaxed font-sans"
              />
            </div>

            {/* Quick Hypothesis Modifiers */}
            <div className="mt-2.5 flex flex-wrap items-center gap-1.5 text-[11px] font-mono">
              <span className="text-slate-400 text-[10px] uppercase tracking-wider mr-1">
                Inject Research Condition:
              </span>
              <button
                type="button"
                onClick={() => appendCondition('and cannot contain NULL values')}
                className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition-colors cursor-pointer text-[10px]"
                title="Append correct additional domain knowledge"
              >
                + Correct Extra
              </button>
              <button
                type="button"
                onClick={() => appendCondition('and can contain duplicate values')}
                className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors cursor-pointer text-[10px]"
                title="Append contradictory misconception"
              >
                + Misconception
              </button>
              <button
                type="button"
                onClick={() => appendCondition('SQL was developed in the 1970s')}
                className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 hover:bg-slate-200 transition-colors cursor-pointer text-[10px]"
                title="Append irrelevant domain statement"
              >
                + Irrelevant Extra
              </button>
            </div>

            <div className="text-[10px] font-mono text-slate-400 mt-2 flex items-center justify-between">
              <span>Tokens: {sWords} words • {studentAnswer.length} characters</span>
              <span className="text-indigo-600 font-medium">Clausal Structure: ~{sClauses} proposition units</span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Button & Telemetry */}
      <div className="mt-7 flex flex-col items-center gap-3">
        <button
          type="button"
          onClick={onAnalyze}
          disabled={isLoading}
          className={`px-8 py-3 rounded-xl bg-[#0f172a] text-white font-mono text-xs font-semibold tracking-wider uppercase shadow-md transition-all flex items-center gap-3 cursor-pointer ${
            isLoading
              ? 'opacity-80 cursor-wait ring-2 ring-indigo-500/50'
              : 'hover:bg-slate-800 hover:shadow-indigo-500/20 active:scale-[0.98]'
          }`}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Executing ASAG Pipeline...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 2v4" />
                <path d="m4.93 4.93 2.83 2.83" />
                <path d="M2 12h4" />
                <path d="m4.93 19.07 2.83-2.83" />
                <path d="M12 18v4" />
                <path d="m16.24 16.24 2.83 2.83" />
                <path d="M18 12h4" />
                <path d="m16.24 7.76 2.83-2.83" />
              </svg>
              <span>ANALYZE ANSWER</span>
              <span className="ml-1 px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 border border-slate-700">
                ⌘ Enter
              </span>
            </>
          )}
        </button>

        {isLoading && (
          <div className="flex items-center gap-2 text-[10px] font-mono text-indigo-600 bg-indigo-50/70 border border-indigo-100 rounded-full px-3 py-1">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping" />
            <span>Universal Dependencies → Clausal Triples → Bipartite Match → Entailment → Score</span>
          </div>
        )}
      </div>
    </div>
  );
}
