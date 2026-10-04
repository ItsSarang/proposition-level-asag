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

  const currentPreset = PRESETS.find((p) => p.id === selectedPresetId);

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-8 flex flex-col items-center">
      {/* Top Header Section */}
      <div className="text-center mb-8">
        <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900 mb-2">
          Grade a Short Answer
        </h1>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          Inspect how a student's answer is interpreted, matched, and scored through interpretable dependency and proposition analysis.
        </p>
      </div>

      {/* Preset / Input Controls Bar */}
      <div className="w-full mb-4 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="inline-flex rounded-xl bg-slate-100 p-1 border border-slate-200/80">
          <button
            type="button"
            onClick={() => handleSelectPreset(selectedPresetId)}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium flex items-center gap-1.5 transition-all ${
              !isCustomMode
                ? 'bg-white text-slate-900 shadow-xs'
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
            className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium flex items-center gap-1.5 transition-all ${
              isCustomMode
                ? 'bg-white text-slate-900 shadow-xs'
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
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            {!isCustomMode ? 'Benchmark Preset Loaded' : 'Custom Input Mode'}
          </span>
        </div>
      </div>

      {/* Preset Selector Dropdown Bar */}
      {!isCustomMode && (
        <div className="w-full mb-6 p-3 rounded-xl bg-white border border-slate-200/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate-500">
            <span className="text-[11px] uppercase tracking-wider text-slate-400">BENCHMARK CORPUS:</span>
            <select
              value={selectedPresetId}
              onChange={(e) => handleSelectPreset(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1 text-slate-800 font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              {PRESETS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title} ({p.domain.split('//')[1]?.trim() || 'CS'})
                </option>
              ))}
            </select>
          </div>
          <span className="text-slate-400 text-[11px]">Standard NLP Reference Set</span>
        </div>
      )}

      {/* Error / Validation Notification */}
      {error && (
        <div className="w-full mb-6 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-mono flex items-center gap-2">
          <svg className="w-4 h-4 text-rose-500 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" x2="12" y1="8" y2="12" />
            <line x1="12" x2="12.01" y1="16" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Central Input Document Card */}
      <div className="w-full bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
        {/* 01 // QUESTION */}
        <div className="p-6 transition-colors focus-within:bg-slate-50/50">
          <div className="flex items-center justify-between text-xs font-mono mb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">01 //</span>
              <span className="font-semibold text-slate-700 uppercase tracking-wide">QUESTION</span>
            </div>
            <span className="text-slate-400 text-[11px]">Prompt / Query</span>
          </div>
          <div className="relative pl-3 border-l-2 border-slate-200 focus-within:border-slate-400 transition-colors">
            <textarea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter the question prompt..."
              className="w-full bg-transparent text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none resize-y leading-relaxed font-sans"
            />
          </div>
        </div>

        {/* 02 // REFERENCE ANSWER */}
        <div className="p-6 transition-colors focus-within:bg-slate-50/50">
          <div className="flex items-center justify-between text-xs font-mono mb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">02 //</span>
              <span className="font-semibold text-slate-700 uppercase tracking-wide">REFERENCE ANSWER</span>
            </div>
            <span className="text-slate-400 text-[11px]">Gold Ground Truth</span>
          </div>
          <div className="relative pl-3 border-l-2 border-slate-200 focus-within:border-slate-400 transition-colors">
            <textarea
              rows={3}
              value={referenceAnswer}
              onChange={(e) => setReferenceAnswer(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter the instructor reference answer..."
              className="w-full bg-transparent text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none resize-y leading-relaxed font-sans"
            />
          </div>
        </div>

        {/* 03 // STUDENT ANSWER */}
        <div className="p-6 bg-indigo-50/20 transition-colors focus-within:bg-indigo-50/40">
          <div className="flex items-center justify-between text-xs font-mono mb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-indigo-500 font-medium">03 //</span>
              <span className="font-semibold text-indigo-900 uppercase tracking-wide">STUDENT ANSWER</span>
              <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 text-[10px] font-mono">
                Primary Subject
              </span>
            </div>
            <span className="text-slate-400 text-[11px]">Candidate Text Area</span>
          </div>
          <div className="relative pl-3 border-l-2 border-indigo-600 transition-colors">
            <textarea
              rows={4}
              value={studentAnswer}
              onChange={(e) => setStudentAnswer(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter the student's answer to inspect..."
              className="w-full bg-transparent text-sm text-slate-900 font-medium placeholder:text-slate-400 focus:outline-none resize-y leading-relaxed font-sans"
            />
          </div>
        </div>
      </div>

      {/* Action Button at Bottom */}
      <div className="mt-8 flex flex-col items-center gap-3">
        <button
          type="button"
          onClick={onAnalyze}
          disabled={isLoading}
          className={`px-7 py-3 rounded-xl bg-slate-900 text-white font-mono text-xs font-semibold tracking-wider uppercase shadow-md transition-all flex items-center gap-3 ${
            isLoading
              ? 'opacity-70 cursor-wait'
              : 'hover:bg-slate-800 hover:shadow-indigo-500/20 hover:ring-2 hover:ring-indigo-500/40 active:scale-[0.98]'
          }`}
        >
          {isLoading ? (
            <>
              <svg className="animate-spin w-4 h-4 text-indigo-400" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>Analyzing Answer...</span>
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

        <p className="text-[11px] font-mono text-slate-400">
          Universal Dependencies • Clausal Triples • Bipartite Entailment • Model D2
        </p>
      </div>
    </div>
  );
}
