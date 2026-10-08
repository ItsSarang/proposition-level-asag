import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import AlignmentBar from './AlignmentBar';

function formatMatchType(method) {
  if (!method) return 'Similarity Match';
  const m = method.toLowerCase();
  if (m === 'exact_triple' || m === 'exact_match') return 'Exact Triple';
  if (m === 'lemma_triple' || m === 'lemma_match') return 'Lemma Triple';
  if (m === 'semantic_synonym_triple') return 'Semantic Synonym';
  if (m === 'semantic_path_triple') return 'Semantic Path Similarity';
  if (m === 'partial_structural_match') return 'Structural Match';
  if (m === 'weighted_slots') return 'Weighted Slot Alignment';
  return method.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function getMatchLabel(pair) {
  const method = (pair.match_method || '').toLowerCase();
  const pct = Math.round((pair.triple_score || 0) * 100);
  let typeLabel = 'MATCH';
  if (method === 'exact_triple' || method === 'exact_match') {
    typeLabel = 'EXACT MATCH';
  } else if (method === 'lemma_triple' || method === 'lemma_match') {
    typeLabel = 'LEMMA MATCH';
  } else if (
    method === 'semantic_synonym_triple' ||
    method === 'semantic_path_triple' ||
    method === 'weighted_slots' ||
    method.includes('semantic')
  ) {
    typeLabel = 'SEMANTIC MATCH';
  } else if (method.includes('structural') || method.includes('partial')) {
    typeLabel = 'STRUCTURAL MATCH';
  }
  return `${typeLabel} · ${pct}%`;
}

function getMatchExplanation(pair) {
  if (pair.explanation) return pair.explanation;
  const m = (pair.match_method || '').toLowerCase();
  if (m === 'exact_triple' || m === 'exact_match') {
    return 'All three proposition roles align with exact lexical match.';
  }
  if (m === 'lemma_triple' || m === 'lemma_match') {
    return 'Proposition roles align via morphological lemma equivalence.';
  }
  if (m.includes('semantic') || m.includes('synonym') || m.includes('path')) {
    return 'Proposition arguments align via WordNet semantic taxonomy similarity exceeding threshold.';
  }
  return 'Subject and predicate arguments align above the semantic matching threshold.';
}

export default function AlignmentPhase({
  matchData,
  relationsData,
  studentAnswer = '',
  referenceAnswer = '',
  parseMode = 'student',
  onSwitchParseMode,
}) {
  const [answerMode, setAnswerMode] = useState(parseMode || 'student');
  const [hoveredMatchId, setHoveredMatchId] = useState(null);
  const [selectedMatchId, setSelectedMatchId] = useState(null);
  const [hoveredPropId, setHoveredPropId] = useState(null);
  const [selectedPropId, setSelectedPropId] = useState(null);
  const [selectedUnmatchedProp, setSelectedUnmatchedProp] = useState(null);

  const [animStage, setAnimStage] = useState('STEP_4_SETTLED');
  const [revealedMatchCount, setRevealedMatchCount] = useState(0);
  const [showUnmatchedStatus, setShowUnmatchedStatus] = useState(true);
  const [anchors, setAnchors] = useState({});

  const canvasBoxRef = useRef(null);
  const studentCardRefs = useRef({});
  const referenceCardRefs = useRef({});

  const matchedPairs = useMemo(() => matchData?.matched_pairs || [], [matchData]);
  const studentProps = useMemo(() => relationsData?.student_propositions || [], [relationsData]);
  const referenceProps = useMemo(() => relationsData?.reference_propositions || [], [relationsData]);

  const matchedStudentIds = useMemo(
    () => new Set(matchedPairs.map((p) => p.student_id)),
    [matchedPairs]
  );
  const matchedReferenceIds = useMemo(
    () => new Set(matchedPairs.map((p) => p.reference_id)),
    [matchedPairs]
  );

  useEffect(() => {
    if (parseMode && parseMode !== answerMode) {
      setAnswerMode(parseMode);
    }
  }, [parseMode]);

  const handleSwitchAnswerMode = (mode) => {
    setAnswerMode(mode);
    if (onSwitchParseMode) {
      onSwitchParseMode(mode);
    }
  };

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (mediaQuery.matches) {
      setAnimStage('STEP_4_SETTLED');
      setRevealedMatchCount(matchedPairs.length);
      setShowUnmatchedStatus(true);
      return;
    }

    setAnimStage('STEP_0_ENTER');
    setRevealedMatchCount(0);
    setShowUnmatchedStatus(false);

    const timers = [];

    const tScan = setTimeout(() => {
      setAnimStage('STEP_1_SCAN');
    }, 320);
    timers.push(tScan);

    matchedPairs.forEach((_, idx) => {
      const tMatch = setTimeout(() => {
        setAnimStage('STEP_2_CONNECTING');
        setRevealedMatchCount(idx + 1);
      }, 580 + idx * 280);
      timers.push(tMatch);
    });

    const unmatchedDelay = 580 + matchedPairs.length * 280 + 140;
    const tUnmatched = setTimeout(() => {
      setAnimStage('STEP_3_UNMATCHED');
      setShowUnmatchedStatus(true);
    }, unmatchedDelay);
    timers.push(tUnmatched);

    const settledDelay = unmatchedDelay + 260;
    const tSettled = setTimeout(() => {
      setAnimStage('STEP_4_SETTLED');
    }, settledDelay);
    timers.push(tSettled);

    return () => {
      timers.forEach(clearTimeout);
    };
  }, [matchData, relationsData, matchedPairs]);

  const updateAnchors = useCallback(() => {
    if (!canvasBoxRef.current) return;
    const boxRect = canvasBoxRef.current.getBoundingClientRect();
    const newAnchors = {};

    studentProps.forEach((p) => {
      const el = studentCardRefs.current[p.id];
      if (el) {
        const r = el.getBoundingClientRect();
        newAnchors[p.id] = {
          x: r.right - boxRect.left,
          y: r.top - boxRect.top + r.height / 2,
        };
      }
    });

    referenceProps.forEach((p) => {
      const el = referenceCardRefs.current[p.id];
      if (el) {
        const r = el.getBoundingClientRect();
        newAnchors[p.id] = {
          x: r.left - boxRect.left,
          y: r.top - boxRect.top + r.height / 2,
        };
      }
    });

    setAnchors(newAnchors);
  }, [studentProps, referenceProps]);

  useEffect(() => {
    updateAnchors();
    const rafId = requestAnimationFrame(updateAnchors);
    const handleResize = () => updateAnchors();
    window.addEventListener('resize', handleResize);

    let ro = null;
    if (typeof ResizeObserver !== 'undefined' && canvasBoxRef.current) {
      ro = new ResizeObserver(updateAnchors);
      ro.observe(canvasBoxRef.current);
    }

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('resize', handleResize);
      if (ro) ro.disconnect();
    };
  }, [updateAnchors, studentProps, referenceProps, matchedPairs, animStage]);

  const activeSelection = useMemo(() => {
    const activeMatchId = hoveredMatchId || selectedMatchId;
    if (activeMatchId) {
      const match = matchedPairs.find((m) => m.id === activeMatchId);
      if (match) {
        return {
          matchId: match.id,
          studentId: match.student_id,
          referenceId: match.reference_id,
        };
      }
    }

    const activeProp = hoveredPropId || selectedPropId;
    if (activeProp) {
      const matchForStu = matchedPairs.find((m) => m.student_id === activeProp);
      if (matchForStu) {
        return {
          matchId: matchForStu.id,
          studentId: matchForStu.student_id,
          referenceId: matchForStu.reference_id,
        };
      }
      const matchForRef = matchedPairs.find((m) => m.reference_id === activeProp);
      if (matchForRef) {
        return {
          matchId: matchForRef.id,
          studentId: matchForRef.student_id,
          referenceId: matchForRef.reference_id,
        };
      }
      if (activeProp.startsWith('stu_')) {
        return { matchId: null, studentId: activeProp, referenceId: null };
      }
      return { matchId: null, studentId: null, referenceId: activeProp };
    }

    return { matchId: null, studentId: null, referenceId: null };
  }, [hoveredMatchId, selectedMatchId, hoveredPropId, selectedPropId, matchedPairs]);

  const activeStudentProp = useMemo(() => {
    if (!activeSelection.studentId) return null;
    return studentProps.find((p) => p.id === activeSelection.studentId) || null;
  }, [activeSelection.studentId, studentProps]);

  const activeReferenceProp = useMemo(() => {
    if (!activeSelection.referenceId) return null;
    return referenceProps.find((p) => p.id === activeSelection.referenceId) || null;
  }, [activeSelection.referenceId, referenceProps]);

  const highlightPropForBar = answerMode === 'student' ? activeStudentProp : activeReferenceProp;
  const fullTextForBar = answerMode === 'student' ? studentAnswer : referenceAnswer;

  const handleToggleMatch = (pair) => {
    setSelectedUnmatchedProp(null);
    if (selectedMatchId === pair.id) {
      setSelectedMatchId(null);
      setSelectedPropId(null);
    } else {
      setSelectedMatchId(pair.id);
      setSelectedPropId(null);
    }
  };

  const handleSelectStudentCard = (prop) => {
    setSelectedUnmatchedProp(null);
    const match = matchedPairs.find((m) => m.student_id === prop.id);
    if (match) {
      handleToggleMatch(match);
    } else {
      setSelectedMatchId(null);
      setSelectedPropId(prop.id);
      setSelectedUnmatchedProp({
        id: prop.id,
        idLabel: `P${prop.index + 1}`,
        side: 'student',
        text: prop.text,
      });
    }
    handleSwitchAnswerMode('student');
  };

  const handleSelectReferenceCard = (prop) => {
    setSelectedUnmatchedProp(null);
    const match = matchedPairs.find((m) => m.reference_id === prop.id);
    if (match) {
      handleToggleMatch(match);
    } else {
      setSelectedMatchId(null);
      setSelectedPropId(prop.id);
      setSelectedUnmatchedProp({
        id: prop.id,
        idLabel: `R${prop.index + 1}`,
        side: 'reference',
        text: prop.text,
      });
    }
    handleSwitchAnswerMode('reference');
  };

  const selectedMatch = useMemo(() => {
    if (!selectedMatchId) return null;
    return matchedPairs.find((m) => m.id === selectedMatchId) || null;
  }, [selectedMatchId, matchedPairs]);

  const selectedMatchPos = useMemo(() => {
    if (!selectedMatch) return null;
    const p1 = anchors[selectedMatch.student_id];
    const p2 = anchors[selectedMatch.reference_id];
    if (!p1 || !p2) return null;
    return {
      x: (p1.x + p2.x) / 2,
      y: (p1.y + p2.y) / 2,
    };
  }, [selectedMatch, anchors]);

  const selectedUnmatchedPos = useMemo(() => {
    if (!selectedUnmatchedProp) return null;
    const a = anchors[selectedUnmatchedProp.id];
    if (!a) return null;
    return a;
  }, [selectedUnmatchedProp, anchors]);

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden bg-[#f7f4ed]">
      <AlignmentBar
        answerMode={answerMode}
        onSwitchAnswerMode={handleSwitchAnswerMode}
        fullText={fullTextForBar}
        highlightProp={highlightPropForBar}
      />

      <div
        className="flex-1 min-h-0 relative w-full overflow-y-auto p-4 md:p-8 flex flex-col items-center"
        onClick={(e) => {
          if (e.target === e.currentTarget) {
            setSelectedMatchId(null);
            setSelectedPropId(null);
            setSelectedUnmatchedProp(null);
          }
        }}
      >
        <div className="h-6 flex items-center justify-center mb-3">
          {(animStage === 'STEP_0_ENTER' || animStage === 'STEP_1_SCAN') && (
            <div className="text-[11px] font-mono text-indigo-900 bg-indigo-50/90 px-3 py-0.5 rounded-full border border-indigo-200 shadow-2xs animate-pulse">
              Scanning proposition correspondences...
            </div>
          )}
          {animStage === 'STEP_2_CONNECTING' && (
            <div className="text-[11px] font-mono text-indigo-900 bg-indigo-50/90 px-3 py-0.5 rounded-full border border-indigo-200 shadow-2xs">
              Establishing proposition alignments ({revealedMatchCount} of {matchedPairs.length})...
            </div>
          )}
        </div>

        {studentProps.length === 0 && referenceProps.length === 0 ? (
          <div className="py-20 text-center text-[#706b63] font-mono text-xs">
            No clausal propositions available for alignment.
          </div>
        ) : (
          <div
            ref={canvasBoxRef}
            className="relative w-full max-w-5xl flex justify-between items-start gap-4 sm:gap-8 pb-20 select-none"
          >
            <div className="w-[300px] sm:w-[340px] flex flex-col gap-4 shrink-0 z-20">
              <div className="flex items-center justify-between pb-1 px-1">
                <span className="text-[11px] font-mono font-bold tracking-wider text-[#7a7266] uppercase">
                  Student Propositions
                </span>
                <span className="text-[10.5px] font-mono text-[#8c8477]">
                  {studentProps.length} {studentProps.length === 1 ? 'assertion' : 'assertions'}
                </span>
              </div>

              {studentProps.map((prop) => {
                const isMatched = matchedStudentIds.has(prop.id);
                const isUnmatched = !isMatched;
                const isSelected = activeSelection.studentId === prop.id;

                return (
                  <div
                    key={prop.id}
                    ref={(el) => {
                      if (el) studentCardRefs.current[prop.id] = el;
                    }}
                    onClick={() => handleSelectStudentCard(prop)}
                    onMouseEnter={() => setHoveredPropId(prop.id)}
                    onMouseLeave={() => setHoveredPropId(null)}
                    style={{
                      transform: animStage === 'STEP_0_ENTER' ? 'translateX(14px)' : 'translateX(0)',
                      opacity: animStage === 'STEP_0_ENTER' ? 0.75 : 1,
                      transition: 'all 320ms cubic-bezier(0.16, 1, 0.3, 1)',
                    }}
                    className={`relative rounded-xl p-3.5 transition-all cursor-pointer border ${
                      isSelected
                        ? 'bg-[#faf8f4] border-indigo-700 shadow-md ring-2 ring-indigo-700/15'
                        : isMatched
                        ? 'bg-[#fdfcf9] border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs'
                        : 'bg-[#faf8f4] border-[#dfd8c8] hover:border-[#b5ab9b]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-1.5 font-mono">
                        <span className="text-[12.5px] font-bold text-indigo-950">
                          P{prop.index + 1}
                        </span>
                        <span className="text-[#a89e8f] text-[11px] select-none">—</span>
                        <span className="text-[10px] text-[#706b63] font-semibold uppercase tracking-tight px-1.5 py-0.5 rounded bg-[#f4f0e8] border border-[#dfd8c8]">
                          {prop.representation_type || 'TRIPLE'}
                        </span>
                      </div>

                      {isUnmatched && showUnmatchedStatus && (
                        <span className="text-[9.5px] font-mono font-semibold px-2 py-0.5 rounded bg-[#ede8dc] text-[#706b63] border border-[#dfd8c8] tracking-tight">
                          UNMATCHED
                        </span>
                      )}

                      {isMatched && (
                        <span
                          className={`w-2 h-2 rounded-full transition-colors ${
                            isSelected ? 'bg-indigo-700' : 'bg-indigo-400'
                          }`}
                        />
                      )}
                    </div>

                    <div className="text-[13px] font-medium text-[#1e1c19] leading-snug">
                      &ldquo;{prop.text}&rdquo;
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex-1 self-stretch relative min-w-[120px] pointer-events-none" />

            <div className="w-[300px] sm:w-[340px] flex flex-col gap-4 shrink-0 z-20">
              <div className="flex items-center justify-between pb-1 px-1">
                <span className="text-[11px] font-mono font-bold tracking-wider text-[#7a7266] uppercase">
                  Reference Propositions
                </span>
                <span className="text-[10.5px] font-mono text-[#8c8477]">
                  {referenceProps.length} {referenceProps.length === 1 ? 'assertion' : 'assertions'}
                </span>
              </div>

              {referenceProps.map((prop) => {
                const isMatched = matchedReferenceIds.has(prop.id);
                const isUnmatched = !isMatched;
                const isSelected = activeSelection.referenceId === prop.id;

                return (
                  <div
                    key={prop.id}
                    ref={(el) => {
                      if (el) referenceCardRefs.current[prop.id] = el;
                    }}
                    onClick={() => handleSelectReferenceCard(prop)}
                    onMouseEnter={() => setHoveredPropId(prop.id)}
                    onMouseLeave={() => setHoveredPropId(null)}
                    style={{
                      opacity: animStage === 'STEP_0_ENTER' ? 0.35 : 1,
                      transition: 'opacity 320ms ease-out',
                    }}
                    className={`relative rounded-xl p-3.5 transition-all cursor-pointer border ${
                      isSelected
                        ? 'bg-[#faf8f4] border-indigo-700 shadow-md ring-2 ring-indigo-700/15'
                        : isMatched
                        ? 'bg-[#fdfcf9] border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs'
                        : 'bg-[#faf8f4] border-[#dfd8c8] hover:border-[#b5ab9b]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-1.5 font-mono">
                        <span className="text-[12.5px] font-bold text-indigo-950">
                          R{prop.index + 1}
                        </span>
                        <span className="text-[#a89e8f] text-[11px] select-none">—</span>
                        <span className="text-[10px] text-[#706b63] font-semibold uppercase tracking-tight px-1.5 py-0.5 rounded bg-[#f4f0e8] border border-[#dfd8c8]">
                          {prop.representation_type || 'TRIPLE'}
                        </span>
                      </div>

                      {isUnmatched && showUnmatchedStatus && (
                        <span className="text-[9.5px] font-mono font-semibold px-2 py-0.5 rounded bg-[#ede8dc] text-[#706b63] border border-[#dfd8c8] tracking-tight">
                          UNMATCHED
                        </span>
                      )}

                      {isMatched && (
                        <span
                          className={`w-2 h-2 rounded-full transition-colors ${
                            isSelected ? 'bg-indigo-700' : 'bg-indigo-400'
                          }`}
                        />
                      )}
                    </div>

                    <div className="text-[13px] font-medium text-[#1e1c19] leading-snug">
                      &ldquo;{prop.text}&rdquo;
                    </div>
                  </div>
                );
              })}
            </div>

            <svg className="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-visible">
              {matchedPairs.map((pair, idx) => {
                const p1 = anchors[pair.student_id];
                const p2 = anchors[pair.reference_id];
                if (!p1 || !p2) return null;

                const dx = p2.x - p1.x;
                const curve = `M ${p1.x} ${p1.y} C ${p1.x + dx * 0.45} ${p1.y}, ${p2.x - dx * 0.45} ${p2.y}, ${p2.x} ${p2.y}`;
                const isRevealed = idx < revealedMatchCount;
                const isHighlighted = isRevealed && (activeSelection.matchId === pair.id);

                return (
                  <path
                    key={pair.id || idx}
                    d={curve}
                    fill="none"
                    stroke={isHighlighted ? '#3730a3' : '#3730a3'}
                    strokeWidth={isHighlighted ? 2.5 : 1.75}
                    strokeOpacity={isHighlighted ? 1 : 0.8}
                    strokeDasharray="800"
                    strokeDashoffset={isRevealed ? 0 : 800}
                    style={{
                      transition: 'stroke-dashoffset 350ms ease-out, stroke-width 180ms, stroke-opacity 180ms',
                    }}
                  />
                );
              })}
            </svg>

            {matchedPairs.map((pair, idx) => {
              const p1 = anchors[pair.student_id];
              const p2 = anchors[pair.reference_id];
              if (!p1 || !p2) return null;

              const midX = (p1.x + p2.x) / 2;
              const midY = (p1.y + p2.y) / 2;
              const isRevealed = idx < revealedMatchCount;
              const isHighlighted = isRevealed && (activeSelection.matchId === pair.id);
              const isSelected = selectedMatchId === pair.id;

              return (
                <div
                  key={`badge-${pair.id || idx}`}
                  style={{
                    left: `${midX}px`,
                    top: `${midY}px`,
                    transform: 'translate(-50%, -50%)',
                    opacity: isRevealed ? 1 : 0,
                    pointerEvents: isRevealed ? 'auto' : 'none',
                    transition: 'opacity 250ms ease-out, transform 250ms ease-out',
                  }}
                  className="absolute z-30"
                >
                  <button
                    type="button"
                    onClick={() => handleToggleMatch(pair)}
                    onMouseEnter={() => setHoveredMatchId(pair.id)}
                    onMouseLeave={() => setHoveredMatchId(null)}
                    className={`px-3 py-1 rounded-full text-[10.5px] font-mono font-bold tracking-tight shadow-2xs transition-all cursor-pointer border ${
                      isSelected
                        ? 'bg-indigo-950 text-white border-indigo-950 scale-105 shadow-md ring-2 ring-indigo-400'
                        : isHighlighted
                        ? 'bg-[#3730a3] text-white border-indigo-900 scale-102 shadow-sm'
                        : 'bg-[#faf8f4] text-indigo-950 border-[#dfd8c8] hover:border-indigo-500 hover:bg-indigo-50'
                    }`}
                  >
                    {getMatchLabel(pair)}
                  </button>
                </div>
              );
            })}

            {selectedMatch && selectedMatchPos && (
              <div
                style={{
                  left: `${selectedMatchPos.x}px`,
                  top: `${selectedMatchPos.y}px`,
                  transform: 'translate(-50%, 18px)',
                }}
                className="absolute z-40 w-[300px] sm:w-[330px] bg-[#fdfcf9] border border-[#dfd8c8] rounded-2xl p-4 shadow-xl text-left pointer-events-auto"
              >
                <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-[#dfd8c8]">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#7a7266] font-bold block">
                      ALIGNMENT
                    </span>
                    <span className="text-[14px] font-mono font-bold text-indigo-950">
                      P{selectedMatch.student_index + 1} ↔ R{selectedMatch.reference_index + 1}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedMatchId(null)}
                    className="w-6 h-6 flex items-center justify-center rounded-md text-[#706b63] hover:text-[#1e1c19] hover:bg-[#ede8dc] cursor-pointer text-xs font-mono font-bold transition-colors"
                  >
                    &times;
                  </button>
                </div>

                <div className="space-y-3 text-[12px] font-mono">
                  <div>
                    <span className="text-[10px] uppercase text-[#7a7266] font-semibold block mb-0.5">
                      Match Type
                    </span>
                    <span className="text-[#1e1c19] font-medium">
                      {formatMatchType(selectedMatch.match_method)}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase text-[#7a7266] font-semibold block mb-1">
                      Similarity
                    </span>
                    <div className="grid grid-cols-3 gap-2 bg-[#f7f4ed] p-2 rounded-lg border border-[#dfd8c8] text-center">
                      <div>
                        <span className="text-[9px] text-[#7a7266] block">Subject</span>
                        <span className="font-bold text-[#1e1c19]">
                          {selectedMatch.subject_similarity !== null
                            ? selectedMatch.subject_similarity.toFixed(2)
                            : '—'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[9px] text-[#7a7266] block">Predicate</span>
                        <span className="font-bold text-[#1e1c19]">
                          {selectedMatch.predicate_similarity !== null
                            ? selectedMatch.predicate_similarity.toFixed(2)
                            : '—'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[9px] text-[#7a7266] block">Object</span>
                        <span className="font-bold text-[#1e1c19]">
                          {selectedMatch.object_similarity !== null
                            ? selectedMatch.object_similarity.toFixed(2)
                            : '—'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[11px] text-[#7a7266] font-semibold uppercase">
                      Composite Score
                    </span>
                    <span className="text-[13px] font-bold text-indigo-950">
                      {selectedMatch.triple_score.toFixed(2)}
                    </span>
                  </div>

                  <div className="pt-2 border-t border-[#dfd8c8]/80 text-[11px] font-sans text-[#706b63] leading-relaxed">
                    <span className="font-mono text-[10px] uppercase text-[#7a7266] font-semibold block mb-0.5">
                      Why matched?
                    </span>
                    <span>
                      {getMatchExplanation(selectedMatch)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {selectedUnmatchedProp && selectedUnmatchedPos && (
              <div
                style={{
                  left: `${selectedUnmatchedPos.x}px`,
                  top: `${selectedUnmatchedPos.y}px`,
                  transform:
                    selectedUnmatchedProp.side === 'student'
                      ? 'translate(12px, -50%)'
                      : 'translate(calc(-100% - 12px), -50%)',
                }}
                className="absolute z-40 w-[260px] bg-[#fdfcf9] border border-[#dfd8c8] rounded-2xl p-3.5 shadow-xl text-left pointer-events-auto"
              >
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#dfd8c8]">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#7a7266] font-bold block">
                      {selectedUnmatchedProp.side === 'student' ? 'STUDENT ASSERTION' : 'REFERENCE CRITERION'}
                    </span>
                    <span className="text-sm font-mono font-bold text-[#1e1c19]">
                      {selectedUnmatchedProp.idLabel}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedUnmatchedProp(null)}
                    className="w-6 h-6 flex items-center justify-center rounded-md text-[#706b63] hover:text-[#1e1c19] hover:bg-[#ede8dc] cursor-pointer text-xs font-mono font-bold"
                  >
                    &times;
                  </button>
                </div>
                <div className="text-[11.5px] font-mono text-[#706b63] mb-1.5">
                  Status: <strong className="text-[#1e1c19]">UNMATCHED</strong>
                </div>
                <div className="text-[11.5px] font-sans text-[#706b63] leading-relaxed">
                  {selectedUnmatchedProp.side === 'student'
                    ? 'No corresponding reference proposition met the alignment similarity threshold.'
                    : 'This reference requirement was not aligned to any candidate student proposition.'}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
