import { useState, useEffect, useMemo, useRef } from 'react';
import AnswerBar from './AnswerBar';
import PropositionBar from './PropositionBar';
import InfiniteCanvas from './InfiniteCanvas';
import DetailPanel from './DetailPanel';
import WorkbenchCard from './WorkbenchCard';

function renderNodeCard({
  key,
  node,
  x,
  y,
  opacity = 1,
  transition,
  isSelected = false,
  onClick,
}) {
  const isRoot = (node.dep || '').toLowerCase() === 'root' || node.isRoot;

  return (
    <div
      key={key}
      data-interactive="true"
      onClick={onClick}
      style={{
        left: `${x}px`,
        top: `${y}px`,
        width: `${node.width || 88}px`,
        height: `${node.height || 50}px`,
        position: 'absolute',
        opacity,
        transition,
        pointerEvents: opacity === 0 ? 'none' : 'auto',
      }}
      className={`flex flex-col justify-between p-2 rounded-xl cursor-pointer select-none ${
        isRoot
          ? isSelected
            ? 'bg-[#1e1c19] border-2 border-indigo-500 text-[#f7f4ed] shadow-md z-30'
            : 'bg-[#1e1c19] border-2 border-[#1e1c19] text-[#f7f4ed] shadow-xs z-20'
          : isSelected
          ? 'bg-[#fdfcf9] border-2 border-indigo-700 shadow-sm z-30'
          : 'bg-[#fdfcf9] border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs z-20'
      }`}
    >
      <div className="flex items-center justify-between gap-1">
        <span
          className={`text-[9.5px] font-mono font-medium tracking-wide ${
            isRoot
              ? 'text-[#c2baa8]'
              : isSelected
              ? 'text-indigo-800'
              : 'text-[#8c8477]'
          }`}
        >
          {node.pos}
        </span>
        {isRoot ? (
          <span className="text-[8px] font-mono font-bold text-indigo-300 bg-indigo-950/80 px-1.5 py-0.2 rounded border border-indigo-800/60">
            ROOT
          </span>
        ) : (
          <span className="text-[8px] font-mono text-[#8c8477]">
            #{node.orderIndex + 1}
          </span>
        )}
      </div>

      <div
        className={`text-[13px] font-bold tracking-tight leading-snug truncate ${
          isRoot ? 'text-[#f7f4ed]' : 'text-[#1e1c19]'
        }`}
        title={node.text}
      >
        {node.text}
      </div>
    </div>
  );
}

export default function SyntacticPropositionCanvasPhase({
  activePhase,
  parseData,
  parseMode,
  onSwitchParseMode,
  activeSentenceIndex,
  onSwitchSentence,
  selectedNode,
  onSelectNode,
  onSelectNodeIndex,
  relationsData,
  studentAnswer = '',
  referenceAnswer = '',
  zoom = 1,
  onZoomChange,
  showGrid = true,
  fitTrigger = 0,
  onResetFit,
  onAnalyze,
  loading = false,
  statusMessage = '',
  analysisInput = null,
}) {
  const [propMode, setPropMode] = useState(parseMode || 'student');
  const [selectedPropId, setSelectedPropId] = useState(null);

  useEffect(() => {
    if (parseMode && parseMode !== propMode) {
      setPropMode(parseMode);
    }
  }, [parseMode]);

  const prevPhaseRef = useRef(activePhase);
  const [stage, setStage] = useState(activePhase === '02' ? 'PHASE_02' : 'SETTLED');
  const [boundariesOpacity, setBoundariesOpacity] = useState(activePhase === '03' ? 1 : 0);

  const studentProps = relationsData?.student_propositions || [];
  const referenceProps = relationsData?.reference_propositions || [];
  const activeProps = propMode === 'student' ? studentProps : referenceProps;
  const fullText = propMode === 'student' ? studentAnswer : referenceAnswer;

  const nodes = parseData?.nodes || [];
  const edges = parseData?.edges || [];

  useEffect(() => {
    if (activeProps.length > 0) {
      setSelectedPropId(activeProps[0].id);
    } else {
      setSelectedPropId(null);
    }
  }, [propMode, relationsData]);

  const selectedProp = activeProps.find((p) => p.id === selectedPropId) || activeProps[0] || null;

  useEffect(() => {
    const prev = prevPhaseRef.current;
    if (prev === activePhase) return;
    prevPhaseRef.current = activePhase;

    if (activePhase === '01') {
      setBoundariesOpacity(0);
      return;
    }

    if (activePhase === '02') {
      if (prev === '03') {
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        if (mediaQuery.matches) {
          setStage('PHASE_02');
          setBoundariesOpacity(0);
          return;
        }

        setStage('REVERSE_MOVE');
        setBoundariesOpacity(0);

        const tRev = setTimeout(() => {
          setStage('PHASE_02');
        }, 1100);

        return () => clearTimeout(tRev);
      } else {
        setStage('PHASE_02');
        setBoundariesOpacity(0);
      }
      return;
    }

    if (activePhase === '03') {
      if (prev === '02') {
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        if (mediaQuery.matches) {
          setStage('SETTLED');
          setBoundariesOpacity(1);
          return;
        }

        setStage('STEP_1_FADE');
        setBoundariesOpacity(0);

        const t1 = setTimeout(() => {
          setStage('STEP_2_MOVE');
        }, 80);

        const tBox = setTimeout(() => {
          setBoundariesOpacity(1);
        }, 520);

        const tSettled = setTimeout(() => {
          setStage('SETTLED');
        }, 1200);

        return () => {
          clearTimeout(t1);
          clearTimeout(tBox);
          clearTimeout(tSettled);
        };
      } else {
        setStage('SETTLED');
        setBoundariesOpacity(1);
      }
    }
  }, [activePhase]);

  const isFirstMount = useRef(true);
  useEffect(() => {
    if (isFirstMount.current) {
      isFirstMount.current = false;
      return;
    }
    if (onResetFit) {
      onResetFit();
    }
  }, [activePhase, propMode, parseMode, activeSentenceIndex, onResetFit]);

  const handleSkip = (e) => {
    e.stopPropagation();
    if (activePhase === '02') {
      setStage('PHASE_02');
      setBoundariesOpacity(0);
    } else {
      setStage('SETTLED');
      setBoundariesOpacity(1);
    }
  };

  const laneLayouts = useMemo(() => {
    const LANE_LEFT = 50;
    const LANE_TOP_START = 28;
    const LANE_HEIGHT = 96;
    const LANE_GAP = 18;
    const CARD_GAP = 8;
    const ARROW_WIDTH = 24;

    const cleanWords = (text) =>
      (text || '')
        .toLowerCase()
        .replace(/[^\w\s]/g, '')
        .split(/\s+/)
        .filter(Boolean);

    const matchesWords = (n, wordList) => {
      if (!wordList.length) return false;
      const textClean = (n.text || '').toLowerCase().replace(/[^\w\s]/g, '');
      const lemmaClean = (n.lemma || '').toLowerCase().replace(/[^\w\s]/g, '');
      return (textClean && wordList.includes(textClean)) || (lemmaClean && wordList.includes(lemmaClean));
    };

    const getNodeWidth = (n) => n?.width || 88;
    const calcNodesWidth = (nodeList) => {
      if (!nodeList || nodeList.length === 0) return 88;
      const sumWidth = nodeList.reduce((acc, n) => acc + getNodeWidth(n), 0);
      return sumWidth + Math.max(0, nodeList.length - 1) * CARD_GAP;
    };

    let maxSubjSlotWidth = 88;
    let maxPredSlotWidth = 88;
    let maxObjSlotWidth = 88;

    activeProps.forEach((prop) => {
      const sWords = cleanWords(prop.subject);
      const pWords = cleanWords(prop.predicate);
      const oWords = cleanWords(prop.object);

      const sNodes = nodes.filter((n) => matchesWords(n, sWords));
      const pNodes = nodes.filter((n) => matchesWords(n, pWords));
      const oNodes = nodes.filter((n) => matchesWords(n, oWords));

      const sWidth = calcNodesWidth(sNodes);
      const pWidth = calcNodesWidth(pNodes);
      const oWidth = calcNodesWidth(oNodes);

      if (sWidth > maxSubjSlotWidth) maxSubjSlotWidth = sWidth;
      if (pWidth > maxPredSlotWidth) maxPredSlotWidth = pWidth;
      if (oWidth > maxObjSlotWidth) maxObjSlotWidth = oWidth;
    });

    const subjSlotWidth = maxSubjSlotWidth;
    const predSlotWidth = maxPredSlotWidth;
    const objSlotWidth = maxObjSlotWidth;

    const subjColX = 185;
    const arrow1ColX = subjColX + subjSlotWidth + 18;
    const predColX = arrow1ColX + ARROW_WIDTH + 18;
    const arrow2ColX = predColX + predSlotWidth + 18;
    const objColX = arrow2ColX + ARROW_WIDTH + 18;
    const laneWidth = objColX + objSlotWidth + 28;

    return activeProps.map((prop, propIdx) => {
      const laneTop = LANE_TOP_START + propIdx * (LANE_HEIGHT + LANE_GAP);

      const subjWords = cleanWords(prop.subject);
      const predWords = cleanWords(prop.predicate);
      const objWords = cleanWords(prop.object);

      const subjNodes = nodes
        .filter((n) => matchesWords(n, subjWords))
        .sort((a, b) => (a.orderIndex ?? a.index ?? 0) - (b.orderIndex ?? b.index ?? 0));

      const predNodes = nodes
        .filter((n) => matchesWords(n, predWords))
        .sort((a, b) => (a.orderIndex ?? a.index ?? 0) - (b.orderIndex ?? b.index ?? 0));

      const objNodes = nodes
        .filter((n) => matchesWords(n, objWords))
        .sort((a, b) => (a.orderIndex ?? a.index ?? 0) - (b.orderIndex ?? b.index ?? 0));

      const subjCardTotalWidth = calcNodesWidth(subjNodes);
      const subjCardStartX = subjColX + (subjSlotWidth - subjCardTotalWidth) / 2;

      let subjOffset = 0;
      const subjCardLayouts = subjNodes.map((n) => {
        const cardW = getNodeWidth(n);
        const posX = LANE_LEFT + subjCardStartX + subjOffset;
        subjOffset += cardW + CARD_GAP;
        return {
          key: `card-${prop.id}-subj-${n.id}`,
          node: n,
          x: posX,
          y: laneTop + 23,
          role: 'subj',
          propId: prop.id,
        };
      });

      const predCardTotalWidth = calcNodesWidth(predNodes);
      const predCardStartX = predColX + (predSlotWidth - predCardTotalWidth) / 2;

      let predOffset = 0;
      const predCardLayouts = predNodes.map((n) => {
        const cardW = getNodeWidth(n);
        const posX = LANE_LEFT + predCardStartX + predOffset;
        predOffset += cardW + CARD_GAP;
        return {
          key: `card-${prop.id}-pred-${n.id}`,
          node: n,
          x: posX,
          y: laneTop + 23,
          role: 'pred',
          propId: prop.id,
        };
      });

      const objCardTotalWidth = calcNodesWidth(objNodes);
      const objCardStartX = objColX + (objSlotWidth - objCardTotalWidth) / 2;

      let objOffset = 0;
      const objCardLayouts = objNodes.map((n) => {
        const cardW = getNodeWidth(n);
        const posX = LANE_LEFT + objCardStartX + objOffset;
        objOffset += cardW + CARD_GAP;
        return {
          key: `card-${prop.id}-obj-${n.id}`,
          node: n,
          x: posX,
          y: laneTop + 23,
          role: 'obj',
          propId: prop.id,
        };
      });

      return {
        prop,
        propIdx,
        laneLeft: LANE_LEFT,
        laneTop,
        laneWidth,
        laneHeight: LANE_HEIGHT,
        subjColX,
        subjSlotWidth,
        subjCardStartX,
        subjNodes: subjCardLayouts,
        arrow1ColX,
        predColX,
        predSlotWidth,
        predCardStartX,
        predNodes: predCardLayouts,
        arrow2ColX,
        objColX,
        objSlotWidth,
        objCardStartX,
        objNodes: objCardLayouts,
      };
    });
  }, [activeProps, nodes]);

  const { laneCardItems, unusedNodes } = useMemo(() => {
    const items = [];
    const usedIds = new Set();
    const seenNodeIds = new Set();

    laneLayouts.forEach((lane) => {
      lane.subjNodes.forEach((item) => {
        const isDuplicate = seenNodeIds.has(item.node.id);
        seenNodeIds.add(item.node.id);
        items.push({ ...item, isDuplicate });
        usedIds.add(item.node.id);
      });
      lane.predNodes.forEach((item) => {
        const isDuplicate = seenNodeIds.has(item.node.id);
        seenNodeIds.add(item.node.id);
        items.push({ ...item, isDuplicate });
        usedIds.add(item.node.id);
      });
      lane.objNodes.forEach((item) => {
        const isDuplicate = seenNodeIds.has(item.node.id);
        seenNodeIds.add(item.node.id);
        items.push({ ...item, isDuplicate });
        usedIds.add(item.node.id);
      });
    });

    const unused = nodes.filter((n) => !usedIds.has(n.id));

    return { laneCardItems: items, unusedNodes: unused };
  }, [laneLayouts, nodes]);

  const activePathEdgeIds = useMemo(() => {
    const set = new Set();
    if (selectedNode && stage === 'PHASE_02') {
      let currNodeId = selectedNode.id;
      const visited = new Set();
      while (currNodeId && !visited.has(currNodeId)) {
        visited.add(currNodeId);
        const incomingEdge = edges.find((e) => e.toId === currNodeId);
        if (incomingEdge) {
          set.add(incomingEdge.id);
          currNodeId = incomingEdge.fromId;
        } else {
          break;
        }
      }
    }
    return set;
  }, [selectedNode, edges, stage]);

  const isPhase01 = activePhase === '01';
  const isPhase02 = activePhase === '02';
  const isPhase03 = activePhase === '03';
  const isTransitioning =
    stage === 'STEP_1_FADE' || stage === 'STEP_2_MOVE' || stage === 'REVERSE_MOVE';

  const maxLaneWidth = laneLayouts.length > 0 ? laneLayouts[0].laneWidth : 760;
  const contentWidth = isPhase01
    ? 1060
    : Math.max(parseData?.maxX || 1080, 50 + maxLaneWidth + 60);
  const contentHeight = isPhase01
    ? 780
    : Math.max(
        parseData?.maxY || 460,
        28 + activeProps.length * 114 + 60,
        500
      );

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      <div
        className={`grid grid-cols-1 grid-rows-1 w-full shrink-0 transition-all duration-500 ${
          isPhase01 ? 'h-0 opacity-0 overflow-hidden pointer-events-none' : 'opacity-100'
        }`}
      >
        <div
          className={`col-start-1 row-start-1 w-full transition-opacity duration-500 ease-out ${
            isPhase02 ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
          }`}
        >
          <AnswerBar
            parseMode={parseMode}
            onSwitchParseMode={onSwitchParseMode}
            sentenceCount={parseData.sentenceCount}
            activeSentenceIndex={activeSentenceIndex}
            onSwitchSentence={onSwitchSentence}
            textTokens={parseData.textTokens}
            nodes={parseData.nodes}
            selectedNode={selectedNode}
            onSelectNode={onSelectNode}
          />
        </div>

        <div
          className={`col-start-1 row-start-1 w-full transition-opacity duration-500 ease-out ${
            isPhase03 ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
          }`}
        >
          <PropositionBar
            propMode={propMode}
            onSwitchPropMode={(mode) => {
              setPropMode(mode);
              if (onSwitchParseMode) onSwitchParseMode(mode);
            }}
            studentCount={studentProps.length}
            referenceCount={referenceProps.length}
            fullText={fullText}
            selectedProp={selectedProp}
          />
        </div>
      </div>

      <div className="flex-1 flex min-h-0 relative w-full overflow-hidden">
        <div className="relative flex-1 h-full min-w-0 overflow-hidden">
          {isTransitioning && (
            <div className="absolute top-4 right-6 z-30 pointer-events-auto">
              <button
                type="button"
                onClick={handleSkip}
                className="text-[11.5px] font-mono text-[#706b63] hover:text-[#1e1c19] px-3 py-1.5 rounded-lg border border-[#dfd8c8] bg-[#fdfcf9] shadow-xs cursor-pointer transition-all active:scale-95"
              >
                Skip animation →
              </button>
            </div>
          )}

          <InfiniteCanvas
            zoom={zoom}
            onZoomChange={onZoomChange}
            showGrid={showGrid}
            contentWidth={contentWidth}
            contentHeight={contentHeight}
            fitTrigger={fitTrigger}
            allowWheelZoom={!isPhase01}
          >
            <div
              style={{ width: `${contentWidth}px`, height: `${contentHeight}px` }}
              className="relative select-none"
            >
              <div
                style={{
                  position: 'absolute',
                  left: `${Math.max(40, (contentWidth - 980) / 2)}px`,
                  top: '30px',
                  width: '980px',
                  opacity: isPhase01 ? 1 : 0,
                  pointerEvents: isPhase01 ? 'auto' : 'none',
                  transition: 'opacity 0.6s cubic-bezier(0.45, 0.05, 0.15, 0.98)',
                }}
                onPointerDown={(e) => e.stopPropagation()}
                onMouseDown={(e) => e.stopPropagation()}
                onTouchStart={(e) => e.stopPropagation()}
                className="z-30"
              >
                <WorkbenchCard
                  onAnalyze={onAnalyze}
                  loading={loading}
                  statusMessage={statusMessage}
                  initialInput={analysisInput}
                />
              </div>

              {(isPhase02 || stage === 'STEP_1_FADE' || stage === 'REVERSE_MOVE') && (
                <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
                  <defs>
                    <marker
                      id="arrowhead-primary-sync"
                      markerWidth="10"
                      markerHeight="10"
                      refX="1"
                      refY="5"
                      orient="auto"
                      markerUnits="userSpaceOnUse"
                    >
                      <path d="M 1 2 L 7 5 L 1 8 Z" fill="#3730a3" />
                    </marker>
                    <marker
                      id="arrowhead-default-sync"
                      markerWidth="10"
                      markerHeight="10"
                      refX="1"
                      refY="5"
                      orient="auto"
                      markerUnits="userSpaceOnUse"
                    >
                      <path d="M 1 2 L 7 5 L 1 8 Z" fill="#b5ab9b" />
                    </marker>
                  </defs>

                  <g
                    className="edge-lines transition-opacity duration-400 ease-out"
                    style={{ opacity: stage === 'STEP_1_FADE' ? 0 : 1 }}
                  >
                    {edges.map((edge) => {
                      const isPathActive = activePathEdgeIds.has(edge.id);
                      const verticalDist = Math.max(30, edge.toY - edge.fromY);
                      const controlOffset = Math.max(25, verticalDist * 0.45);
                      const pathD = `M ${edge.fromX} ${edge.fromY} C ${edge.fromX} ${edge.fromY + controlOffset}, ${edge.toX} ${edge.toY - controlOffset}, ${edge.toX} ${edge.toY}`;

                      return (
                        <path
                          key={`path-${edge.id}`}
                          d={pathD}
                          fill="none"
                          stroke={isPathActive ? '#3730a3' : '#b5ab9b'}
                          strokeWidth={isPathActive ? '2.4' : '1.3'}
                          markerEnd={
                            isPathActive
                              ? 'url(#arrowhead-primary-sync)'
                              : 'url(#arrowhead-default-sync)'
                          }
                        />
                      );
                    })}
                  </g>

                  <g
                    className="edge-labels transition-opacity duration-400 ease-out"
                    style={{ opacity: stage === 'STEP_1_FADE' ? 0 : 1 }}
                  >
                    {edges.map((edge) => {
                      const isPathActive = activePathEdgeIds.has(edge.id);
                      const labelText = edge.label || 'dep';
                      const badgeWidth = Math.max(28, labelText.length * 6.5 + 12);
                      const badgeHeight = 17;

                      return (
                        <g key={`label-${edge.id}`}>
                          <rect
                            x={edge.midX - badgeWidth / 2}
                            y={edge.midY - badgeHeight / 2}
                            width={badgeWidth}
                            height={badgeHeight}
                            rx={5}
                            fill="#fdfcf9"
                            stroke={isPathActive ? '#3730a3' : '#dfd8c8'}
                            strokeWidth={isPathActive ? '1.5' : '1'}
                            className="drop-shadow-2xs"
                          />
                          <text
                            x={edge.midX}
                            y={edge.midY + 3.5}
                            fill={isPathActive ? '#3730a3' : '#706b63'}
                            fontSize="9"
                            fontFamily="ui-monospace, monospace"
                            fontWeight={isPathActive ? '700' : '600'}
                            textAnchor="middle"
                            className="select-none pointer-events-none"
                          >
                            {labelText}
                          </text>
                        </g>
                      );
                    })}
                  </g>
                </svg>
              )}

              <div
                className="absolute inset-0 pointer-events-none z-10 transition-opacity duration-600 cubic-bezier(0.45, 0.05, 0.15, 0.98)"
                style={{ opacity: boundariesOpacity }}
              >
                {laneLayouts.map((lane) => {
                  const isSelected = selectedPropId === lane.prop.id;

                  return (
                    <div
                      key={`lane-box-${lane.prop.id}`}
                      onClick={() => setSelectedPropId(lane.prop.id)}
                      style={{
                        left: `${lane.laneLeft}px`,
                        top: `${lane.laneTop}px`,
                        width: `${lane.laneWidth}px`,
                        height: `${lane.laneHeight}px`,
                        pointerEvents: boundariesOpacity > 0 ? 'auto' : 'none',
                      }}
                      className={`absolute rounded-2xl transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-[#fdfcf9] border-2 border-indigo-700 shadow-md ring-2 ring-indigo-700/10'
                          : 'bg-[#fdfcf9]/95 border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs'
                      }`}
                    >
                      <div
                        style={{ left: '18px', top: '14px', width: '135px', height: '68px' }}
                        className="absolute flex flex-col justify-between select-none"
                      >
                        <div className="flex items-center gap-1.5 font-mono">
                          <span className="text-[13px] font-bold text-indigo-950 tracking-wide">
                            P{lane.propIdx + 1}
                          </span>
                          <span className="text-[#a89e8f] text-[11px] select-none">—</span>
                          <span className="text-[10px] text-[#706b63] font-semibold tracking-tight uppercase">
                            {lane.prop.representation_type}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 mt-auto">
                          <span
                            className={`text-[9.5px] font-mono font-semibold px-2 py-0.5 rounded border ${
                              lane.prop.polarity === 'NEGATIVE'
                                ? 'bg-rose-50 text-rose-800 border-rose-200'
                                : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            }`}
                          >
                            {lane.prop.polarity}
                          </span>
                        </div>
                      </div>

                      <div
                        style={{ left: '165px', top: '14px', width: '1px', height: '68px' }}
                        className="absolute bg-[#dfd8c8]"
                      />

                      <div
                        style={{ left: `${lane.subjColX}px`, top: '7px', width: `${lane.subjSlotWidth}px` }}
                        className="absolute text-center text-[9px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold select-none"
                      >
                        Subject
                      </div>

                      <div
                        style={{ left: `${lane.arrow1ColX}px`, top: '36px', width: '24px' }}
                        className="absolute text-center text-indigo-900 font-mono text-[16px] font-bold select-none"
                      >
                        →
                      </div>

                      <div
                        style={{ left: `${lane.predColX}px`, top: '7px', width: `${lane.predSlotWidth}px` }}
                        className="absolute text-center text-[9px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold select-none"
                      >
                        Predicate
                      </div>

                      <div
                        style={{ left: `${lane.arrow2ColX}px`, top: '36px', width: '24px' }}
                        className="absolute text-center text-indigo-900 font-mono text-[16px] font-bold select-none"
                      >
                        →
                      </div>

                      <div
                        style={{ left: `${lane.objColX}px`, top: '7px', width: `${lane.objSlotWidth}px` }}
                        className="absolute text-center text-[9px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold select-none"
                      >
                        {lane.prop.object ? 'Object' : 'Argument'}
                      </div>
                    </div>
                  );
                })}

                {laneLayouts.map((lane) => (
                  <div key={`placeholders-${lane.prop.id}`}>
                    {lane.subjNodes.length === 0 && (
                      <div
                        style={{
                          left: `${lane.laneLeft + lane.subjColX + (lane.subjSlotWidth - 88) / 2}px`,
                          top: `${lane.laneTop + 23}px`,
                          width: '88px',
                          height: '50px',
                          position: 'absolute',
                        }}
                        className="flex items-center justify-center rounded-xl bg-[#f4f0e8] border border-[#dfd8c8] text-[11px] font-mono text-[#8c8477] italic select-none"
                      >
                        (elliptical)
                      </div>
                    )}
                    {lane.predNodes.length === 0 && (
                      <div
                        style={{
                          left: `${lane.laneLeft + lane.predColX + (lane.predSlotWidth - 88) / 2}px`,
                          top: `${lane.laneTop + 23}px`,
                          width: '88px',
                          height: '50px',
                          position: 'absolute',
                        }}
                        className="flex items-center justify-center rounded-xl bg-[#f4f0e8] border border-[#dfd8c8] text-[11px] font-mono text-[#8c8477] italic select-none"
                      >
                        —
                      </div>
                    )}
                    {lane.objNodes.length === 0 && (
                      <div
                        style={{
                          left: `${lane.laneLeft + lane.objColX + (lane.objSlotWidth - 88) / 2}px`,
                          top: `${lane.laneTop + 23}px`,
                          width: '88px',
                          height: '50px',
                          position: 'absolute',
                        }}
                        className="flex items-center justify-center rounded-xl bg-[#f4f0e8] border border-[#dfd8c8] text-[11px] font-mono text-[#8c8477] italic select-none"
                      >
                        —
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="absolute inset-0 pointer-events-none z-20">
                {stage === 'PHASE_02' ? (
                  !isPhase01 &&
                  nodes.map((node) =>
                    renderNodeCard({
                      key: `node-${node.id}`,
                      node,
                      x: node.x,
                      y: node.y,
                      opacity: 1,
                      isSelected: selectedNode?.id === node.id,
                      onClick: () => onSelectNode && onSelectNode(node),
                    })
                  )
                ) : (
                  <>
                    {(stage === 'STEP_1_FADE' || stage === 'REVERSE_MOVE') &&
                      unusedNodes.map((node) =>
                        renderNodeCard({
                          key: `unused-${node.id}`,
                          node,
                          x: node.x,
                          y: node.y,
                          opacity: stage === 'REVERSE_MOVE' ? 1 : 0,
                          transition: 'opacity 0.5s ease-out',
                          isSelected: false,
                        })
                      )}

                    {laneCardItems.map((item) => {
                      const curX =
                        stage === 'STEP_1_FADE' || stage === 'REVERSE_MOVE'
                          ? item.node.x
                          : item.x;
                      const curY =
                        stage === 'STEP_1_FADE' || stage === 'REVERSE_MOVE'
                          ? item.node.y
                          : item.y;

                      const isOriginal = !item.isDuplicate;

                      let cardOpacity = 1;
                      if (stage === 'STEP_1_FADE') {
                        cardOpacity = isOriginal ? 1 : 0;
                      } else if (stage === 'REVERSE_MOVE') {
                        cardOpacity = isOriginal ? 1 : 0;
                      } else {
                        cardOpacity = 1;
                      }

                      return renderNodeCard({
                        key: item.key,
                        node: item.node,
                        x: curX,
                        y: curY,
                        opacity: cardOpacity,
                        transition:
                          stage === 'STEP_1_FADE'
                            ? 'none'
                            : 'left 1.1s cubic-bezier(0.45, 0.05, 0.15, 0.98), top 1.1s cubic-bezier(0.45, 0.05, 0.15, 0.98), opacity 0.7s cubic-bezier(0.45, 0.05, 0.15, 0.98)',
                        isSelected: false,
                        onClick: () => setSelectedPropId(item.propId),
                      });
                    })}
                  </>
                )}
              </div>
            </div>
          </InfiniteCanvas>
        </div>

        <div
          style={{
            transition: 'all 0.7s cubic-bezier(0.45, 0.05, 0.15, 0.98)',
          }}
          className={`h-full flex flex-col overflow-hidden shrink-0 ${
            isPhase02 ? 'w-80 opacity-100' : 'w-0 opacity-0 pointer-events-none'
          }`}
        >
          <DetailPanel
            selectedNode={selectedNode}
            nodes={parseData.nodes}
            onSelectNodeIndex={onSelectNodeIndex}
          />
        </div>
      </div>
    </div>
  );
}
