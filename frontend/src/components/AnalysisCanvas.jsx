import React, { useState, useRef, useEffect } from 'react';

export default function AnalysisCanvas({
  analysisData,
  activePhase,
  onPhaseChange,
  onNewAnalysis,
}) {
  const [zoom, setZoom] = useState(100);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showGrid, setShowGrid] = useState(true);

  // Selection state
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [selectedPropositionId, setSelectedPropositionId] = useState(null);
  const [selectedTokenId, setSelectedTokenId] = useState(null);

  const canvasRef = useRef(null);

  // Extract phase payloads safely
  const pInput = analysisData?.phase_01_input || {};
  const pParse = analysisData?.phase_02_parse || {};
  const pRelations = analysisData?.phase_03_relations || {};
  const pMatch = analysisData?.phase_04_match || {};
  const pEntailment = analysisData?.phase_05_entailment || {};
  const pAdditional = analysisData?.phase_06_additional || {};
  const pScore = analysisData?.phase_07_score || {};

  // Auto-select first proposition or node on phase change
  useEffect(() => {
    if (activePhase === '02' && pParse.student_tokens?.length) {
      setSelectedTokenId(pParse.student_tokens[0].id);
    } else if (activePhase === '03' && pRelations.student_propositions?.length) {
      setSelectedPropositionId(pRelations.student_propositions[0].id);
    } else if (activePhase === '04' && pMatch.matched_pairs?.length) {
      setSelectedPropositionId(pMatch.matched_pairs[0].student_id);
    } else if (activePhase === '06' && pAdditional.unmatched_propositions?.length) {
      setSelectedPropositionId(pAdditional.unmatched_propositions[0].id);
    }
  }, [activePhase]);

  // Pan handlers
  const handleMouseDown = (e) => {
    // Only pan if clicking canvas background directly
    if (e.target === canvasRef.current || e.target.classList.contains('canvas-background')) {
      setIsPanning(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isPanning) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleWheel = (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -10 : 10;
      setZoom((prev) => Math.min(180, Math.max(50, prev + delta)));
    }
  };

  const resetView = () => {
    setZoom(100);
    setPan({ x: 0, y: 0 });
  };

  // Student answer with interactive highlights
  const renderHighlightedStudentText = () => {
    const text = pInput.student_answer || '';
    if (!text) return null;

    // Find highlights based on propositions
    const spans = [];
    if (pRelations.student_propositions) {
      pRelations.student_propositions.forEach((p, idx) => {
        if (p.char_start >= 0 && p.char_end > p.char_start) {
          const isMatched = pMatch.matched_student_indices?.includes(p.index);
          spans.push({
            id: p.id,
            start: p.char_start,
            end: p.char_end,
            label: p.text,
            isMatched,
            proposition: p,
          });
        }
      });
    }

    if (spans.length === 0) {
      return <span>{text}</span>;
    }

    // Sort spans by start offset
    spans.sort((a, b) => a.start - b.start);

    const elements = [];
    let lastIdx = 0;

    spans.forEach((span, i) => {
      if (span.start > lastIdx) {
        elements.push(
          <span key={`text_${lastIdx}`} className="text-slate-700">
            {text.substring(lastIdx, span.start)}
          </span>
        );
      }

      const isSelected = selectedPropositionId === span.id;
      let badgeClass = 'bg-indigo-50 text-indigo-800 border-indigo-200 hover:bg-indigo-100';
      if (!span.isMatched) {
        badgeClass = 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100';
      }
      if (isSelected) {
        badgeClass = 'bg-indigo-600 text-white border-indigo-700 ring-2 ring-indigo-200';
      }

      elements.push(
        <button
          key={`span_${span.id}_${i}`}
          onClick={(e) => {
            e.stopPropagation();
            setSelectedPropositionId(span.id);
          }}
          className={`inline-block px-1.5 py-0.5 mx-0.5 rounded text-xs font-medium border transition-all cursor-pointer ${badgeClass}`}
        >
          {text.substring(span.start, span.end)}
        </button>
      );
      lastIdx = span.end;
    });

    if (lastIdx < text.length) {
      elements.push(
        <span key={`text_${lastIdx}`} className="text-slate-700">
          {text.substring(lastIdx)}
        </span>
      );
    }

    return elements;
  };

  return (
    <div className="relative w-full h-[calc(100vh-105px)] overflow-hidden flex flex-col bg-[#fafaf9]">
      {/* Sub-status header under PhaseNav */}
      <div className="w-full px-6 py-1.5 bg-white/90 border-b border-slate-200/70 flex items-center justify-between text-[11px] font-mono text-slate-500">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-indigo-600 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
            MODEL: V5 FINAL PROPOSED ASAG
          </span>
          <span className="text-slate-300">|</span>
          <span>CANONICAL FRAGMENTS: ACTIVE</span>
          <span className="text-slate-300">|</span>
          <span>CONTRADICTION GUARDS: ACTIVE</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-400">
            PROPOSITIONS: {pRelations.student_count || 0} STU / {pRelations.reference_count || 0} REF
          </span>
          <button
            onClick={onNewAnalysis}
            className="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 cursor-pointer"
          >
            ← New Analysis
          </button>
        </div>
      </div>

      {/* Main Spatial Canvas Area */}
      <div
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        className={`relative flex-1 w-full h-full overflow-hidden select-none cursor-grab active:cursor-grabbing ${
          showGrid ? 'dot-grid-canvas' : 'bg-[#fafaf9]'
        }`}
      >
        {/* Spatial Transformation Container */}
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom / 100})`,
            transformOrigin: '0 0',
            transition: isPanning ? 'none' : 'transform 0.08s ease-out',
          }}
          className="absolute inset-0 pointer-events-auto p-8"
        >
          {/* Phase 01: Input Overview */}
          {activePhase === '01' && (
            <div className="max-w-3xl mx-auto mt-6 space-y-5">
              <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-2">
                  01 // QUESTION PROMPT
                </span>
                <p className="text-base text-slate-900 font-medium leading-relaxed">
                  {pInput.question}
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-xs">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-2">
                  02 // REFERENCE ANSWER (GOLD TARGET)
                </span>
                <p className="text-sm text-slate-700 leading-relaxed font-sans">
                  {pInput.reference_answer}
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-indigo-50/40 border-2 border-indigo-500/40 shadow-xs">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-indigo-900 font-semibold">
                    03 // STUDENT SUBMISSION (PRIMARY SUBJECT)
                  </span>
                  <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 text-[10px] font-mono">
                    Candidate For Grading
                  </span>
                </div>
                <p className="text-sm text-slate-900 leading-relaxed font-sans font-medium">
                  {pInput.student_answer}
                </p>
              </div>

              <div className="text-center pt-4">
                <button
                  onClick={() => onPhaseChange('02')}
                  className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-mono font-semibold tracking-wider hover:bg-slate-800 transition-colors shadow-xs"
                >
                  PROCEED TO 02 PARSE →
                </button>
              </div>
            </div>
          )}

          {/* Phase 02: Syntactic Dependency Parse Graph */}
          {activePhase === '02' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-2">
                  SYNTACTIC DEPENDENCY PARSE TREE
                </span>
                <p className="text-xs text-slate-500 mb-4">
                  Tokens parsed via Universal Dependencies (`en_core_web_sm`). Click any token node to inspect its syntactic properties and head governor.
                </p>

                {/* Horizontal Token Flow with Dependency Badges */}
                <div className="flex flex-wrap gap-2 pt-2">
                  {pParse.student_tokens?.map((tok) => {
                    const isSelected = selectedTokenId === tok.id;
                    const isRoot = tok.is_root;
                    return (
                      <div
                        key={tok.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedTokenId(tok.id);
                        }}
                        className={`p-2.5 rounded-xl border text-xs font-mono cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-indigo-600 text-white border-indigo-700 shadow-md ring-4 ring-indigo-100 scale-105'
                            : isRoot
                            ? 'bg-amber-50 text-amber-900 border-amber-300 hover:border-amber-400'
                            : 'bg-white text-slate-800 border-slate-200 hover:border-slate-300 hover:shadow-xs'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 text-[10px] opacity-75 mb-1">
                          <span>{tok.dep}</span>
                          <span>{tok.pos}</span>
                        </div>
                        <div className="font-semibold text-sm">{tok.text}</div>
                        <div className="text-[10px] opacity-70 mt-1">
                          head: {tok.head_text} [{tok.head_index}]
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Dependency Relation List Table */}
              <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs text-xs font-mono">
                <span className="text-[11px] font-semibold text-slate-700 uppercase tracking-wide block mb-3">
                  PARSED DEPENDENCY ARCS ({pParse.student_dependencies?.length || 0})
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {pParse.student_dependencies?.map((dep) => (
                    <div
                      key={dep.id}
                      className="p-2 rounded-lg bg-slate-50 border border-slate-200/60 flex items-center justify-between text-[11px]"
                    >
                      <span className="font-medium text-slate-800">{dep.source_text}</span>
                      <span className="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 text-[10px]">
                        → {dep.label} →
                      </span>
                      <span className="font-medium text-slate-800">{dep.target_text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Phase 03: Relations (Propositions & Syntactic Slots) */}
          {activePhase === '03' && (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Student Propositions */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold">
                    STUDENT PROPOSITIONS ({pRelations.student_count || 0})
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    Subject-Predicate-Object & Hybrid Units
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {pRelations.student_propositions?.map((p) => {
                    const isSelected = selectedPropositionId === p.id;
                    const isMatched = pMatch.matched_student_indices?.includes(p.index);

                    return (
                      <div
                        key={p.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedPropositionId(p.id);
                        }}
                        className={`p-4 rounded-2xl border transition-all cursor-pointer bg-white ${
                          isSelected
                            ? 'border-indigo-600 ring-4 ring-indigo-100 shadow-md'
                            : 'border-slate-200 hover:border-slate-300 hover:shadow-xs'
                        }`}
                      >
                        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-2">
                          <span className="font-semibold text-slate-700">P{p.index + 1} // {p.representation_type}</span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                              isMatched
                                ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            }`}
                          >
                            {isMatched ? 'Matched Core' : 'Unmatched Info'}
                          </span>
                        </div>
                        <div className="text-sm font-semibold text-slate-900 mb-2.5">
                          "{p.text}"
                        </div>
                        <div className="grid grid-cols-3 gap-1.5 text-[11px] font-mono text-slate-600 bg-slate-50 p-2 rounded-lg">
                          <div>
                            <span className="text-[9px] uppercase text-slate-400 block">SUBJ</span>
                            <span className="truncate block font-medium">{p.subject || '—'}</span>
                          </div>
                          <div>
                            <span className="text-[9px] uppercase text-slate-400 block">PRED</span>
                            <span className="truncate block font-medium text-indigo-600">{p.predicate || '—'}</span>
                          </div>
                          <div>
                            <span className="text-[9px] uppercase text-slate-400 block">OBJ</span>
                            <span className="truncate block font-medium">{p.object || '—'}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Reference Propositions */}
              <div className="pt-4 border-t border-slate-200/80">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold block mb-3">
                  REFERENCE PROPOSITIONS ({pRelations.reference_count || 0})
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {pRelations.reference_propositions?.map((p) => (
                    <div
                      key={p.id}
                      className="p-3.5 rounded-xl border border-slate-200 bg-white/70 text-xs font-mono"
                    >
                      <span className="text-[10px] text-slate-400 block mb-1">REF // P{p.index + 1}</span>
                      <div className="text-xs font-semibold text-slate-800 mb-2">"{p.text}"</div>
                      <div className="flex gap-2 text-[10px] text-slate-500">
                        <span>Pred: <strong className="text-slate-700">{p.predicate}</strong></span>
                        {p.object && <span>Obj: <strong className="text-slate-700">{p.object}</strong></span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Phase 04: Bipartite Match */}
          {activePhase === '04' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="flex items-center justify-between text-xs font-mono text-slate-500">
                <span>BIPARTITE ALIGNMENT (ROLE-PRESERVING TRIPLE MATCHING)</span>
                <span>MATCHED: {pMatch.matched_count || 0} | UNMATCHED: {pMatch.unmatched_student_count || 0}</span>
              </div>

              {/* Matched Pairs */}
              <div className="space-y-3">
                {pMatch.matched_pairs?.map((m, i) => (
                  <div
                    key={m.id}
                    className="p-4 rounded-2xl bg-white border border-slate-200/90 shadow-xs grid grid-cols-1 md:grid-cols-12 gap-3 items-center"
                  >
                    <div className="md:col-span-5 text-xs font-mono">
                      <span className="text-[10px] text-slate-400 uppercase tracking-wide block mb-1">
                        REFERENCE PROPOSITION
                      </span>
                      <div className="font-semibold text-slate-900 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        "{m.reference_text}"
                      </div>
                    </div>

                    <div className="md:col-span-2 flex flex-col items-center justify-center text-center">
                      <span className="text-xs font-mono font-semibold text-indigo-600 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full">
                        {(m.triple_score * 100).toFixed(0)}% Match
                      </span>
                      <span className="text-[10px] font-mono text-slate-400 mt-1">
                        {m.match_method}
                      </span>
                      <span className="text-indigo-400 text-lg leading-none mt-0.5">↔</span>
                    </div>

                    <div className="md:col-span-5 text-xs font-mono">
                      <span className="text-[10px] text-indigo-600 font-semibold uppercase tracking-wide block mb-1">
                        STUDENT PROPOSITION
                      </span>
                      <div className="font-semibold text-slate-900 bg-indigo-50/40 p-2.5 rounded-lg border border-indigo-100">
                        "{m.student_text}"
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Unmatched Student Information */}
              {pMatch.unmatched_student_ids?.length > 0 && (
                <div className="p-4 rounded-2xl bg-emerald-50/30 border border-emerald-200 shadow-xs">
                  <span className="text-xs font-mono font-semibold text-emerald-800 uppercase tracking-wide block mb-2">
                    UNMATCHED STUDENT INFORMATION ({pMatch.unmatched_student_ids.length} propositions)
                  </span>
                  <p className="text-xs text-slate-600 mb-3">
                    These assertions do not directly correspond to reference propositions and are passed forward to Phase 06 for additional-information classification.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {pMatch.unmatched_student_ids.map((id) => {
                      const prop = pRelations.student_propositions?.find((p) => p.id === id);
                      return (
                        <span
                          key={id}
                          className="px-3 py-1.5 rounded-lg bg-white border border-emerald-200 text-xs font-mono font-medium text-emerald-900 shadow-xs"
                        >
                          "{prop?.text || id}"
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Phase 05: Entailment */}
          {activePhase === '05' && (
            <div className="max-w-4xl mx-auto space-y-4">
              <div className="text-xs font-mono text-slate-500 uppercase tracking-wide">
                PROPOSITIONAL TEXTUAL ENTAILMENT DECISIONS ({pEntailment.total_evaluated || 0})
              </div>

              {pEntailment.entailment_evaluations?.map((ev, i) => {
                const isEntailed = ev.status === 'ENTAILS';
                const isUncertain = ev.status === 'UNCERTAIN';

                return (
                  <div
                    key={ev.match_id}
                    className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-slate-400">PAIR {i + 1}</span>
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold ${
                            isEntailed
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                              : isUncertain
                              ? 'bg-amber-100 text-amber-800 border border-amber-300'
                              : 'bg-rose-100 text-rose-800 border border-rose-300'
                          }`}
                        >
                          {ev.status}
                        </span>
                      </div>
                      <span className="text-xs font-mono text-slate-500">
                        Confidence: {(ev.confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/60">
                        <span className="text-[10px] text-slate-400 uppercase block mb-1">REFERENCE</span>
                        <div className="font-semibold text-slate-900">"{ev.reference_text}"</div>
                      </div>
                      <div className="p-3 rounded-xl bg-indigo-50/50 border border-indigo-100">
                        <span className="text-[10px] text-indigo-600 uppercase block mb-1">STUDENT</span>
                        <div className="font-semibold text-slate-900">"{ev.student_text}"</div>
                      </div>
                    </div>

                    <div className="p-3 rounded-xl bg-slate-50 text-xs font-sans text-slate-600 flex items-start gap-2">
                      <svg className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>{ev.evidence}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Phase 06: Additional Information */}
          {activePhase === '06' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-200 text-xs text-indigo-900">
                <span className="font-semibold font-mono uppercase block mb-1">
                  RESEARCH EXTENSION: UNMATCHED STUDENT INFORMATION ANALYSIS
                </span>
                <p className="leading-relaxed">
                  Information not directly covered in the instructor's reference answer is evaluated against domain knowledge, question relevance, and contradiction guards rather than being discarded or blindly rewarded.
                </p>
              </div>

              {/* Unmatched Propositions List */}
              <div className="space-y-3">
                {pAdditional.unmatched_propositions?.map((item) => {
                  const isCorrect = item.classification === 'CORRECT_ADDITIONAL';
                  const isIrrelevant = item.classification === 'IRRELEVANT';
                  const isIncorrect = item.classification === 'INCORRECT';

                  return (
                    <div
                      key={item.id}
                      onClick={() => setSelectedPropositionId(item.id)}
                      className="p-5 rounded-2xl bg-white border border-slate-200/90 shadow-xs space-y-3 cursor-pointer hover:border-indigo-300 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 font-mono">
                          <span className="text-xs text-slate-400">UNMATCHED PROPOSITION</span>
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              isCorrect
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : isIrrelevant
                                ? 'bg-slate-100 text-slate-700 border border-slate-300'
                                : isIncorrect
                                ? 'bg-rose-100 text-rose-800 border border-rose-300'
                                : 'bg-amber-100 text-amber-800 border border-amber-300'
                            }`}
                          >
                            {item.classification}
                          </span>
                        </div>
                        <span className="text-xs font-mono font-semibold text-slate-600">
                          Score Effect: {item.score_effect > 0 ? `+${item.score_effect}` : item.score_effect}
                        </span>
                      </div>

                      <div className="text-sm font-semibold text-slate-900 font-sans">
                        "{item.text}"
                      </div>

                      <div className="p-3 rounded-xl bg-slate-50 text-xs font-sans text-slate-600">
                        <span className="font-semibold text-slate-700">Rationale: </span>
                        {item.rationale}
                      </div>
                    </div>
                  );
                })}
              </div>

              {pAdditional.unmatched_propositions?.length === 0 && (
                <div className="p-8 text-center text-xs font-mono text-slate-400 border-2 border-dashed border-slate-200 rounded-2xl">
                  No unmatched student propositions detected. All assertions matched reference concepts.
                </div>
              )}
            </div>
          )}

          {/* Phase 07: Score & Trace */}
          {activePhase === '07' && (
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Score Headline Card */}
              <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-6">
                <div>
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-1">
                    FINAL EVALUATED GRADE
                  </span>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold tracking-tight text-slate-900 font-mono">
                      {pScore.final_grade?.toFixed(2)}
                    </span>
                    <span className="text-lg text-slate-400 font-mono">/ {pScore.max_points?.toFixed(2)}</span>
                  </div>
                  <span className="text-xs text-slate-500 font-mono mt-1 block">
                    Normalized: {(pScore.final_score * 100).toFixed(1)}%
                  </span>
                </div>

                {/* Score Breakdown Pills */}
                <div className="flex flex-wrap gap-3 font-mono text-xs">
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-center min-w-[120px]">
                    <span className="text-[10px] text-slate-400 block uppercase">Base Coverage</span>
                    <span className="font-semibold text-slate-900 text-sm">
                      {pScore.base_grade?.toFixed(2)}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-center min-w-[120px]">
                    <span className="text-[10px] text-emerald-600 block uppercase">Additional Bonus</span>
                    <span className="font-semibold text-emerald-700 text-sm">
                      +{pScore.positive_adjustment?.toFixed(2)}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-center min-w-[120px]">
                    <span className="text-[10px] text-rose-600 block uppercase">Penalty</span>
                    <span className="font-semibold text-rose-700 text-sm">
                      -{pScore.negative_adjustment?.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Itemized Attribution Trace Table */}
              <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-4">
                  PROPOSITION SCORE ATTRIBUTION TRACE
                </span>
                <div className="divide-y divide-slate-100 text-xs font-mono">
                  {pScore.itemized_trace?.map((item, idx) => (
                    <div key={idx} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex-1">
                        <span className="font-semibold text-slate-800 block">"{item.proposition_text}"</span>
                        <span className="text-[11px] text-slate-500 font-sans">{item.rationale}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {item.classification}
                        </span>
                        <span className="font-bold text-slate-900 min-w-[50px] text-right">
                          {item.adjustment_value >= 0 ? `+${item.adjustment_value.toFixed(2)}` : item.adjustment_value.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Floating Student Verbatim Submission Card */}
        <div className="absolute top-6 left-6 z-20 max-w-md w-full glass-panel-elevated rounded-2xl p-4 transition-all">
          <div className="flex items-center justify-between text-[11px] font-mono mb-2">
            <span className="font-semibold text-slate-800 uppercase tracking-wide">
              STUDENT SUBMISSION
            </span>
            <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-[10px]">
              INTERACTIVE
            </span>
          </div>
          <div className="text-xs leading-relaxed text-slate-800 font-sans">
            {renderHighlightedStudentText()}
          </div>
          <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>Click any highlighted span to inspect</span>
            <span>Scale: 5.0</span>
          </div>
        </div>

        {/* Floating Contextual Inspector (Right Panel) */}
        {selectedPropositionId && (
          <div className="absolute top-6 right-6 z-20 w-80 sm:w-96 glass-panel-elevated rounded-2xl p-5 transition-all shadow-xl">
            <div className="flex items-center justify-between text-xs font-mono pb-2 border-b border-slate-100 mb-3">
              <span className="font-semibold text-slate-800 uppercase tracking-wide">
                • PROPOSITION INSPECTOR
              </span>
              <button
                onClick={() => setSelectedPropositionId(null)}
                className="text-slate-400 hover:text-slate-700 cursor-pointer font-bold text-sm"
              >
                ✕
              </button>
            </div>

            {/* Content for selected proposition */}
            {(() => {
              const prop =
                pRelations.student_propositions?.find((p) => p.id === selectedPropositionId) ||
                pAdditional.unmatched_propositions?.find((p) => p.id === selectedPropositionId);

              if (!prop) {
                return <div className="text-xs text-slate-400">Select an element to inspect.</div>;
              }

              const match = pMatch.matched_pairs?.find((m) => m.student_id === prop.id);
              const isMatched = !!match;

              return (
                <div className="space-y-3.5 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase block mb-1">
                      EXTRACTED STUDENT STATEMENT
                    </span>
                    <div className="font-semibold text-slate-900 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      "{prop.text}"
                    </div>
                  </div>

                  {isMatched ? (
                    <div>
                      <span className="text-[10px] text-indigo-600 uppercase font-semibold block mb-1">
                        MATCHED REFERENCE TARGET
                      </span>
                      <div className="font-medium text-slate-800 bg-indigo-50/50 p-2.5 rounded-lg border border-indigo-100">
                        "{match.reference_text}"
                      </div>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <div className="p-2 rounded bg-slate-50 border border-slate-100">
                          <span className="text-[9px] text-slate-400 block">Alignment Score</span>
                          <span className="font-bold text-slate-900">{(match.triple_score * 100).toFixed(0)}%</span>
                        </div>
                        <div className="p-2 rounded bg-slate-50 border border-slate-100">
                          <span className="text-[9px] text-slate-400 block">Method</span>
                          <span className="font-bold text-slate-900">{match.match_method}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <span className="text-[10px] text-emerald-600 uppercase font-semibold block mb-1">
                        UNMATCHED CLASSIFICATION
                      </span>
                      <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 font-medium">
                        {prop.classification || 'UNMATCHED (Analyzed by Model D2)'}
                      </div>
                      {prop.rationale && (
                        <div className="text-[11px] text-slate-600 mt-2 font-sans bg-slate-50 p-2 rounded">
                          {prop.rationale}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Provenance: Clausal / Hybrid Unit</span>
                    <span className="text-indigo-600 font-medium">Verified</span>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {/* Floating Bottom-Left Canvas Controls */}
        <div className="absolute bottom-6 left-6 z-20 flex items-center gap-1.5 p-1 rounded-xl bg-white/95 border border-slate-200/90 shadow-md text-xs font-mono">
          <button
            onClick={() => setZoom((z) => Math.min(180, z + 10))}
            className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center font-bold text-slate-700 cursor-pointer"
            title="Zoom In"
          >
            +
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(50, z - 10))}
            className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center font-bold text-slate-700 cursor-pointer"
            title="Zoom Out"
          >
            −
          </button>
          <button
            onClick={resetView}
            className="px-2.5 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-700 font-medium cursor-pointer"
            title="Fit / Reset View"
          >
            Fit
          </button>
          <button
            onClick={() => setShowGrid((g) => !g)}
            className={`px-2.5 h-8 rounded-lg flex items-center justify-center font-medium cursor-pointer ${
              showGrid ? 'bg-indigo-50 text-indigo-700' : 'hover:bg-slate-100 text-slate-700'
            }`}
            title="Toggle Grid"
          >
            Grid
          </button>
          <span className="px-2 text-[11px] text-slate-400">{zoom}%</span>
        </div>

        {/* Bottom Legend */}
        <div className="absolute bottom-6 right-6 z-20 hidden md:flex items-center gap-4 text-[11px] font-mono text-slate-500 p-2 px-3 rounded-xl bg-white/90 border border-slate-200 shadow-xs">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-indigo-600 rounded" /> Matched Core
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-500 rounded" /> Additional Info
          </span>
          <span className="text-slate-300">|</span>
          <span className="text-slate-400">UNIVERSAL DEPENDENCY + ASAG EVALUATOR</span>
        </div>
      </div>
    </div>
  );
}
