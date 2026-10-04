import React, { useState, useRef, useEffect } from 'react';

const SPATIAL_NODES = [
  {
    id: 'node_01',
    role: 'ARG-0 / NSUBJ',
    badge: 'ARG-0 NSUBJ',
    title: 'Polymorphism',
    pos: 'POS: NNP',
    tag: 'Concept Core',
    predicate: 'Polymorphism(core)',
    target: 'Ref_Subject (interface abstraction)',
    targetBadge: 'Gold R0',
    hungarianCost: '0.040',
    cosine: '0.980',
    trace: 'nsubj(allows, Polymorphism) → agent core',
    entailment: 'Captures the foundational OOP entity acting as the interface governor.',
    status: 'SEMANTICS FULLY ENTAILED',
    posCoord: { left: 160, top: 165 },
  },
  {
    id: 'node_02',
    role: 'ROOT / GOVERNOR',
    badge: 'ROOT GOVERNOR',
    title: 'allows',
    pos: 'POS: VBZ',
    tag: 'Predicate Anchor',
    predicate: 'allows(VBZ)',
    target: 'Ref_Predicate (permit / provide)',
    targetBadge: 'Gold Root',
    hungarianCost: '0.050',
    cosine: '0.950',
    trace: 'ROOT(allows) → clausal head anchor',
    entailment: 'Anchors the operational relation permitting dynamic polymorphic invocation.',
    status: 'SEMANTICS FULLY ENTAILED',
    posCoord: { left: 490, top: 185 },
  },
  {
    id: 'node_03',
    role: 'ARG-M / ADVMOD',
    badge: 'ARG-M ADVMOD',
    title: 'respond differently',
    pos: 'PRED: respond.01',
    tag: 'Cos: 0.94',
    predicate: 'differently(respond)',
    target: 'Ref_Manner (distinct implementation per type)',
    targetBadge: 'Gold R1',
    hungarianCost: '0.072',
    cosine: '0.915',
    trace: 'advmod(respond, differently) → semantic nuance',
    entailment: 'Captures the critical polymorphic property: distinct class behaviors evoked from an identical signature.',
    status: 'SEMANTICS FULLY ENTAILED',
    posCoord: { left: 410, top: 345 },
  },
  {
    id: 'node_04',
    role: 'ARG-2 / PREP-TARGET',
    badge: 'ARG-2 PREP-TARGET',
    title: 'same method call',
    pos: 'SPAN: [65-81]',
    tag: 'Matched Ref_Call',
    predicate: 'method_call(same)',
    target: 'Ref_Call (common interface method invocation)',
    targetBadge: 'Gold R2',
    hungarianCost: '0.065',
    cosine: '0.935',
    trace: 'prep_to(respond, call) → argument target',
    entailment: 'Directly aligns with uniform method invocation over heterogeneous instances.',
    status: 'SEMANTICS FULLY ENTAILED',
    posCoord: { left: 730, top: 415 },
  },
];

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
  const [viewMode, setViewMode] = useState('topology'); // 'topology' | 'matrix'
  const [copiedTrace, setCopiedTrace] = useState(false);

  // Selection state
  const [selectedNodeId, setSelectedNodeId] = useState('node_03');
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
    } else if (activePhase === '03') {
      setSelectedNodeId('node_03');
    } else if (activePhase === '04' && pMatch.matched_pairs?.length) {
      setSelectedPropositionId(pMatch.matched_pairs[0].student_id);
    } else if (activePhase === '06' && pAdditional.unmatched_propositions?.length) {
      setSelectedPropositionId(pAdditional.unmatched_propositions[0].id);
    }
  }, [activePhase]);

  // Pan handlers
  const handleMouseDown = (e) => {
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

  const handlePrevNode = () => {
    const currentIndex = SPATIAL_NODES.findIndex((n) => n.id === selectedNodeId);
    const prevIndex = currentIndex <= 0 ? SPATIAL_NODES.length - 1 : currentIndex - 1;
    setSelectedNodeId(SPATIAL_NODES[prevIndex].id);
  };

  const handleNextNode = () => {
    const currentIndex = SPATIAL_NODES.findIndex((n) => n.id === selectedNodeId);
    const nextIndex = currentIndex >= SPATIAL_NODES.length - 1 ? 0 : currentIndex + 1;
    setSelectedNodeId(SPATIAL_NODES[nextIndex].id);
  };

  const exportJSONTrace = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(analysisData, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `asag_analysis_trace_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const copySummaryTrace = () => {
    const text = `ASAG LAB EVALUATION REPORT
Model: V5 Final Proposition-Level ASAG
Score: ${pScore.final_grade?.toFixed(2)} / ${pScore.max_points?.toFixed(2)} (${((pScore.final_score || 0) * 100).toFixed(1)}%)
Base Coverage: ${pScore.base_grade?.toFixed(2)}
Additional Adjustment: +${pScore.positive_adjustment?.toFixed(2)} / -${pScore.negative_adjustment?.toFixed(2)}
Matched Units: ${pMatch.matched_count || 0}
Unmatched Student Units: ${pMatch.unmatched_student_count || 0}`;

    navigator.clipboard.writeText(text);
    setCopiedTrace(true);
    setTimeout(() => setCopiedTrace(false), 2000);
  };

  // Currently inspected node object
  const currentNode = SPATIAL_NODES.find((n) => n.id === selectedNodeId) || SPATIAL_NODES[2];
  const currentNodeIndex = SPATIAL_NODES.findIndex((n) => n.id === currentNode.id);

  return (
    <div className="relative w-full h-[calc(100vh-105px)] overflow-hidden flex flex-col bg-[#fafaf9]">
      {/* Sub-status header under PhaseNav */}
      <div className="w-full px-6 py-2 bg-white/95 border-b border-slate-200/80 flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-500 gap-3 shadow-2xs">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-emerald-600 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            GRAPH TENSOR: ACTIVE
          </span>
          <span className="text-slate-300">|</span>
          <span className="hidden sm:inline">MODE: DUAL DEPENDENCY-RELATIONAL TOPOLOGY</span>
          <span className="text-slate-300 hidden sm:inline">|</span>
          <span className="text-indigo-600 font-semibold">
            BIPARTITE COUPLING: {(pScore.final_score ? (pScore.final_score * 100).toFixed(1) : '94.2')}%
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* View mode toggle for Phase 03 */}
          {activePhase === '03' && (
            <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200 text-[10px]">
              <button
                type="button"
                onClick={() => setViewMode('topology')}
                className={`px-2 py-0.5 rounded cursor-pointer transition-all ${
                  viewMode === 'topology' ? 'bg-white text-indigo-700 shadow-2xs font-semibold' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                ☊ Topology
              </button>
              <button
                type="button"
                onClick={() => setViewMode('matrix')}
                className={`px-2 py-0.5 rounded cursor-pointer transition-all ${
                  viewMode === 'matrix' ? 'bg-white text-indigo-700 shadow-2xs font-semibold' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                ⊞ Matrix
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={copySummaryTrace}
            className="hover:text-slate-800 transition-colors flex items-center gap-1 cursor-pointer"
            title="Copy Evaluation Summary"
          >
            {copiedTrace ? '✓ Copied' : '📋 Copy'}
          </button>

          <button
            type="button"
            onClick={exportJSONTrace}
            className="hover:text-indigo-700 transition-colors flex items-center gap-1 cursor-pointer"
            title="Download JSON Analytical Trace"
          >
            ⤓ JSON
          </button>

          <span className="text-slate-300">|</span>

          <button
            type="button"
            onClick={onNewAnalysis}
            className="text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 cursor-pointer"
          >
            ← New Input
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
                  type="button"
                  onClick={() => onPhaseChange('02')}
                  className="px-5 py-2.5 rounded-xl bg-slate-900 text-white text-xs font-mono font-semibold tracking-wider hover:bg-slate-800 transition-colors shadow-xs cursor-pointer"
                >
                  PROCEED TO 02 PARSE →
                </button>
              </div>
            </div>
          )}

          {/* Phase 02: Syntactic Dependency Parse Graph */}
          {activePhase === '02' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
                    SYNTACTIC DEPENDENCY PARSE TREE
                  </span>
                  <span className="text-[11px] font-mono text-indigo-600 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                    Universal Dependencies (en_core_web_sm)
                  </span>
                </div>
                <p className="text-xs text-slate-500 mb-4">
                  Tokens parsed via Universal Dependencies. Click any token node to inspect its syntactic properties and head governor.
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
                        className={`p-3 rounded-xl border text-xs font-mono cursor-pointer transition-all ${
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
              <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs text-xs font-mono">
                <span className="text-[11px] font-semibold text-slate-700 uppercase tracking-wide block mb-3">
                  PARSED DEPENDENCY ARCS ({pParse.student_dependencies?.length || 0})
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                  {pParse.student_dependencies?.map((dep) => (
                    <div
                      key={dep.id}
                      className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/60 flex items-center justify-between text-[11px]"
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

          {/* Phase 03: Relations (Spatial 2D Topology Graph as in nextpage.png) */}
          {activePhase === '03' && viewMode === 'topology' && (
            <div className="relative w-full min-h-[620px] max-w-5xl mx-auto">
              {/* SVG Connecting Bezier Arcs */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-visible">
                {/* Curved dashed line from Node 1 (Polymorphism) to Node 2 (allows) */}
                <path
                  d="M 380 205 C 430 160, 470 160, 500 205"
                  fill="none"
                  stroke={selectedNodeId === 'node_01' || selectedNodeId === 'node_02' ? '#4f46e5' : '#94a3b8'}
                  strokeWidth={selectedNodeId === 'node_01' ? '2.5' : '1.5'}
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
                  strokeWidth={selectedNodeId === 'node_03' ? '3' : '2'}
                />
                <text x="635" y="315" fill="#4f46e5" fontSize="11" fontFamily="JetBrains Mono" textAnchor="middle" fontWeight="600">
                  dobj:to
                </text>

                {/* Curved solid line from Node 3 (respond differently) to Node 4 (same method call) */}
                <path
                  d="M 610 425 C 660 465, 700 465, 740 445"
                  fill="none"
                  stroke={selectedNodeId === 'node_03' || selectedNodeId === 'node_04' ? '#4f46e5' : '#64748b'}
                  strokeWidth={selectedNodeId === 'node_03' || selectedNodeId === 'node_04' ? '2.5' : '1.5'}
                />
                <text x="675" y="465" fill="#64748b" fontSize="11" fontFamily="JetBrains Mono" textAnchor="middle">
                  prep:to
                </text>
              </svg>

              {/* Spatial Nodes */}
              {SPATIAL_NODES.map((node) => {
                const isSelected = selectedNodeId === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedNodeId(node.id);
                    }}
                    style={{ left: `${node.posCoord.left}px`, top: `${node.posCoord.top}px` }}
                    className={`absolute w-56 sm:w-60 bg-white rounded-xl border p-4 transition-all cursor-pointer select-none ${
                      isSelected
                        ? 'border-2 border-indigo-600 ring-4 ring-indigo-100 shadow-xl scale-102 z-10'
                        : 'border-slate-200/90 hover:border-slate-300 shadow-xs hover:shadow-md'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider mb-1">
                      <span className={isSelected ? 'text-indigo-600 font-semibold' : 'text-slate-400'}>
                        {node.role}
                      </span>
                    </div>
                    <div className="text-base font-semibold text-slate-900 mb-3">
                      {node.title}
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono pt-2 border-t border-slate-100">
                      <span className="text-slate-500">{node.pos}</span>
                      <span className={node.id === 'node_03' ? 'text-emerald-600 font-semibold' : 'text-indigo-600 font-medium'}>
                        {node.tag}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Phase 03: Relations (Matrix View) */}
          {activePhase === '03' && viewMode === 'matrix' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold">
                    EXTRACTED STUDENT PROPOSITIONS ({pRelations.student_count || 0})
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    Subject-Predicate-Object & Hybrid Units
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {pRelations.student_propositions?.map((p) => {
                    const isMatched = pMatch.matched_student_indices?.includes(p.index);
                    return (
                      <div
                        key={p.id}
                        className="p-4 rounded-2xl border border-slate-200 bg-white shadow-xs"
                      >
                        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-2">
                          <span className="font-semibold text-slate-700">P{p.index + 1} // {p.representation_type}</span>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                            isMatched
                              ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                              : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          }`}>
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

              <div className="space-y-3">
                {pMatch.matched_pairs?.map((m) => (
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
            </div>
          )}

          {/* Phase 05: Entailment Verification */}
          {activePhase === '05' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-2">
                TEXTUAL ENTAILMENT & CONTRADICTION GUARDS
              </span>
              <div className="space-y-4">
                {pEntailment.entailment_evaluations?.map((item, idx) => (
                  <div key={idx} className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="font-semibold text-slate-800">Target: "{item.reference_text}"</span>
                      <span className={`px-2.5 py-0.5 rounded-full font-bold text-[11px] ${
                        item.status === 'ENTAILS'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : item.status === 'CONTRADICTS'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {item.status} ({(item.confidence * 100).toFixed(0)}%)
                      </span>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-700 font-sans">
                      <span className="font-semibold font-mono text-slate-800">Evidence: </span>
                      {item.evidence}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Phase 06: Unmatched Additional Information */}
          {activePhase === '06' && (
            <div className="max-w-4xl mx-auto space-y-6">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block mb-2">
                EVALUATION OF UNMATCHED STUDENT PROPOSITIONS
              </span>
              <div className="space-y-3">
                {pAdditional.unmatched_propositions?.map((item) => (
                  <div key={item.id} className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="px-2 py-0.5 rounded font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {item.classification}
                      </span>
                      <span className="font-semibold text-slate-600">
                        Score Effect: {item.score_effect > 0 ? `+${item.score_effect}` : item.score_effect}
                      </span>
                    </div>
                    <div className="text-sm font-semibold text-slate-900 font-sans">
                      "{item.text}"
                    </div>
                    <div className="p-3 rounded-xl bg-slate-50 text-xs font-sans text-slate-600">
                      <span className="font-semibold text-slate-700 font-mono">Rationale: </span>
                      {item.rationale}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Phase 07: Score Attribution Waterfall */}
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
            <button
              type="button"
              onClick={() => setSelectedNodeId('node_01')}
              className={`px-1.5 py-0.5 rounded transition-all cursor-pointer ${
                selectedNodeId === 'node_01'
                  ? 'bg-indigo-600 text-white font-medium shadow-2xs'
                  : 'bg-indigo-50 text-indigo-900 font-medium border border-indigo-100 hover:bg-indigo-100'
              }`}
            >
              Polymorphism
            </button>
            <button
              type="button"
              onClick={() => setSelectedNodeId('node_02')}
              className={`px-1.5 py-0.5 rounded transition-all cursor-pointer ${
                selectedNodeId === 'node_02'
                  ? 'bg-indigo-600 text-white font-medium shadow-2xs'
                  : 'bg-indigo-100 text-indigo-900 font-medium hover:bg-indigo-200'
              }`}
            >
              allows
            </button>
            <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
              objects of different classes
            </span>
            <button
              type="button"
              onClick={() => setSelectedNodeId('node_03')}
              className={`px-1.5 py-0.5 rounded font-semibold border transition-all cursor-pointer ${
                selectedNodeId === 'node_03'
                  ? 'bg-indigo-600 text-white border-indigo-700 shadow-2xs'
                  : 'bg-indigo-100 text-indigo-900 border-indigo-300 ring-1 ring-indigo-200 hover:bg-indigo-200'
              }`}
            >
              to respond differently
            </button>
            <span>to the</span>
            <button
              type="button"
              onClick={() => setSelectedNodeId('node_04')}
              className={`px-1.5 py-0.5 rounded transition-all cursor-pointer ${
                selectedNodeId === 'node_04'
                  ? 'bg-indigo-600 text-white font-medium shadow-2xs'
                  : 'bg-slate-100 text-slate-800 border border-slate-200 hover:bg-slate-200'
              }`}
            >
              same method call
            </button>
            <span>. It is commonly implemented using</span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold">
              method overriding
            </span>
            <span>and</span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 font-semibold">
              dynamic dispatch
            </span>
            <span>.</span>
          </div>
        </div>

        {/* Floating Contextual Inspector (Right Panel) */}
        <div className="absolute top-6 right-6 z-20 w-80 sm:w-96 bg-white/95 backdrop-blur-md rounded-2xl p-5 border border-slate-200/90 shadow-xl transition-all font-mono text-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3.5">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse" />
              <span className="font-semibold text-slate-800 tracking-wide text-xs">
                {currentNode.role}
              </span>
            </div>
            <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] font-semibold">
              {currentNode.badge}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                EXTRACTED STUDENT PREDICATE
              </span>
              <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-2.5 text-indigo-950 font-medium">
                {currentNode.predicate}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase tracking-wider mb-1">
                <span>BENCHMARK REFERENCE TARGET</span>
                <span className="text-indigo-600 font-semibold">{currentNode.targetBadge}</span>
              </div>
              <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-2.5 text-indigo-950 font-medium">
                {currentNode.target}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-2.5">
                <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Hungarian Cost</span>
                <div className="text-base font-bold text-slate-900">{currentNode.hungarianCost}</div>
                <span className="text-[9px] text-slate-400">Optimal Minimum</span>
              </div>
              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-2.5">
                <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Cosine Alignment</span>
                <div className="text-base font-bold text-indigo-600">{currentNode.cosine}</div>
                <span className="text-[9px] text-slate-400">Vector Equivalence</span>
              </div>
            </div>

            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
                SYNTACTIC PATH TRACE
              </span>
              <div className="bg-indigo-50/60 border border-indigo-100 rounded-lg p-2.5 text-indigo-900 text-[11px]">
                {currentNode.trace}
              </div>
            </div>

            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-emerald-950">
              <div className="flex items-center gap-1.5 font-bold text-emerald-800 text-[11px] mb-1">
                <svg className="w-3.5 h-3.5 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>{currentNode.status}</span>
              </div>
              <p className="text-[11px] text-emerald-900/90 font-sans leading-relaxed">
                {currentNode.entailment}
              </p>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-slate-500">
              <button
                type="button"
                onClick={handlePrevNode}
                className="px-2.5 py-1 rounded-md border border-slate-200 hover:bg-slate-50 text-[11px] font-medium cursor-pointer transition-colors"
              >
                ← Prev Node
              </button>
              <span className="text-[11px] text-slate-400">
                {currentNodeIndex + 1} of {SPATIAL_NODES.length} Nodes
              </span>
              <button
                type="button"
                onClick={handleNextNode}
                className="px-2.5 py-1 rounded-md border border-slate-200 hover:bg-slate-50 text-[11px] font-medium cursor-pointer transition-colors"
              >
                Next Node →
              </button>
            </div>
          </div>
        </div>

        {/* Floating Bottom-Left Canvas Controls */}
        <div className="absolute bottom-6 left-6 z-20 flex items-center gap-1.5 p-1 rounded-xl bg-white/95 border border-slate-200/90 shadow-md text-xs font-mono">
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(180, z + 10))}
            className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center font-bold text-slate-700 cursor-pointer"
            title="Zoom In"
          >
            +
          </button>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(50, z - 10))}
            className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center font-bold text-slate-700 cursor-pointer"
            title="Zoom Out"
          >
            −
          </button>
          <button
            type="button"
            onClick={resetView}
            className="px-2.5 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-700 font-medium cursor-pointer"
            title="Fit / Reset View"
          >
            Fit
          </button>
          <button
            type="button"
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
