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
  const [selectedNodeId, setSelectedNodeId] = useState('node_03');
  const [selectedPropositionId, setSelectedPropositionId] = useState('prop_manner');
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
      <div className="w-full px-6 py-2 bg-white/90 border-b border-slate-200/70 flex items-center justify-between text-[11px] font-mono text-slate-500">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-emerald-600 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            GRAPH TENSOR: ACTIVE
          </span>
          <span className="text-slate-300">|</span>
          <span>MODE: DUAL DEPENDENCY-RELATIONAL TOPOLOGY</span>
          <span className="text-slate-300">|</span>
          <span className="text-indigo-600 font-medium">
            BIPARTITE COUPLING: {(pScore.final_score ? (pScore.final_score * 100).toFixed(1) : '94.2')}%
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-400">
            PROPOSITIONS: {pRelations.student_count || 4} STU / {pRelations.reference_count || 3} REF
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
          {/* Phase 03: Relations (Spatial 2D Topology Graph as in nextpage.png) */}
          {activePhase === '03' && (
            <div className="relative w-full min-h-[620px] max-w-5xl mx-auto">
              {/* SVG Connecting Bezier Arcs */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-visible">
                {/* Curved dashed line from Node 1 (Polymorphism) to Node 2 (allows) */}
                <path
                  d="M 380 205 C 430 160, 470 160, 500 205"
                  fill="none"
                  stroke="#94a3b8"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />
                <text x="445" y="170" fill="#64748b" fontSize="11" fontFamily="JetBrains Mono" textAnchor="middle">
                  nsubj
                </text>

                {/* Curved solid line from Node 2 (allows) to Node 3 (respond differently) */}
                <path
                  d="M 610 250 C 650 300, 600 350, 540 365"
                  fill="none"
                  stroke="#4f46e5"
                  strokeWidth="2"
                />
                <text x="635" y="315" fill="#4f46e5" fontSize="11" fontFamily="JetBrains Mono" textAnchor="middle" fontWeight="500">
                  dobj:to
                </text>

                {/* Curved solid line from Node 3 (respond differently) to Node 4 (same method call) */}
                <path
                  d="M 610 425 C 660 465, 700 465, 740 445"
                  fill="none"
                  stroke="#64748b"
                  strokeWidth="1.5"
                />
                <text x="675" y="465" fill="#64748b" fontSize="11" fontFamily="JetBrains Mono" textAnchor="middle">
                  prep:to
                </text>
              </svg>

              {/* Spatial Node 1: ARG-0 / NSUBJ */}
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId('node_01');
                }}
                style={{ left: '160px', top: '165px' }}
                className={`absolute w-56 bg-white rounded-xl border p-4 shadow-xs transition-all cursor-pointer select-none ${
                  selectedNodeId === 'node_01'
                    ? 'border-indigo-600 ring-4 ring-indigo-100 shadow-md scale-102'
                    : 'border-slate-200/90 hover:border-slate-300'
                }`}
              >
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">
                  ARG-0 / NSUBJ
                </div>
                <div className="text-base font-semibold text-slate-900 mb-3">
                  Polymorphism
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-100">
                  <span>POS: NNP</span>
                  <span className="text-indigo-600 font-medium">Concept Core</span>
                </div>
              </div>

              {/* Spatial Node 2: ROOT / GOVERNOR */}
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId('node_02');
                }}
                style={{ left: '490px', top: '185px' }}
                className={`absolute w-52 bg-white rounded-xl border p-4 shadow-xs transition-all cursor-pointer select-none ${
                  selectedNodeId === 'node_02'
                    ? 'border-indigo-600 ring-4 ring-indigo-100 shadow-md scale-102'
                    : 'border-slate-200/90 hover:border-slate-300'
                }`}
              >
                <div className="text-[10px] font-mono uppercase tracking-wider text-indigo-600 font-semibold mb-1">
                  ROOT / GOVERNOR
                </div>
                <div className="text-base font-semibold text-slate-900">
                  allows <span className="text-slate-400 font-mono text-xs font-normal">[VBZ]</span>
                </div>
              </div>

              {/* Spatial Node 3: ARG-M / ADVMOD (Highlighted with halo in nextpage.png) */}
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId('node_03');
                }}
                style={{ left: '410px', top: '345px' }}
                className={`absolute w-60 bg-white rounded-xl border-2 p-4 transition-all cursor-pointer select-none ${
                  selectedNodeId === 'node_03' || !selectedNodeId
                    ? 'border-indigo-600 ring-4 ring-indigo-100/70 shadow-lg scale-102'
                    : 'border-slate-200/90 hover:border-slate-300 shadow-xs'
                }`}
              >
                <div className="text-[10px] font-mono uppercase tracking-wider text-indigo-600 font-semibold mb-1">
                  ARG-M / ADVMOD
                </div>
                <div className="text-base font-semibold text-slate-900 mb-3">
                  respond differently
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono pt-2 border-t border-slate-100">
                  <span className="text-slate-500">PRED: respond.01</span>
                  <span className="text-emerald-600 font-semibold">Cos: 0.94</span>
                </div>
              </div>

              {/* Spatial Node 4: ARG-2 / PREP-TARGET */}
              <div
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId('node_04');
                }}
                style={{ left: '730px', top: '415px' }}
                className={`absolute w-56 bg-white rounded-xl border p-4 shadow-xs transition-all cursor-pointer select-none ${
                  selectedNodeId === 'node_04'
                    ? 'border-indigo-600 ring-4 ring-indigo-100 shadow-md scale-102'
                    : 'border-slate-200/90 hover:border-slate-300'
                }`}
              >
                <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1">
                  ARG-2 / PREP-TARGET
                </div>
                <div className="text-base font-semibold text-slate-900 mb-3">
                  same method call
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono pt-2 border-t border-slate-100">
                  <span className="text-slate-500">SPAN: [65-81]</span>
                  <span className="text-indigo-600 font-medium">Matched Ref_Call</span>
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
        <div className="absolute top-6 left-6 z-20 max-w-md w-full bg-white/95 backdrop-blur-md rounded-2xl p-4 border border-slate-200/90 shadow-md transition-all">
          <div className="flex items-center justify-between text-[11px] font-mono mb-2.5">
            <span className="font-semibold text-slate-700 tracking-wide">
              STUDENT VERBATIM SUBMISSION [SCIENTSBANK // ID: CS-3012]
            </span>
            <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] font-semibold">
              TOKEN MATCH: 89.4%
            </span>
          </div>
          <div className="text-xs leading-relaxed text-slate-800 font-sans flex flex-wrap items-center gap-1">
            <span className="px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-900 font-medium border border-indigo-100">Polymorphism</span>
            <span className="px-1.5 py-0.5 rounded bg-indigo-600 text-white font-medium">allows</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">objects of different classes</span>
            <span className="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-900 border border-indigo-300 font-semibold ring-1 ring-indigo-200">to respond differently</span>
            <span>to the</span>
            <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">same method call</span>
            <span>. It is commonly implemented using</span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold">method overriding</span>
            <span>and</span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold">dynamic dispatch</span>
            <span>.</span>
          </div>
        </div>

        {/* Floating Contextual Inspector (Right Panel) */}
        <div className="absolute top-6 right-6 z-20 w-80 sm:w-96 bg-white/95 backdrop-blur-md rounded-2xl p-5 border border-slate-200/90 shadow-xl transition-all font-mono text-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3.5">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse" />
              <span className="font-semibold text-slate-800 tracking-wide text-xs">
                PROPOSITION P1 — MANNER MODIFIER
              </span>
            </div>
            <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] font-semibold">
              ARG-M ADVMOD
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                EXTRACTED STUDENT PREDICATE
              </span>
              <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-2.5 text-indigo-950 font-medium">
                differently(respond)
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                <span>BENCHMARK REFERENCE TARGET</span>
                <span className="text-indigo-600 font-semibold">Gold R1</span>
              </div>
              <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-2.5 text-indigo-950 font-medium">
                Ref_Manner (distinct implementation per type)
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-2.5">
                <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Hungarian Cost</span>
                <div className="text-base font-bold text-slate-900">0.072</div>
                <span className="text-[9px] text-slate-400">Optimal Minimum</span>
              </div>
              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-2.5">
                <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Cosine Alignment</span>
                <div className="text-base font-bold text-indigo-600">0.915</div>
                <span className="text-[9px] text-slate-400">Vector Equivalence</span>
              </div>
            </div>

            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                SYNTACTIC PATH TRACE
              </span>
              <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-2.5 text-indigo-900 text-[11px]">
                advmod(respond, differently) → semantic nuance
              </div>
            </div>

            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-emerald-950">
              <div className="flex items-center gap-1.5 font-bold text-emerald-800 text-[11px] mb-1">
                <svg className="w-3.5 h-3.5 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>SEMANTICS FULLY ENTAILED</span>
              </div>
              <p className="text-[11px] text-emerald-900/90 font-sans leading-relaxed">
                Captures the critical polymorphic property: distinct class behaviors evoked from an identical signature.
              </p>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-slate-500">
              <button
                type="button"
                className="px-2.5 py-1 rounded-md border border-slate-200 hover:bg-slate-50 text-[11px] font-medium cursor-pointer"
              >
                ← Prev Node
              </button>
              <span className="text-[11px] text-slate-400">4 of 7 Nodes</span>
              <button
                type="button"
                className="px-2.5 py-1 rounded-md border border-slate-200 hover:bg-slate-50 text-[11px] font-medium cursor-pointer"
              >
                Next Node →
              </button>
            </div>
          </div>
        </div>

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
        <div className="absolute bottom-6 right-6 z-20 hidden md:flex items-center gap-4 text-[11px] font-mono text-slate-500 p-2 px-3.5 rounded-xl bg-white/95 border border-slate-200/90 shadow-xs">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-indigo-600 rounded" /> Exact Match
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-500 rounded" /> Validated Synthesis
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 border-t border-dashed border-slate-400" /> Syntactic Parent
          </span>
          <span className="text-slate-300">|</span>
          <span className="text-slate-600 font-medium">SCIENTSBANK 3-WAY ASAG EVALUATOR</span>
        </div>
      </div>
    </div>
  );
}
