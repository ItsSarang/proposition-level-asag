import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import AnswerBar from "./AnswerBar"
import PropositionBar from "./PropositionBar"
import AlignmentBar from "./AlignmentBar"
import AssessmentBar from "./AssessmentBar"
import ResultBar from "./ResultBar"
import InfiniteCanvas from "./InfiniteCanvas"
import DetailPanel from "./DetailPanel"
import WorkbenchCard from "./WorkbenchCard"
import PhaseAnnotation from "./PhaseAnnotation"

const PHASE_ANNOTATION_CONFIG = {
  "01": {
    number: "01",
    title: "INPUT",
    description: "What was asked?",
    connector: "right-down",
    left: "30px",
    top: "0px",
    titleSize: "22px",
    descSize: "17px",
  },
  "02": {
    number: "02",
    title: "DEPENDENCIES",
    description: "Parse the answer into syntactic relationships",
    connector: "right-down",
    left: "44px",
    top: "16px",
    titleSize: "22px",
    descSize: "17px",
  },
  "03": {
    number: "03",
    title: "PROPOSITIONS",
    description: "Extract meaningful assertions",
    connector: "right-down",
    left: "20px",
    top: "-50px",
    titleSize: "22px",
    descSize: "17px",
  },
  "04": {
    number: "04",
    title: "ALIGNMENT",
    description: "Find corresponding information",
    connector: "right-down",
    left: "-40px",
    top: "-90px",
    titleSize: "22px",
    descSize: "17px",
  },
  "05": {
    number: "05",
    title: "ASSESSMENT",
    description: "Evaluate what each proposition means",
    connector: "right-down",
    left: "-40px",
    top: "-90px",
    titleSize: "22px",
    descSize: "17px",
  },
  "06": {
    number: "06",
    title: "RESULT",
    description: "See how the answer was graded",
    connector: "right-down",
    left: "0px",
    top: "-90px",
    titleSize: "22px",
    descSize: "17px",
  },
}

function getMatchLabel(pair) {
  const method = (pair.match_method || "").toLowerCase()
  const pct = Math.round((pair.triple_score || 0) * 100)
  let typeLabel = "MATCH"
  if (method === "exact_triple" || method === "exact_match") {
    typeLabel = "EXACT MATCH"
  } else if (method === "lemma_triple" || method === "lemma_match") {
    typeLabel = "LEMMA MATCH"
  } else if (
    method === "semantic_synonym_triple" ||
    method === "semantic_path_triple" ||
    method === "weighted_slots" ||
    method.includes("semantic")
  ) {
    typeLabel = "SEMANTIC MATCH"
  } else if (method.includes("structural") || method.includes("partial")) {
    typeLabel = "STRUCTURAL MATCH"
  }
  return `${typeLabel} · ${pct}%`
}

function getSpanStyle(role, isHovered, isSelected) {
  if (role === "CORE_INFORMATION" || role === "CORE") {
    return {
      bg: isSelected
        ? "bg-indigo-100"
        : isHovered
          ? "bg-indigo-50/90"
          : "bg-indigo-50/60",
      border: isSelected
        ? "border-indigo-700"
        : isHovered
          ? "border-indigo-600"
          : "border-indigo-500",
      text: "text-indigo-950 font-medium",
      badgeBg: "bg-indigo-100 text-indigo-800 border-indigo-200",
      borderStyle: "border-b-2",
      dotColor: "#4f46e5",
      label: "Core information",
    }
  }
  if (role === "CORRECT_ADDITIONAL") {
    return {
      bg: isSelected
        ? "bg-emerald-100"
        : isHovered
          ? "bg-emerald-50/90"
          : "bg-emerald-50/60",
      border: isSelected
        ? "border-emerald-700"
        : isHovered
          ? "border-emerald-600"
          : "border-emerald-500",
      text: "text-emerald-950 font-medium",
      badgeBg: "bg-emerald-100 text-emerald-800 border-emerald-200",
      borderStyle: "border-b-2",
      dotColor: "#059669",
      label: "Correct additional",
    }
  }
  if (role === "IRRELEVANT") {
    return {
      bg: isSelected
        ? "bg-[#e8e2d4]"
        : isHovered
          ? "bg-[#ede7da]"
          : "bg-[#f4efe4]/70",
      border: isSelected
        ? "border-[#8a8070]"
        : isHovered
          ? "border-[#a89d8b]"
          : "border-[#b5ab9b]",
      text: "text-[#47423b]",
      badgeBg: "bg-[#ede7da] text-[#5e584f] border-[#dfd8c8]",
      borderStyle: "border-b-2",
      dotColor: "#8a8070",
      label: "Irrelevant",
    }
  }
  if (role === "INCORRECT") {
    return {
      bg: isSelected
        ? "bg-rose-100"
        : isHovered
          ? "bg-rose-50/90"
          : "bg-rose-50/60",
      border: isSelected
        ? "border-rose-700"
        : isHovered
          ? "border-rose-600"
          : "border-rose-500",
      text: "text-rose-950 font-medium",
      badgeBg: "bg-rose-100 text-rose-800 border-rose-200",
      borderStyle: "border-b-2",
      dotColor: "#e11d48",
      label: "Incorrect",
    }
  }
  return {
    bg: isSelected
      ? "bg-amber-100"
      : isHovered
        ? "bg-amber-50/90"
        : "bg-amber-50/50",
    border: isSelected
      ? "border-amber-700"
      : isHovered
        ? "border-amber-600"
        : "border-amber-500",
    text: "text-amber-950",
    badgeBg: "bg-amber-100 text-amber-800 border-amber-200",
    borderStyle: "border-b-2 border-dashed",
    dotColor: "#d97706",
    label: "Uncertain",
  }
}

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
  const isRoot = (node.dep || "").toLowerCase() === "root" || node.isRoot

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
        position: "absolute",
        opacity,
        transition,
        pointerEvents: opacity === 0 ? "none" : "auto",
      }}
      className={`flex flex-col justify-between p-2 rounded-xl cursor-pointer select-none ${
        isRoot
          ? isSelected
            ? "bg-[#1e1c19] border-2 border-indigo-500 text-[#f7f4ed] shadow-md z-30"
            : "bg-[#1e1c19] border-2 border-[#1e1c19] text-[#f7f4ed] shadow-xs z-20"
          : isSelected
            ? "bg-[#fdfcf9] border-2 border-indigo-700 shadow-sm z-30"
            : "bg-[#fdfcf9] border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs z-20"
      }`}
    >
      <div className="flex items-center justify-between gap-1">
        <span
          className={`text-[9.5px] font-mono font-medium tracking-wide ${
            isRoot
              ? "text-[#c2baa8]"
              : isSelected
                ? "text-indigo-800"
                : "text-[#8c8477]"
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
          isRoot ? "text-[#f7f4ed]" : "text-[#1e1c19]"
        }`}
        title={node.text}
      >
        {node.text}
      </div>
    </div>
  )
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
  matchData = null,
  entailmentData = null,
  additionalData = null,
  scoreData = null,
  studentAnswer = "",
  referenceAnswer = "",
  zoom = 1,
  onZoomChange,
  showGrid = true,
  fitTrigger = 0,
  onAnalyze,
  loading = false,
  statusMessage = "",
  analysisInput = null,
}) {
  const [propMode, setPropMode] = useState(parseMode || "student")
  const [selectedPropId, setSelectedPropId] = useState(null)

  const [hoveredMatchId, setHoveredMatchId] = useState(null)
  const [selectedMatchId, setSelectedMatchId] = useState(null)
  const [hoveredP4PropId, setHoveredP4PropId] = useState(null)
  const [selectedP4PropId, setSelectedP4PropId] = useState(null)
  const [selectedUnmatchedProp, setSelectedUnmatchedProp] = useState(null)

  const [p4AnimStage, setP4AnimStage] = useState("STEP_4_SETTLED")
  const [revealedMatchCount, setRevealedMatchCount] = useState(0)
  const [showUnmatchedStatus, setShowUnmatchedStatus] = useState(true)
  const [p4RefCardsVisible, setP4RefCardsVisible] = useState(true)

  const [selectedP5MatchedId, setSelectedP5MatchedId] = useState(null)
  const [selectedP5UnmatchedId, setSelectedP5UnmatchedId] = useState(null)
  const [hoveredP5Id, setHoveredP5Id] = useState(null)
  const [p5AnimStage, setP5AnimStage] = useState("STEP_5_SETTLED")
  const [p5FromPhase, setP5FromPhase] = useState("04")
  const [p5RefCardsVisible, setP5RefCardsVisible] = useState(true)
  const [p5RevealedMatchCount, setP5RevealedMatchCount] = useState(0)
  const [isExitingP4P5, setIsExitingP4P5] = useState(false)
  const [p2FadeIn, setP2FadeIn] = useState(true)

  const lastActivePhaseRef = useRef(activePhase)
  const effectiveP5FromPhase =
    activePhase === "05" && lastActivePhaseRef.current !== "05"
      ? lastActivePhaseRef.current
      : p5FromPhase
  if (lastActivePhaseRef.current !== activePhase) {
    lastActivePhaseRef.current = activePhase
  }

  const [hoveredSpanId, setHoveredSpanId] = useState(null)
  const [p6AnimStage, setP6AnimStage] = useState("STEP_5_SETTLED")
  const [p6ScoringVisible, setP6ScoringVisible] = useState(true)
  const [internalFitTrigger, setInternalFitTrigger] = useState(0)

  useEffect(() => {
    if (parseMode && parseMode !== propMode) {
      setPropMode(parseMode)
    }
  }, [parseMode])

  const prevPhaseRef = useRef(activePhase)
  const [stage, setStage] = useState(
    activePhase === "02" ? "PHASE_02" : "SETTLED",
  )
  const [boundariesOpacity, setBoundariesOpacity] = useState(
    activePhase === "03" || activePhase === "04" || activePhase === "05"
      ? 1
      : 0,
  )

  const studentProps = relationsData?.student_propositions || []
  const referenceProps = relationsData?.reference_propositions || []
  const activeProps = propMode === "student" ? studentProps : referenceProps
  const fullText = propMode === "student" ? studentAnswer : referenceAnswer

  const matchedPairs = useMemo(
    () => matchData?.matched_pairs || [],
    [matchData],
  )
  const matchedStudentIds = useMemo(
    () => new Set(matchedPairs.map((p) => p.student_id)),
    [matchedPairs],
  )
  const matchedReferenceIds = useMemo(
    () => new Set(matchedPairs.map((p) => p.reference_id)),
    [matchedPairs],
  )

  const entailmentEvaluations = useMemo(
    () => entailmentData?.entailment_evaluations || [],
    [entailmentData],
  )
  const unmatchedAddProps = useMemo(
    () => additionalData?.unmatched_propositions || [],
    [additionalData],
  )

  const unmatchedStudentProps = useMemo(
    () => studentProps.filter((p) => !matchedStudentIds.has(p.id)),
    [studentProps, matchedStudentIds],
  )

  const nodes = parseData?.nodes || []
  const edges = parseData?.edges || []

  useEffect(() => {
    if (activeProps.length > 0) {
      setSelectedPropId(activeProps[0].id)
    } else {
      setSelectedPropId(null)
    }
  }, [propMode, relationsData])

  const selectedProp =
    activeProps.find((p) => p.id === selectedPropId) || activeProps[0] || null

  useEffect(() => {
    const prev = prevPhaseRef.current
    if (prev === activePhase) return
    prevPhaseRef.current = activePhase

    if (activePhase === "05") {
      setP5FromPhase(prev)
    }

    if (activePhase === "01") {
      setBoundariesOpacity(0)
      return
    }

    if (activePhase === "02") {
      setP2FadeIn(false)
      const tP2Fade = setTimeout(() => {
        setP2FadeIn(true)
      }, 40)

      const tSettledFit = setTimeout(() => {
        setInternalFitTrigger((p) => p + 1)
      }, 760)

      if (prev === "03") {
        const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
        if (mediaQuery.matches) {
          setStage("PHASE_02")
          setBoundariesOpacity(0)
          return () => {
            clearTimeout(tSettledFit)
            clearTimeout(tP2Fade)
          }
        }

        setStage("REVERSE_MOVE")
        setBoundariesOpacity(0)

        const tRev = setTimeout(() => {
          setStage("PHASE_02")
        }, 1100)

        return () => {
          clearTimeout(tRev)
          clearTimeout(tSettledFit)
          clearTimeout(tP2Fade)
        }
      } else {
        setStage("PHASE_02")
        setBoundariesOpacity(0)
      }
      return () => {
        clearTimeout(tSettledFit)
        clearTimeout(tP2Fade)
      }
    }

    if (activePhase === "03") {
      let tExit = null
      if (prev === "04" || prev === "05") {
        setIsExitingP4P5(true)
        tExit = setTimeout(() => {
          setIsExitingP4P5(false)
        }, 400)
      }

      if (prev === "02") {
        const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
        if (mediaQuery.matches) {
          setStage("SETTLED")
          setBoundariesOpacity(1)
          return () => {
            if (tExit) clearTimeout(tExit)
          }
        }

        setStage("STEP_1_FADE")
        setBoundariesOpacity(0)

        const t1 = setTimeout(() => {
          setStage("STEP_2_MOVE")
        }, 80)

        const tBox = setTimeout(() => {
          setBoundariesOpacity(1)
        }, 520)

        const tSettled = setTimeout(() => {
          setStage("SETTLED")
        }, 1200)

        return () => {
          clearTimeout(t1)
          clearTimeout(tBox)
          clearTimeout(tSettled)
          if (tExit) clearTimeout(tExit)
        }
      } else {
        setStage("SETTLED")
        setBoundariesOpacity(1)
      }
      return () => {
        if (tExit) clearTimeout(tExit)
      }
    }

    if (activePhase === "04" || activePhase === "05") {
      setStage("SETTLED")
      setBoundariesOpacity(1)
      return
    }

    if (activePhase === "06") {
      setStage("SETTLED")
      setBoundariesOpacity(0)
      return
    }
  }, [activePhase, relationsData])

  useEffect(() => {
    if (activePhase !== "04") {
      setP4AnimStage("STEP_0_ENTER")
      setRevealedMatchCount(0)
      setShowUnmatchedStatus(false)
      setP4RefCardsVisible(false)
      setSelectedMatchId(null)
      setSelectedUnmatchedProp(null)
      return
    }

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    if (mediaQuery.matches) {
      setP4AnimStage("STEP_4_SETTLED")
      setP4RefCardsVisible(true)
      setRevealedMatchCount(matchedPairs.length)
      setShowUnmatchedStatus(true)
      return
    }

    setP4AnimStage("STEP_0_ENTER")
    setRevealedMatchCount(0)
    setShowUnmatchedStatus(false)
    setP4RefCardsVisible(false)

    const timers = []

    const tRef = setTimeout(() => {
      setP4RefCardsVisible(true)
    }, 100)
    timers.push(tRef)

    const tScan = setTimeout(() => {
      setP4AnimStage("STEP_1_SCAN")
    }, 320)
    timers.push(tScan)

    matchedPairs.forEach((_, idx) => {
      const tMatch = setTimeout(
        () => {
          setP4AnimStage("STEP_2_CONNECTING")
          setRevealedMatchCount(idx + 1)
        },
        550 + idx * 260,
      )
      timers.push(tMatch)
    })

    const unmatchedDelay = 550 + matchedPairs.length * 260 + 120
    const tUnmatched = setTimeout(() => {
      setP4AnimStage("STEP_3_UNMATCHED")
      setShowUnmatchedStatus(true)
    }, unmatchedDelay)
    timers.push(tUnmatched)

    const settledDelay = unmatchedDelay + 240
    const tSettled = setTimeout(() => {
      setP4AnimStage("STEP_4_SETTLED")
    }, settledDelay)
    timers.push(tSettled)

    return () => {
      timers.forEach(clearTimeout)
    }
  }, [activePhase, matchedPairs])

  useEffect(() => {
    if (activePhase !== "05") {
      setP5AnimStage("STEP_0_ENTER")
      setP5RevealedMatchCount(0)
      setSelectedP5MatchedId(null)
      setSelectedP5UnmatchedId(null)
      return
    }

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    if (mediaQuery.matches) {
      setP5AnimStage("STEP_5_SETTLED")
      setP5RefCardsVisible(true)
      setP5RevealedMatchCount(matchedPairs.length)
      return
    }

    if (p5FromPhase === "04") {
      setP5RefCardsVisible(true)
      setP5RevealedMatchCount(matchedPairs.length)
      setP5AnimStage("STEP_0_ENTER")

      const timers = []

      const t1 = setTimeout(() => {
        setP5AnimStage("STEP_1_HIGHLIGHT")
      }, 350)
      timers.push(t1)

      const t2 = setTimeout(() => {
        setP5AnimStage("STEP_2_MOVE_UNMATCHED")
      }, 750)
      timers.push(t2)

      const t3 = setTimeout(() => {
        setP5AnimStage("STEP_3_LABEL")
      }, 1350)
      timers.push(t3)

      const t4 = setTimeout(() => {
        setP5AnimStage("STEP_4_CLASSIFICATION")
      }, 1750)
      timers.push(t4)

      const tSettled = setTimeout(() => {
        setP5AnimStage("STEP_5_SETTLED")
      }, 2150)
      timers.push(tSettled)

      return () => {
        timers.forEach(clearTimeout)
      }
    } else {
      setP5RefCardsVisible(false)
      setP5RevealedMatchCount(0)
      setP5AnimStage("STEP_0_ENTER")

      const timers = []

      const tRef = setTimeout(() => {
        setP5RefCardsVisible(true)
      }, 100)
      timers.push(tRef)

      matchedPairs.forEach((_, idx) => {
        const tMatch = setTimeout(
          () => {
            setP5RevealedMatchCount(idx + 1)
          },
          380 + idx * 240,
        )
        timers.push(tMatch)
      })

      const linesFinishDelay = 380 + matchedPairs.length * 240 + 120

      const tBadges = setTimeout(() => {
        setP5AnimStage("STEP_3_LABEL")
      }, linesFinishDelay)
      timers.push(tBadges)

      const tCls = setTimeout(() => {
        setP5AnimStage("STEP_4_CLASSIFICATION")
      }, linesFinishDelay + 320)
      timers.push(tCls)

      const tSettled = setTimeout(() => {
        setP5AnimStage("STEP_5_SETTLED")
      }, linesFinishDelay + 600)
      timers.push(tSettled)

      return () => {
        timers.forEach(clearTimeout)
      }
    }
  }, [activePhase, p5FromPhase, matchedPairs])

  useEffect(() => {
    if (activePhase !== "06") {
      setP6AnimStage("STEP_0_ENTER")
      setHoveredSpanId(null)
      setP6ScoringVisible(false)
      return
    }

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)")
    if (mediaQuery.matches) {
      setP6AnimStage("STEP_5_SETTLED")
      setP6ScoringVisible(true)
      return
    }

    setP6AnimStage("STEP_0_ENTER")
    setP6ScoringVisible(false)

    const timers = []

    const t1 = setTimeout(() => {
      setP6AnimStage("STEP_1_ATTRIBUTION")
    }, 350)
    timers.push(t1)

    const t2 = setTimeout(() => {
      setP6AnimStage("STEP_2_ANSWER")
    }, 800)
    timers.push(t2)

    const tScore = setTimeout(() => {
      setP6ScoringVisible(true)
      setP6AnimStage("STEP_3_SUMMARY")
    }, 1050)
    timers.push(tScore)

    const t4 = setTimeout(() => {
      setP6AnimStage("STEP_4_FINAL_GRADE")
    }, 1450)
    timers.push(t4)

    const tSettled = setTimeout(() => {
      setP6AnimStage("STEP_5_SETTLED")
    }, 1850)
    timers.push(tSettled)

    return () => {
      timers.forEach(clearTimeout)
    }
  }, [activePhase])

  const isPhase01 = activePhase === "01"
  const isPhase02 = activePhase === "02"
  const isPhase03 = activePhase === "03"
  const isPhase04 = activePhase === "04"
  const isPhase05 = activePhase === "05"
  const isPhase06 = activePhase === "06"

  const propsForLanes =
    isPhase04 || isPhase05 || isPhase06 ? studentProps : activeProps

  const laneLayouts = useMemo(() => {
    const LANE_LEFT = 50
    const LANE_TOP_START = 28
    const LANE_HEIGHT = 96
    const LANE_GAP = 18
    const CARD_GAP = 8
    const ARROW_WIDTH = 24

    const cleanWords = (text) =>
      (text || "")
        .toLowerCase()
        .replace(/[^\w\s]/g, "")
        .split(/\s+/)
        .filter(Boolean)

    const matchesWords = (n, wordList) => {
      if (!wordList.length) return false
      const textClean = (n.text || "").toLowerCase().replace(/[^\w\s]/g, "")
      const lemmaClean = (n.lemma || "").toLowerCase().replace(/[^\w\s]/g, "")
      return (
        (textClean && wordList.includes(textClean)) ||
        (lemmaClean && wordList.includes(lemmaClean))
      )
    }

    const getNodeWidth = (n) => n?.width || 88
    const calcNodesWidth = (nodeList) => {
      if (!nodeList || nodeList.length === 0) return 88
      const sumWidth = nodeList.reduce((acc, n) => acc + getNodeWidth(n), 0)
      return sumWidth + Math.max(0, nodeList.length - 1) * CARD_GAP
    }

    let maxSubjSlotWidth = 88
    let maxPredSlotWidth = 88
    let maxObjSlotWidth = 88

    propsForLanes.forEach((prop) => {
      const sWords = cleanWords(prop.subject)
      const pWords = cleanWords(prop.predicate)
      const oWords = cleanWords(prop.object)

      const sNodes = nodes.filter((n) => matchesWords(n, sWords))
      const pNodes = nodes.filter((n) => matchesWords(n, pWords))
      const oNodes = nodes.filter((n) => matchesWords(n, oWords))

      const sWidth = calcNodesWidth(sNodes)
      const pWidth = calcNodesWidth(pNodes)
      const oWidth = calcNodesWidth(oNodes)

      if (sWidth > maxSubjSlotWidth) maxSubjSlotWidth = sWidth
      if (pWidth > maxPredSlotWidth) maxPredSlotWidth = pWidth
      if (oWidth > maxObjSlotWidth) maxObjSlotWidth = oWidth
    })

    const subjSlotWidth = maxSubjSlotWidth
    const predSlotWidth = maxPredSlotWidth
    const objSlotWidth = maxObjSlotWidth

    const subjColX = 185
    const arrow1ColX = subjColX + subjSlotWidth + 18
    const predColX = arrow1ColX + ARROW_WIDTH + 18
    const arrow2ColX = predColX + predSlotWidth + 18
    const objColX = arrow2ColX + ARROW_WIDTH + 18
    const laneWidth = objColX + objSlotWidth + 28

    return propsForLanes.map((prop, propIdx) => {
      const laneTop = LANE_TOP_START + propIdx * (LANE_HEIGHT + LANE_GAP)

      const subjWords = cleanWords(prop.subject)
      const predWords = cleanWords(prop.predicate)
      const objWords = cleanWords(prop.object)

      const subjNodes = nodes
        .filter((n) => matchesWords(n, subjWords))
        .sort(
          (a, b) =>
            (a.orderIndex ?? a.index ?? 0) - (b.orderIndex ?? b.index ?? 0),
        )

      const predNodes = nodes
        .filter((n) => matchesWords(n, predWords))
        .sort(
          (a, b) =>
            (a.orderIndex ?? a.index ?? 0) - (b.orderIndex ?? b.index ?? 0),
        )

      const objNodes = nodes
        .filter((n) => matchesWords(n, objWords))
        .sort(
          (a, b) =>
            (a.orderIndex ?? a.index ?? 0) - (b.orderIndex ?? b.index ?? 0),
        )

      const subjCardTotalWidth = calcNodesWidth(subjNodes)
      const subjCardStartX = subjColX + (subjSlotWidth - subjCardTotalWidth) / 2

      let subjOffset = 0
      const subjCardLayouts = subjNodes.map((n) => {
        const cardW = getNodeWidth(n)
        const posX = LANE_LEFT + subjCardStartX + subjOffset
        subjOffset += cardW + CARD_GAP
        return {
          key: `card-${prop.id}-subj-${n.id}`,
          node: n,
          x: posX,
          y: laneTop + 23,
          role: "subj",
          propId: prop.id,
        }
      })

      const predCardTotalWidth = calcNodesWidth(predNodes)
      const predCardStartX = predColX + (predSlotWidth - predCardTotalWidth) / 2

      let predOffset = 0
      const predCardLayouts = predNodes.map((n) => {
        const cardW = getNodeWidth(n)
        const posX = LANE_LEFT + predCardStartX + predOffset
        predOffset += cardW + CARD_GAP
        return {
          key: `card-${prop.id}-pred-${n.id}`,
          node: n,
          x: posX,
          y: laneTop + 23,
          role: "pred",
          propId: prop.id,
        }
      })

      const objCardTotalWidth = calcNodesWidth(objNodes)
      const objCardStartX = objColX + (objSlotWidth - objCardTotalWidth) / 2

      let objOffset = 0
      const objCardLayouts = objNodes.map((n) => {
        const cardW = getNodeWidth(n)
        const posX = LANE_LEFT + objCardStartX + objOffset
        objOffset += cardW + CARD_GAP
        return {
          key: `card-${prop.id}-obj-${n.id}`,
          node: n,
          x: posX,
          y: laneTop + 23,
          role: "obj",
          propId: prop.id,
        }
      })

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
      }
    })
  }, [propsForLanes, nodes])

  const { laneCardItems, unusedNodes } = useMemo(() => {
    const items = []
    const usedIds = new Set()
    const seenNodeIds = new Set()

    laneLayouts.forEach((lane) => {
      lane.subjNodes.forEach((item) => {
        const isDuplicate = seenNodeIds.has(item.node.id)
        seenNodeIds.add(item.node.id)
        items.push({ ...item, isDuplicate })
        usedIds.add(item.node.id)
      })
      lane.predNodes.forEach((item) => {
        const isDuplicate = seenNodeIds.has(item.node.id)
        seenNodeIds.add(item.node.id)
        items.push({ ...item, isDuplicate })
        usedIds.add(item.node.id)
      })
      lane.objNodes.forEach((item) => {
        const isDuplicate = seenNodeIds.has(item.node.id)
        seenNodeIds.add(item.node.id)
        items.push({ ...item, isDuplicate })
        usedIds.add(item.node.id)
      })
    })

    const unused = nodes.filter((n) => !usedIds.has(n.id))

    return { laneCardItems: items, unusedNodes: unused }
  }, [laneLayouts, nodes])

  const activePathEdgeIds = useMemo(() => {
    const set = new Set()
    if (selectedNode && (isPhase02 || stage === "PHASE_02")) {
      let currNodeId = selectedNode.id
      const visited = new Set()
      while (currNodeId && !visited.has(currNodeId)) {
        visited.add(currNodeId)
        const incomingEdge = edges.find((e) => e.toId === currNodeId)
        if (incomingEdge) {
          set.add(incomingEdge.id)
          currNodeId = incomingEdge.fromId
        } else {
          break
        }
      }
    }
    return set
  }, [selectedNode, edges, isPhase02, stage])

  const maxLaneWidth = laneLayouts.length > 0 ? laneLayouts[0].laneWidth : 760

  const contentWidth = useMemo(() => {
    if (isPhase01) return 1060
    if (isPhase02) return Math.max(parseData?.maxX || 880, 800)
    if (isPhase03) return 50 + maxLaneWidth + 50
    if (isPhase04 || isPhase05 || isPhase06) return 1000
    return 1000
  }, [
    isPhase01,
    isPhase02,
    isPhase03,
    isPhase04,
    isPhase05,
    isPhase06,
    parseData?.maxX,
    maxLaneWidth,
  ])

  const lastTopRow = useMemo(() => {
    const matchedStudentIndices = matchedPairs.map((p) => p.student_index)
    const maxMatchedStudentIdx =
      matchedStudentIndices.length > 0 ? Math.max(...matchedStudentIndices) : 0
    const maxRefIdx = referenceProps.length > 0 ? referenceProps.length - 1 : 0
    return Math.max(maxMatchedStudentIdx, maxRefIdx, 0)
  }, [matchedPairs, referenceProps.length])

  const p5Section2Top = useMemo(
    () => 28 + (lastTopRow + 1) * 114 + 18,
    [lastTopRow],
  )

  const contentHeight = useMemo(() => {
    if (isPhase01) return 780
    if (isPhase02) return Math.max(parseData?.maxY || 460, 400)
    if (isPhase03) return Math.max(28 + activeProps.length * 114 + 60, 360)
    if (isPhase04) {
      const maxCount = Math.max(studentProps.length, referenceProps.length, 1)
      return Math.max(28 + maxCount * 114 + 60, 380)
    }
    if (isPhase05) {
      const s2Rows = Math.max(unmatchedStudentProps.length, 1)
      return Math.max(p5Section2Top + 24 + s2Rows * 114 + 40, 480)
    }
    if (isPhase06) {
      return 420
    }
    return 500
  }, [
    isPhase01,
    isPhase02,
    isPhase03,
    isPhase04,
    isPhase05,
    isPhase06,
    parseData?.maxY,
    activeProps.length,
    studentProps.length,
    referenceProps.length,
    p5Section2Top,
    unmatchedStudentProps.length,
  ])

  const contentBounds = useMemo(() => {
    const anno = PHASE_ANNOTATION_CONFIG[activePhase]
    const aLeft = parseFloat(anno?.left) || 0
    const aTop = parseFloat(anno?.top) || 0
    const aWidth = 360
    const aHeight = 64

    let baseMinX = 0
    let baseMinY = 0
    let baseMaxX = contentWidth
    let baseMaxY = contentHeight

    if (isPhase01) {
      const cardLeft = Math.max(40, (contentWidth - 980) / 2)
      baseMinX = cardLeft
      baseMinY = 72
      baseMaxX = cardLeft + 980
      baseMaxY = 72 + 600
    } else if (isPhase02) {
      baseMinX = 40
      baseMinY = 20
      baseMaxX = Math.max(parseData?.maxX || 880, 800)
      baseMaxY = Math.max(parseData?.maxY || 460, 400)
    } else if (isPhase03) {
      baseMinX = 40
      baseMinY = 28
      baseMaxX = 40 + maxLaneWidth
      baseMaxY = 28 + activeProps.length * 114
    } else if (isPhase04) {
      const maxCount = Math.max(studentProps.length, referenceProps.length, 1)
      baseMinX = 50
      baseMinY = 4
      baseMaxX = 950
      baseMaxY = 28 + maxCount * 114
    } else if (isPhase05) {
      const s2Rows = Math.max(unmatchedStudentProps.length, 1)
      baseMinX = 50
      baseMinY = 4
      baseMaxX = 950
      baseMaxY = p5Section2Top + 24 + s2Rows * 114
    } else if (isPhase06) {
      const left = Math.max(40, (contentWidth - 920) / 2)
      baseMinX = left
      baseMinY = 4
      baseMaxX = left + 920
      baseMaxY = 420
    }

    return {
      minX: Math.min(baseMinX, aLeft),
      minY: Math.min(baseMinY, aTop),
      maxX: Math.max(baseMaxX, aLeft + aWidth),
      maxY: Math.max(baseMaxY, aTop + aHeight),
    }
  }, [
    activePhase,
    contentWidth,
    contentHeight,
    isPhase01,
    isPhase02,
    isPhase03,
    isPhase04,
    isPhase05,
    isPhase06,
    parseData?.maxX,
    parseData?.maxY,
    maxLaneWidth,
    activeProps.length,
    studentProps.length,
    referenceProps.length,
    p5Section2Top,
    unmatchedStudentProps.length,
  ])

  const getP5StudentPos = useCallback(
    (propId, defaultTop) => {
      const isMatched = matchedStudentIds.has(propId)
      if (isMatched) {
        return {
          top: defaultTop,
          isMatched: true,
        }
      }

      const unmatchedIdx = unmatchedStudentProps.findIndex(
        (p) => p.id === propId,
      )
      const finalTop =
        p5Section2Top + 24 + (unmatchedIdx >= 0 ? unmatchedIdx : 0) * 114

      const shouldMove =
        effectiveP5FromPhase !== "04" ||
        p5AnimStage === "STEP_2_MOVE_UNMATCHED" ||
        p5AnimStage === "STEP_3_LABEL" ||
        p5AnimStage === "STEP_4_CLASSIFICATION" ||
        p5AnimStage === "STEP_5_SETTLED"

      return {
        top: shouldMove ? finalTop : defaultTop,
        isMatched: false,
        rowIndex: unmatchedIdx,
      }
    },
    [
      matchedStudentIds,
      unmatchedStudentProps,
      p5Section2Top,
      p5AnimStage,
      effectiveP5FromPhase,
    ],
  )

  const getEntailmentEvaluation = useCallback(
    (pair) => {
      const found = entailmentEvaluations.find(
        (e) =>
          e.match_id === pair.id ||
          (e.student_id === pair.student_id &&
            e.reference_id === pair.reference_id),
      )
      if (found) return found

      const score = pair.triple_score || 0
      let status = "ENTAILS"
      let evidence =
        "Student proposition semantically satisfies the reference concept."
      if (score < 0.4) {
        status = "CONTRADICTS"
        evidence = "Substantial semantic divergence from reference content."
      } else if (score < 0.7) {
        status = "UNCERTAIN"
        evidence = "Partial overlap; entailment is plausible but uncertain."
      }

      return {
        match_id: pair.id,
        reference_id: pair.reference_id,
        student_id: pair.student_id,
        status,
        confidence: score,
        evidence,
        subject_similarity: pair.subject_similarity,
        predicate_similarity: pair.predicate_similarity,
        object_similarity: pair.object_similarity,
      }
    },
    [entailmentEvaluations],
  )

  const getUnmatchedEvaluation = useCallback(
    (prop) => {
      const found = unmatchedAddProps.find(
        (u) => u.student_prop_id === prop.id || u.text === prop.text,
      )
      if (found) return found

      return {
        id: `unmatched_${prop.id}`,
        student_prop_id: prop.id,
        text: prop.text,
        span_text: prop.text,
        char_start: prop.char_start,
        char_end: prop.char_end,
        classification: "UNCERTAIN",
        score_effect: 0.0,
        rationale: "Unmatched proposition evaluated for epistemic validity.",
        severity_level: "NONE",
      }
    },
    [unmatchedAddProps],
  )

  const activeSelectionP4 = useMemo(() => {
    const activeMatch = hoveredMatchId || selectedMatchId
    if (activeMatch) {
      const match = matchedPairs.find((m) => m.id === activeMatch)
      if (match) {
        return {
          matchId: match.id,
          studentId: match.student_id,
          referenceId: match.reference_id,
        }
      }
    }

    const activeProp = hoveredP4PropId || selectedP4PropId
    if (activeProp) {
      const matchForStu = matchedPairs.find((m) => m.student_id === activeProp)
      if (matchForStu) {
        return {
          matchId: matchForStu.id,
          studentId: matchForStu.student_id,
          referenceId: matchForStu.reference_id,
        }
      }
      const matchForRef = matchedPairs.find(
        (m) => m.reference_id === activeProp,
      )
      if (matchForRef) {
        return {
          matchId: matchForRef.id,
          studentId: matchForRef.student_id,
          referenceId: matchForRef.reference_id,
        }
      }
      if (activeProp.startsWith("stu_")) {
        return { matchId: null, studentId: activeProp, referenceId: null }
      }
      return { matchId: null, studentId: null, referenceId: activeProp }
    }

    return { matchId: null, studentId: null, referenceId: null }
  }, [
    hoveredMatchId,
    selectedMatchId,
    hoveredP4PropId,
    selectedP4PropId,
    matchedPairs,
  ])

  const highlightPropForPhase04 = useMemo(() => {
    if (parseMode === "student") {
      if (!activeSelectionP4.studentId) return null
      return (
        studentProps.find((p) => p.id === activeSelectionP4.studentId) || null
      )
    } else {
      if (!activeSelectionP4.referenceId) return null
      return (
        referenceProps.find((p) => p.id === activeSelectionP4.referenceId) ||
        null
      )
    }
  }, [parseMode, activeSelectionP4, studentProps, referenceProps])

  const handleSelectP4StudentCard = (prop) => {
    setSelectedUnmatchedProp(null)
    const match = matchedPairs.find((m) => m.student_id === prop.id)
    if (match) {
      setSelectedMatchId(match.id)
      setSelectedP4PropId(null)
    } else {
      setSelectedMatchId(null)
      setSelectedP4PropId(prop.id)
      setSelectedUnmatchedProp({
        id: prop.id,
        idLabel: `P${prop.index + 1}`,
        side: "student",
        text: prop.text,
        index: prop.index,
      })
    }
    if (onSwitchParseMode) onSwitchParseMode("student")
  }

  const handleSelectP4ReferenceCard = (prop) => {
    setSelectedUnmatchedProp(null)
    const match = matchedPairs.find((m) => m.reference_id === prop.id)
    if (match) {
      setSelectedMatchId(match.id)
      setSelectedP4PropId(null)
    } else {
      setSelectedMatchId(null)
      setSelectedP4PropId(prop.id)
      setSelectedUnmatchedProp({
        id: prop.id,
        idLabel: `R${prop.index + 1}`,
        side: "reference",
        text: prop.text,
        index: prop.index,
      })
    }
    if (onSwitchParseMode) onSwitchParseMode("reference")
  }

  const activeSelectionP5 = useMemo(() => {
    let matchIdToUse = selectedP5MatchedId
    if (hoveredP5Id) {
      if (hoveredP5Id.startsWith("match_")) {
        matchIdToUse = hoveredP5Id
      } else {
        const matchForHover = matchedPairs.find(
          (m) => m.student_id === hoveredP5Id || m.reference_id === hoveredP5Id,
        )
        if (matchForHover) {
          matchIdToUse = matchForHover.id
        }
      }
    }

    if (matchIdToUse) {
      const match = matchedPairs.find((m) => m.id === matchIdToUse)
      if (match) {
        return {
          matchId: match.id,
          studentId: match.student_id,
          referenceId: match.reference_id,
          unmatchedId: null,
        }
      }
    }

    const activeUnmatched =
      hoveredP5Id && !hoveredP5Id.startsWith("match_")
        ? hoveredP5Id
        : selectedP5UnmatchedId
    if (activeUnmatched) {
      return {
        matchId: null,
        studentId: activeUnmatched.startsWith("stu_") ? activeUnmatched : null,
        referenceId: activeUnmatched.startsWith("ref_")
          ? activeUnmatched
          : null,
        unmatchedId: activeUnmatched,
      }
    }

    return {
      matchId: null,
      studentId: null,
      referenceId: null,
      unmatchedId: null,
    }
  }, [hoveredP5Id, selectedP5MatchedId, selectedP5UnmatchedId, matchedPairs])

  const highlightPropForPhase05 = useMemo(() => {
    if (parseMode === "student") {
      if (!activeSelectionP5.studentId) return null
      return (
        studentProps.find((p) => p.id === activeSelectionP5.studentId) || null
      )
    } else {
      if (!activeSelectionP5.referenceId) return null
      return (
        referenceProps.find((p) => p.id === activeSelectionP5.referenceId) ||
        null
      )
    }
  }, [parseMode, activeSelectionP5, studentProps, referenceProps])

  const handleSelectP5StudentCard = (prop) => {
    const match = matchedPairs.find((m) => m.student_id === prop.id)
    if (match) {
      setSelectedP5UnmatchedId(null)
      setSelectedP5MatchedId(match.id)
    } else {
      setSelectedP5MatchedId(null)
      setSelectedP5UnmatchedId(prop.id)
    }
    if (onSwitchParseMode) onSwitchParseMode("student")
  }

  const handleSelectP5ReferenceCard = (prop) => {
    const match = matchedPairs.find((m) => m.reference_id === prop.id)
    if (match) {
      setSelectedP5UnmatchedId(null)
      setSelectedP5MatchedId(match.id)
    } else {
      setSelectedP5MatchedId(null)
      setSelectedP5UnmatchedId(null)
    }
    if (onSwitchParseMode) onSwitchParseMode("reference")
  }

  const handleCanvasClickOutside = useCallback(() => {
    if (isPhase04) {
      setSelectedMatchId(null)
      setSelectedUnmatchedProp(null)
      setSelectedP4PropId(null)
    }
    if (isPhase05) {
      setSelectedP5MatchedId(null)
      setSelectedP5UnmatchedId(null)
    }
  }, [isPhase04, isPhase05])

  const selectedP5Unmatched = useMemo(() => {
    if (!selectedP5UnmatchedId) return null
    const prop =
      studentProps.find((p) => p.id === selectedP5UnmatchedId) ||
      referenceProps.find((p) => p.id === selectedP5UnmatchedId)
    if (!prop) return null
    return {
      prop,
      evaluation: getUnmatchedEvaluation(prop),
      isStudent: prop.id.startsWith("stu_"),
    }
  }, [
    selectedP5UnmatchedId,
    studentProps,
    referenceProps,
    getUnmatchedEvaluation,
  ])

  const phase06Spans = useMemo(() => {
    return studentProps.map((prop, idx) => {
      const match = matchedPairs.find((m) => m.student_id === prop.id)
      let role
      let assessment
      let scoreEffect = 0.0
      let scoreEffectLabel
      let evidence
      let referenceProp = null
      let referenceText = ""
      let unmatchedInfo = null
      let entailment = null

      if (match) {
        role = "CORE_INFORMATION"
        entailment = getEntailmentEvaluation(match)
        assessment = entailment?.status || "ENTAILS"
        evidence =
          entailment?.evidence ||
          "Student proposition semantically satisfies reference ground truth."
        referenceProp =
          referenceProps.find((r) => r.id === match.reference_id) || null
        referenceText = referenceProp?.text || match.reference_text || ""
        scoreEffectLabel = "Core credit"
      } else {
        unmatchedInfo = getUnmatchedEvaluation(prop)
        role = unmatchedInfo?.classification || "UNCERTAIN"
        assessment = unmatchedInfo?.classification || "UNCERTAIN"
        scoreEffect =
          typeof unmatchedInfo?.score_effect === "number"
            ? unmatchedInfo.score_effect
            : 0.0
        evidence =
          unmatchedInfo?.rationale ||
          "Unmatched proposition evaluated for domain validity."
        scoreEffectLabel =
          scoreEffect > 0
            ? `+${scoreEffect.toFixed(2)} pts`
            : scoreEffect < 0
              ? `${scoreEffect.toFixed(2)} pts`
              : "+0.00 pts"
      }

      let charStart = prop.char_start
      let charEnd = prop.char_end

      if (
        typeof charStart !== "number" ||
        typeof charEnd !== "number" ||
        charStart < 0 ||
        charEnd <= charStart ||
        charEnd > studentAnswer.length
      ) {
        const searchTarget = (prop.span_text || prop.text || "").trim()
        if (searchTarget && studentAnswer) {
          const foundIdx = studentAnswer
            .toLowerCase()
            .indexOf(searchTarget.toLowerCase())
          if (foundIdx >= 0) {
            charStart = foundIdx
            charEnd = foundIdx + searchTarget.length
          } else {
            charStart = 0
            charEnd = studentAnswer.length
          }
        } else {
          charStart = 0
          charEnd = studentAnswer.length
        }
      }

      return {
        id: prop.id,
        index: idx,
        prop,
        role,
        assessment,
        scoreEffect,
        scoreEffectLabel,
        evidence,
        referenceProp,
        referenceText,
        unmatchedInfo,
        entailment,
        match,
        char_start: charStart,
        char_end: charEnd,
      }
    })
  }, [
    studentProps,
    matchedPairs,
    referenceProps,
    studentAnswer,
    getEntailmentEvaluation,
    getUnmatchedEvaluation,
  ])

  const renderedAnswerSegments = useMemo(() => {
    if (!studentAnswer) return []
    if (!phase06Spans || phase06Spans.length === 0) {
      return [{ isSpan: false, text: studentAnswer }]
    }

    const validSpans = [...phase06Spans]
      .filter((s) => s.char_start >= 0 && s.char_end > s.char_start)
      .sort((a, b) => a.char_start - b.char_start)

    if (validSpans.length === 0) {
      return [{ isSpan: false, text: studentAnswer }]
    }

    const segments = []
    let cursor = 0

    validSpans.forEach((span) => {
      const start = Math.max(
        cursor,
        Math.min(span.char_start, studentAnswer.length),
      )
      const end = Math.max(start, Math.min(span.char_end, studentAnswer.length))

      if (start > cursor) {
        segments.push({
          isSpan: false,
          text: studentAnswer.slice(cursor, start),
        })
      }

      if (end > start) {
        segments.push({
          isSpan: true,
          span,
          text: studentAnswer.slice(start, end),
        })
        cursor = end
      }
    })

    if (cursor < studentAnswer.length) {
      segments.push({
        isSpan: false,
        text: studentAnswer.slice(cursor),
      })
    }

    return segments
  }, [studentAnswer, phase06Spans])

  const maxPoints = scoreData?.max_points ?? 5.0
  const finalGrade =
    scoreData?.final_grade !== undefined
      ? Number(scoreData.final_grade).toFixed(2)
      : "5.00"
  const baseGrade =
    scoreData?.base_grade !== undefined
      ? Number(scoreData.base_grade).toFixed(2)
      : "5.00"
  const positiveAdj =
    scoreData?.positive_adjustment !== undefined
      ? Number(scoreData.positive_adjustment).toFixed(2)
      : "0.00"
  const negativeAdj =
    scoreData?.negative_adjustment !== undefined
      ? Number(scoreData.negative_adjustment).toFixed(2)
      : "0.00"

  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      <div
        className={`grid grid-cols-1 grid-rows-1 w-full shrink-0 transition-all duration-500 ${
          isPhase01
            ? "h-0 opacity-0 overflow-hidden pointer-events-none"
            : "opacity-100"
        }`}
      >
        <div
          className={`col-start-1 row-start-1 w-full transition-opacity duration-500 ease-out ${
            isPhase02
              ? "opacity-100 pointer-events-auto"
              : "opacity-0 pointer-events-none"
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
            isPhase03
              ? "opacity-100 pointer-events-auto"
              : "opacity-0 pointer-events-none"
          }`}
        >
          <PropositionBar
            propMode={propMode}
            onSwitchPropMode={(mode) => {
              setPropMode(mode)
              if (onSwitchParseMode) onSwitchParseMode(mode)
            }}
            studentCount={studentProps.length}
            referenceCount={referenceProps.length}
            fullText={fullText}
            selectedProp={selectedProp}
          />
        </div>

        <div
          className={`col-start-1 row-start-1 w-full transition-opacity duration-500 ease-out ${
            isPhase04
              ? "opacity-100 pointer-events-auto"
              : "opacity-0 pointer-events-none"
          }`}
        >
          <AlignmentBar
            answerMode={parseMode}
            onSwitchAnswerMode={onSwitchParseMode}
            fullText={parseMode === "student" ? studentAnswer : referenceAnswer}
            highlightProp={highlightPropForPhase04}
          />
        </div>

        <div
          className={`col-start-1 row-start-1 w-full transition-opacity duration-500 ease-out ${
            isPhase05
              ? "opacity-100 pointer-events-auto"
              : "opacity-0 pointer-events-none"
          }`}
        >
          <AssessmentBar
            answerMode={parseMode}
            onSwitchAnswerMode={onSwitchParseMode}
            fullText={parseMode === "student" ? studentAnswer : referenceAnswer}
            highlightProp={highlightPropForPhase05}
          />
        </div>

        <div
          className={`col-start-1 row-start-1 w-full transition-opacity duration-500 ease-out ${
            isPhase06
              ? "opacity-100 pointer-events-auto"
              : "opacity-0 pointer-events-none"
          }`}
        >
          <ResultBar
            answerMode={parseMode}
            onSwitchAnswerMode={onSwitchParseMode}
            fullText={parseMode === "student" ? studentAnswer : referenceAnswer}
            highlightProp={null}
          />
        </div>
      </div>

      <div className="flex-1 flex min-h-0 relative w-full overflow-hidden">
        <div className="relative flex-1 h-full min-w-0 overflow-hidden">
          <InfiniteCanvas
            zoom={zoom}
            onZoomChange={onZoomChange}
            showGrid={showGrid}
            contentWidth={contentWidth}
            contentHeight={contentHeight}
            contentBounds={contentBounds}
            fitTrigger={fitTrigger + internalFitTrigger}
            allowWheelZoom={!isPhase01}
            phaseKey={activePhase}
            onCanvasClick={handleCanvasClickOutside}
          >
            <div
              style={{
                width: `${contentWidth}px`,
                height: `${contentHeight}px`,
              }}
              onClick={(e) => {
                if (
                  !e.target.closest(
                    '[data-interactive="true"], button, a, select, input, textarea',
                  )
                ) {
                  handleCanvasClickOutside()
                }
              }}
              className="relative select-none"
            >
              {Object.entries(PHASE_ANNOTATION_CONFIG).map(
                ([phaseKey, cfg]) => (
                  <PhaseAnnotation
                    key={`phase-anno-${phaseKey}`}
                    number={cfg.number}
                    title={cfg.title}
                    description={cfg.description}
                    connector={cfg.connector}
                    titleSize={cfg.titleSize}
                    descSize={cfg.descSize}
                    visible={activePhase === phaseKey}
                    style={{
                      left: cfg.left,
                      top: cfg.top,
                    }}
                  />
                ),
              )}

              <div
                style={{
                  position: "absolute",
                  left: `${Math.max(40, (contentWidth - 980) / 2)}px`,
                  top: "72px",
                  width: "980px",
                  opacity: isPhase01 ? 1 : 0,
                  pointerEvents: isPhase01 ? "auto" : "none",
                  transition:
                    "opacity 0.6s cubic-bezier(0.45, 0.05, 0.15, 0.98)",
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

              {(isPhase02 ||
                stage === "STEP_1_FADE" ||
                stage === "REVERSE_MOVE") && (
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
                      id="arrowhead-dimmed-sync"
                      markerWidth="10"
                      markerHeight="10"
                      refX="1"
                      refY="5"
                      orient="auto"
                      markerUnits="userSpaceOnUse"
                    >
                      <path d="M 1 2 L 7 5 L 1 8 Z" fill="#b0a898" />
                    </marker>
                  </defs>

                  <g
                    className="transition-opacity duration-600 cubic-bezier(0.45, 0.05, 0.15, 0.98)"
                    style={{
                      opacity:
                        stage === "STEP_1_FADE"
                          ? 0
                          : stage === "STEP_2_MOVE"
                            ? 0
                            : stage === "REVERSE_MOVE"
                              ? 1
                              : isPhase02
                                ? p2FadeIn
                                  ? 1
                                  : 0
                                : 0,
                    }}
                  >
                    {edges.map((edge) => {
                      const isHighlighted = activePathEdgeIds.has(edge.id)
                      const verticalDist = Math.max(30, edge.toY - edge.fromY)
                      const controlOffset = Math.max(25, verticalDist * 0.45)
                      const pathD = `M ${edge.fromX} ${edge.fromY} C ${edge.fromX} ${edge.fromY + controlOffset}, ${edge.toX} ${edge.toY - controlOffset}, ${edge.toX} ${edge.toY}`
                      const labelText = edge.label || "dep"
                      const badgeWidth = Math.max(
                        28,
                        labelText.length * 6.5 + 12,
                      )
                      const badgeHeight = 17

                      return (
                        <g key={edge.id} className="cursor-pointer">
                          <path
                            d={pathD}
                            stroke={isHighlighted ? "#3730a3" : "#b5ab9b"}
                            strokeWidth={isHighlighted ? 2.4 : 1.4}
                            fill="none"
                            markerEnd={
                              isHighlighted
                                ? "url(#arrowhead-primary-sync)"
                                : "url(#arrowhead-dimmed-sync)"
                            }
                            className="transition-colors duration-150"
                          />
                          <rect
                            x={edge.midX - badgeWidth / 2}
                            y={edge.midY - badgeHeight / 2}
                            width={badgeWidth}
                            height={badgeHeight}
                            rx={4}
                            fill="#fdfcf9"
                            stroke={isHighlighted ? "#3730a3" : "#dfd8c8"}
                            strokeWidth={isHighlighted ? 1.5 : 1}
                          />
                          <text
                            x={edge.midX}
                            y={edge.midY + 1}
                            textAnchor="middle"
                            dominantBaseline="middle"
                            fontSize="9"
                            fontFamily="monospace"
                            fill={isHighlighted ? "#3730a3" : "#706b63"}
                            fontWeight={isHighlighted ? "bold" : "600"}
                          >
                            {labelText}
                          </text>
                        </g>
                      )
                    })}
                  </g>
                </svg>
              )}

              {isPhase04 && (
                <div
                  style={{
                    opacity: isPhase04 ? 1 : 0,
                    pointerEvents: isPhase04 ? "auto" : "none",
                    transition: "opacity 0.3s ease-out",
                  }}
                  className="absolute inset-x-0 top-0 pointer-events-none z-20"
                >
                  <div
                    style={{ left: "50px", top: "4px", width: "340px" }}
                    className="absolute flex items-center justify-between pb-1 px-1"
                  >
                    <span className="text-[11px] font-mono font-bold tracking-wider text-[#7a7266] uppercase">
                      Student Propositions
                    </span>
                    <span className="text-[10px] font-mono text-[#8c8477]">
                      {studentProps.length}{" "}
                      {studentProps.length === 1 ? "assertion" : "assertions"}
                    </span>
                  </div>

                  <div
                    style={{ left: "610px", top: "4px", width: "340px" }}
                    className="absolute flex items-center justify-between pb-1 px-1"
                  >
                    <span className="text-[11px] font-mono font-bold tracking-wider text-[#7a7266] uppercase">
                      Reference Propositions
                    </span>
                    <span className="text-[10px] font-mono text-[#8c8477]">
                      {referenceProps.length}{" "}
                      {referenceProps.length === 1 ? "assertion" : "assertions"}
                    </span>
                  </div>
                </div>
              )}

              {(isPhase03 || isPhase04 || isPhase05) && (
                <div
                  className="absolute inset-0 pointer-events-none z-10 transition-opacity duration-600 cubic-bezier(0.45, 0.05, 0.15, 0.98)"
                  style={{ opacity: boundariesOpacity }}
                >
                  {laneLayouts.map((lane) => {
                    const isSelected = selectedPropId === lane.prop.id
                    const isSelectedP4 =
                      isPhase04 &&
                      (activeSelectionP4.studentId === lane.prop.id ||
                        hoveredP4PropId === lane.prop.id)
                    const isMatchedP4 =
                      isPhase04 && matchedStudentIds.has(lane.prop.id)
                    const isUnmatchedP4 = isPhase04 && !isMatchedP4

                    const isSelectedP5 =
                      isPhase05 &&
                      (activeSelectionP5.studentId === lane.prop.id ||
                        activeSelectionP5.unmatchedId === lane.prop.id ||
                        hoveredP5Id === lane.prop.id)
                    const isMatchedP5 =
                      isPhase05 && matchedStudentIds.has(lane.prop.id)
                    const isUnmatchedP5 = isPhase05 && !isMatchedP5
                    const p5Pos = isPhase05
                      ? getP5StudentPos(lane.prop.id, lane.laneTop)
                      : null
                    const cardTop = isPhase05
                      ? `${p5Pos.top}px`
                      : `${lane.laneTop}px`

                    return (
                      <div
                        key={`lane-box-${lane.prop.id}`}
                        data-interactive="true"
                        onClick={() => {
                          if (isPhase05) {
                            handleSelectP5StudentCard(lane.prop)
                          } else if (isPhase04) {
                            handleSelectP4StudentCard(lane.prop)
                          } else {
                            setSelectedPropId(lane.prop.id)
                          }
                        }}
                        onMouseEnter={() => {
                          if (isPhase05) setHoveredP5Id(lane.prop.id)
                          else if (isPhase04) setHoveredP4PropId(lane.prop.id)
                        }}
                        onMouseLeave={() => {
                          if (isPhase05) setHoveredP5Id(null)
                          else if (isPhase04) setHoveredP4PropId(null)
                        }}
                        style={{
                          left: `${lane.laneLeft}px`,
                          top: cardTop,
                          width:
                            isPhase04 || isPhase05
                              ? "340px"
                              : `${lane.laneWidth}px`,
                          height:
                            isPhase04 || isPhase05
                              ? "82px"
                              : `${lane.laneHeight}px`,
                          pointerEvents:
                            boundariesOpacity > 0 ? "auto" : "none",
                          transition:
                            "top 0.8s cubic-bezier(0.16, 1, 0.3, 1), left 0.45s cubic-bezier(0.4, 0, 0.2, 1), width 0.45s cubic-bezier(0.4, 0, 0.2, 1), height 0.45s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s, box-shadow 0.2s, background-color 0.2s",
                        }}
                        className={`absolute rounded-2xl cursor-pointer ${
                          isPhase05
                            ? isSelectedP5
                              ? "bg-[#faf8f4] border-2 border-indigo-700 shadow-md ring-2 ring-indigo-700/15"
                              : isMatchedP5
                                ? "bg-[#fdfcf9] border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs"
                                : "bg-[#faf8f4] border border-[#dfd8c8] hover:border-[#b5ab9b]"
                            : isPhase04
                              ? isSelectedP4
                                ? "bg-[#faf8f4] border-2 border-indigo-700 shadow-md ring-2 ring-indigo-700/15"
                                : isMatchedP4
                                  ? "bg-[#fdfcf9] border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs"
                                  : "bg-[#faf8f4] border border-[#dfd8c8] hover:border-[#b5ab9b]"
                              : isSelected
                                ? "bg-[#fdfcf9] border-2 border-indigo-700 shadow-md ring-2 ring-indigo-700/10"
                                : "bg-[#fdfcf9]/95 border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs"
                        }`}
                      >
                        <div
                          style={{
                            opacity: isPhase04 || isPhase05 ? 0 : 1,
                            pointerEvents:
                              isPhase04 || isPhase05 ? "none" : "auto",
                            transition: "opacity 0.22s ease-out",
                          }}
                          className="absolute inset-0 overflow-hidden"
                        >
                          <div
                            style={{
                              left: "18px",
                              top: "14px",
                              width: "135px",
                              height: "68px",
                            }}
                            className="absolute flex flex-col justify-between select-none"
                          >
                            <div className="flex items-center gap-1.5 font-mono">
                              <span className="text-[13px] font-bold text-indigo-950 tracking-wide">
                                {propMode === "reference" ? "R" : "P"}
                                {lane.propIdx + 1}
                              </span>
                              <span className="text-[#a89e8f] text-[11px] select-none">
                                —
                              </span>
                              <span className="text-[10px] text-[#706b63] font-semibold tracking-tight uppercase">
                                {lane.prop.representation_type}
                              </span>
                            </div>

                            <div className="flex items-center gap-1.5 mt-auto">
                              <span
                                className={`text-[9.5px] font-mono font-semibold px-2 py-0.5 rounded border ${
                                  lane.prop.polarity === "NEGATIVE"
                                    ? "bg-rose-50 text-rose-800 border-rose-200"
                                    : "bg-emerald-50 text-emerald-800 border-emerald-200"
                                }`}
                              >
                                {lane.prop.polarity}
                              </span>
                            </div>
                          </div>

                          <div
                            style={{
                              left: "165px",
                              top: "14px",
                              width: "1px",
                              height: "68px",
                            }}
                            className="absolute bg-[#dfd8c8]"
                          />

                          <div
                            style={{
                              left: `${lane.subjColX}px`,
                              top: "7px",
                              width: `${lane.subjSlotWidth}px`,
                            }}
                            className="absolute text-center text-[9px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold select-none"
                          >
                            Subject
                          </div>

                          <div
                            style={{
                              left: `${lane.arrow1ColX}px`,
                              top: "36px",
                              width: "24px",
                            }}
                            className="absolute text-center text-indigo-900 font-mono text-[16px] font-bold select-none"
                          >
                            →
                          </div>

                          <div
                            style={{
                              left: `${lane.predColX}px`,
                              top: "7px",
                              width: `${lane.predSlotWidth}px`,
                            }}
                            className="absolute text-center text-[9px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold select-none"
                          >
                            Predicate
                          </div>

                          <div
                            style={{
                              left: `${lane.arrow2ColX}px`,
                              top: "36px",
                              width: "24px",
                            }}
                            className="absolute text-center text-indigo-900 font-mono text-[16px] font-bold select-none"
                          >
                            →
                          </div>

                          <div
                            style={{
                              left: `${lane.objColX}px`,
                              top: "7px",
                              width: `${lane.objSlotWidth}px`,
                            }}
                            className="absolute text-center text-[9px] font-mono uppercase tracking-wider text-[#7a7266] font-semibold select-none"
                          >
                            {lane.prop.object ? "Object" : "Argument"}
                          </div>
                        </div>

                        <div
                          style={{
                            opacity: isPhase04 || isPhase05 ? 1 : 0,
                            pointerEvents:
                              isPhase04 || isPhase05 ? "auto" : "none",
                            transition: "opacity 0.3s ease-in 0.15s",
                          }}
                          className="absolute inset-0 p-3.5 flex flex-col justify-between overflow-hidden select-none"
                        >
                          <div className="flex items-center justify-between gap-2 mb-1.5 font-mono">
                            <div className="flex items-center gap-1.5">
                              <span className="text-[12.5px] font-bold text-indigo-950">
                                P{lane.propIdx + 1}
                              </span>
                              <span className="text-[#a89e8f] text-[11px] select-none">
                                —
                              </span>
                              <span className="text-[10px] text-[#706b63] font-semibold uppercase tracking-tight px-1.5 py-0.5 rounded bg-[#f4f0e8] border border-[#dfd8c8]">
                                {lane.prop.representation_type || "TRIPLE"}
                              </span>
                            </div>

                            {((isPhase04 &&
                              isUnmatchedP4 &&
                              showUnmatchedStatus) ||
                              (isPhase05 && isUnmatchedP5)) && (
                              <span className="text-[9.5px] font-mono font-semibold px-2 py-0.5 rounded bg-[#ede8dc] text-[#706b63] border border-[#dfd8c8] tracking-tight">
                                {isPhase05
                                  ? "ADDITIONAL ASSERTION"
                                  : "UNMATCHED"}
                              </span>
                            )}

                            {((isPhase04 && isMatchedP4) ||
                              (isPhase05 && isMatchedP5)) && (
                              <span
                                className={`w-2 h-2 rounded-full transition-colors ${
                                  isSelectedP4 || isSelectedP5
                                    ? "bg-indigo-700"
                                    : "bg-indigo-400"
                                }`}
                              />
                            )}
                          </div>

                          <div className="text-[13px] font-medium text-[#1e1c19] leading-snug truncate">
                            &ldquo;{lane.prop.text}&rdquo;
                          </div>
                        </div>
                      </div>
                    )
                  })}

                  <div
                    style={{
                      opacity: isPhase04 || isPhase05 ? 0 : 1,
                      transition: "opacity 0.22s ease-out",
                      pointerEvents: isPhase04 || isPhase05 ? "none" : "auto",
                    }}
                  >
                    {laneLayouts.map((lane) => (
                      <div key={`placeholders-${lane.prop.id}`}>
                        {lane.subjNodes.length === 0 && (
                          <div
                            style={{
                              left: `${lane.laneLeft + lane.subjColX + (lane.subjSlotWidth - 88) / 2}px`,
                              top: `${lane.laneTop + 23}px`,
                              width: "88px",
                              height: "50px",
                              position: "absolute",
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
                              width: "88px",
                              height: "50px",
                              position: "absolute",
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
                              width: "88px",
                              height: "50px",
                              position: "absolute",
                            }}
                            className="flex items-center justify-center rounded-xl bg-[#f4f0e8] border border-[#dfd8c8] text-[11px] font-mono text-[#8c8477] italic select-none"
                          >
                            —
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {(isPhase04 || isPhase05 || isExitingP4P5) && (
                <div
                  style={{
                    opacity: isPhase04
                      ? p4RefCardsVisible
                        ? 1
                        : 0
                      : isPhase05
                        ? effectiveP5FromPhase === "04" || p5RefCardsVisible
                          ? 1
                          : 0
                        : 0,
                    transform: isPhase04
                      ? p4RefCardsVisible
                        ? "translateX(0)"
                        : "translateX(24px)"
                      : isPhase05
                        ? effectiveP5FromPhase === "04" || p5RefCardsVisible
                          ? "translateX(0)"
                          : "translateX(24px)"
                        : "translateX(24px)",
                    pointerEvents: isPhase04 || isPhase05 ? "auto" : "none",
                    transition:
                      "opacity 0.4s ease-out, transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
                  }}
                  className="absolute inset-0 pointer-events-none z-20"
                >
                  {referenceProps.map((prop, idx) => {
                    const isMatched = matchedReferenceIds.has(prop.id)
                    const isUnmatched = !isMatched
                    const isSelected = isPhase05
                      ? activeSelectionP5.referenceId === prop.id ||
                        hoveredP5Id === prop.id
                      : activeSelectionP4.referenceId === prop.id ||
                        hoveredP4PropId === prop.id
                    const refTop = `${28 + idx * 114}px`

                    return (
                      <div
                        key={`ref-${prop.id}`}
                        data-interactive="true"
                        onClick={() => {
                          if (isPhase05) handleSelectP5ReferenceCard(prop)
                          else handleSelectP4ReferenceCard(prop)
                        }}
                        onMouseEnter={() => {
                          if (isPhase05) setHoveredP5Id(prop.id)
                          else setHoveredP4PropId(prop.id)
                        }}
                        onMouseLeave={() => {
                          if (isPhase05) setHoveredP5Id(null)
                          else setHoveredP4PropId(null)
                        }}
                        style={{
                          left: "610px",
                          top: refTop,
                          width: "340px",
                          height: "82px",
                          transition:
                            "top 0.8s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s, box-shadow 0.2s, background-color 0.2s",
                        }}
                        className={`absolute rounded-2xl p-3.5 flex flex-col justify-between transition-all cursor-pointer pointer-events-auto border ${
                          isSelected
                            ? "bg-[#faf8f4] border-2 border-indigo-700 shadow-md ring-2 ring-indigo-700/15"
                            : isMatched
                              ? "bg-[#fdfcf9] border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs"
                              : "bg-[#faf8f4] border border-[#dfd8c8] hover:border-[#b5ab9b]"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-1.5 font-mono">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[12.5px] font-bold text-indigo-950">
                              R{prop.index + 1}
                            </span>
                            <span className="text-[#a89e8f] text-[11px] select-none">
                              —
                            </span>
                            <span className="text-[10px] text-[#706b63] font-semibold uppercase tracking-tight px-1.5 py-0.5 rounded bg-[#f4f0e8] border border-[#dfd8c8]">
                              {prop.representation_type || "TRIPLE"}
                            </span>
                          </div>

                          {isUnmatched &&
                            ((isPhase04 && showUnmatchedStatus) ||
                              isPhase05) && (
                              <span className="text-[9.5px] font-mono font-semibold px-2 py-0.5 rounded bg-[#ede8dc] text-[#706b63] border border-[#dfd8c8] tracking-tight">
                                {isPhase05
                                  ? "UNMATCHED CRITERION"
                                  : "UNMATCHED"}
                              </span>
                            )}

                          {isMatched && (
                            <span
                              className={`w-2 h-2 rounded-full transition-colors ${
                                isSelected ? "bg-indigo-700" : "bg-indigo-400"
                              }`}
                            />
                          )}
                        </div>

                        <div className="text-[13px] font-medium text-[#1e1c19] leading-snug truncate">
                          &ldquo;{prop.text}&rdquo;
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {(isPhase04 ||
                (isExitingP4P5 && prevPhaseRef.current === "04")) && (
                <svg
                  style={{
                    opacity: isPhase04 ? 1 : 0,
                    transition: "opacity 0.3s ease-out",
                  }}
                  className="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-visible"
                >
                  {matchedPairs.map((pair, idx) => {
                    const x1 = 50 + 340
                    const y1 = 28 + pair.student_index * 114 + 41
                    const x2 = 610
                    const y2 = 28 + pair.reference_index * 114 + 41
                    const dx = x2 - x1
                    const curve = `M ${x1} ${y1} C ${x1 + dx * 0.45} ${y1}, ${x2 - dx * 0.45} ${y2}, ${x2} ${y2}`
                    const isRevealed = idx < revealedMatchCount
                    const isHighlighted =
                      isRevealed && activeSelectionP4.matchId === pair.id

                    return (
                      <path
                        key={pair.id || idx}
                        d={curve}
                        fill="none"
                        stroke="#3730a3"
                        strokeWidth={isHighlighted ? 2.5 : 1.75}
                        strokeOpacity={isHighlighted ? 1 : 0.8}
                        strokeDasharray="600"
                        strokeDashoffset={isRevealed ? 0 : 600}
                        style={{
                          transition:
                            "stroke-dashoffset 350ms ease-out, stroke-width 180ms, stroke-opacity 180ms",
                        }}
                      />
                    )
                  })}
                </svg>
              )}

              {(isPhase04 ||
                (isExitingP4P5 && prevPhaseRef.current === "04")) &&
                matchedPairs.map((pair, idx) => {
                  const x1 = 50 + 340
                  const y1 = 28 + pair.student_index * 114 + 41
                  const x2 = 610
                  const y2 = 28 + pair.reference_index * 114 + 41
                  const midX = (x1 + x2) / 2
                  const midY = (y1 + y2) / 2
                  const isRevealed = idx < revealedMatchCount
                  const isHighlighted =
                    isRevealed &&
                    (activeSelectionP4.matchId === pair.id ||
                      hoveredMatchId === pair.id)

                  return (
                    <div
                      key={`badge-${pair.id || idx}`}
                      style={{
                        left: `${midX}px`,
                        top: `${midY}px`,
                        transform: "translate(-50%, -50%)",
                        opacity: isPhase04 ? (isRevealed ? 1 : 0) : 0,
                        pointerEvents:
                          isPhase04 && isRevealed ? "auto" : "none",
                        transition:
                          "opacity 250ms ease-out, transform 250ms ease-out",
                      }}
                      data-interactive="true"
                      className="absolute z-30 pointer-events-auto"
                    >
                      <div
                        onMouseEnter={() => setHoveredMatchId(pair.id)}
                        onMouseLeave={() => setHoveredMatchId(null)}
                        className={`px-3 py-1 rounded-full text-[10.5px] font-mono font-bold tracking-tight shadow-2xs transition-all cursor-default border select-none ${
                          isHighlighted
                            ? "bg-[#3730a3] text-white border-indigo-900 scale-102 shadow-sm"
                            : "bg-[#faf8f4] text-indigo-950 border-[#dfd8c8] hover:border-indigo-500 hover:bg-indigo-50"
                        }`}
                      >
                        {getMatchLabel(pair)}
                      </div>
                    </div>
                  )
                })}

              {isPhase04 && selectedUnmatchedProp && (
                <div
                  data-interactive="true"
                  style={{
                    left:
                      selectedUnmatchedProp.side === "student"
                        ? "390px"
                        : "610px",
                    top: `${28 + selectedUnmatchedProp.index * 114}px`,
                    transform:
                      selectedUnmatchedProp.side === "student"
                        ? "translate(10px, 0)"
                        : "translate(calc(-100% - 10px), 0)",
                  }}
                  className="absolute z-40 w-[260px] bg-[#fdfcf9] border border-[#dfd8c8] rounded-2xl p-3.5 shadow-xl text-left pointer-events-auto"
                >
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#dfd8c8]">
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-[#7a7266] font-bold block">
                        {selectedUnmatchedProp.side === "student"
                          ? "STUDENT ASSERTION"
                          : "REFERENCE CRITERION"}
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
                    Status:{" "}
                    <strong className="text-[#1e1c19]">UNMATCHED</strong>
                  </div>
                  <div className="text-[11.5px] font-sans text-[#706b63] leading-relaxed">
                    {selectedUnmatchedProp.side === "student"
                      ? "No corresponding reference proposition met the alignment similarity threshold."
                      : "This reference requirement was not aligned to any candidate student proposition."}
                  </div>
                </div>
              )}

              {isPhase05 && (
                <div
                  style={{
                    opacity: isPhase05 ? 1 : 0,
                    pointerEvents: isPhase05 ? "auto" : "none",
                    transition: "opacity 0.3s ease-out",
                  }}
                  className="absolute inset-x-0 top-0 pointer-events-none z-20"
                >
                  <div
                    style={{ left: "50px", top: "4px", width: "900px" }}
                    className="absolute flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[11px] font-bold tracking-wider text-[#7a7266] uppercase">
                        Matched Information
                      </span>
                      <span className="text-[#a89e8f] text-[10px]">—</span>
                      <span className="text-[10.5px] text-[#8c8477] font-normal">
                        Clausal entailment against reference answer
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-[#8c8477]">
                      {matchedPairs.length}{" "}
                      {matchedPairs.length === 1 ? "alignment" : "alignments"}
                    </span>
                  </div>
                </div>
              )}

              {(isPhase05 ||
                (isExitingP4P5 && prevPhaseRef.current === "05")) && (
                <svg
                  style={{
                    opacity: isPhase05 ? 1 : 0,
                    transition: "opacity 0.35s ease-out",
                  }}
                  className="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-visible"
                >
                  <defs>
                    <marker
                      id="arrowhead-p5-flow"
                      markerWidth="8"
                      markerHeight="8"
                      refX="6"
                      refY="4"
                      orient="auto"
                      markerUnits="userSpaceOnUse"
                    >
                      <path d="M 1 1 L 6 4 L 1 7 Z" fill="#706b63" />
                    </marker>
                  </defs>

                  {matchedPairs.map((pair, idx) => {
                    const x1 = 50 + 340
                    const y1 = 28 + pair.student_index * 114 + 41
                    const x2 = 610
                    const y2 = 28 + pair.reference_index * 114 + 41
                    const dx = x2 - x1
                    const curve = `M ${x1} ${y1} C ${x1 + dx * 0.45} ${y1}, ${x2 - dx * 0.45} ${y2}, ${x2} ${y2}`
                    const isHighlighted =
                      activeSelectionP5.matchId === pair.id ||
                      hoveredP5Id === pair.id
                    const isGrown =
                      effectiveP5FromPhase === "04" ||
                      idx < p5RevealedMatchCount

                    return (
                      <path
                        key={`p5-svg-pair-${pair.id || idx}`}
                        d={curve}
                        fill="none"
                        stroke="#3730a3"
                        strokeWidth={isHighlighted ? 2.5 : 1.75}
                        strokeOpacity={isHighlighted ? 1 : 0.8}
                        strokeDasharray="600"
                        strokeDashoffset={isGrown ? 0 : 600}
                        style={{
                          transition:
                            effectiveP5FromPhase === "04"
                              ? "stroke-width 180ms, stroke-opacity 180ms"
                              : "stroke-dashoffset 320ms ease-out, stroke-width 180ms, stroke-opacity 180ms",
                        }}
                      />
                    )
                  })}

                  {unmatchedStudentProps.map((prop, idx) => {
                    const yRow = p5Section2Top + 24 + idx * 114
                    const yCenter = yRow + 41
                    const showFlow =
                      p5AnimStage === "STEP_4_CLASSIFICATION" ||
                      p5AnimStage === "STEP_5_SETTLED"

                    return (
                      <g
                        key={`p5-svg-unmatched-flow-${prop.id}`}
                        style={{
                          opacity: showFlow ? 1 : 0,
                          transition: "opacity 350ms ease-out",
                        }}
                      >
                        <path
                          d={`M 390 ${yCenter} L 436 ${yCenter}`}
                          fill="none"
                          stroke="#b5ab9b"
                          strokeWidth={1.5}
                        />
                        <path
                          d={`M 564 ${yCenter} L 610 ${yCenter}`}
                          fill="none"
                          stroke="#b5ab9b"
                          strokeWidth={1.5}
                          markerEnd="url(#arrowhead-p5-flow)"
                        />
                      </g>
                    )
                  })}
                </svg>
              )}

              {(isPhase05 ||
                (isExitingP4P5 && prevPhaseRef.current === "05")) &&
                matchedPairs.map((pair, idx) => {
                  const x1 = 50 + 340
                  const y1 = 28 + pair.student_index * 114 + 41
                  const x2 = 610
                  const y2 = 28 + pair.reference_index * 114 + 41
                  const midX = (x1 + x2) / 2
                  const midY = (y1 + y2) / 2
                  const evalItem = getEntailmentEvaluation(pair)
                  const isHighlighted =
                    activeSelectionP5.matchId === pair.id ||
                    hoveredP5Id === pair.id
                  const showBadge =
                    effectiveP5FromPhase === "04"
                      ? p5AnimStage !== "STEP_0_ENTER"
                      : idx < p5RevealedMatchCount

                  const status = evalItem.status || "ENTAILS"
                  const confVal =
                    typeof evalItem.confidence === "number"
                      ? evalItem.confidence
                      : typeof pair.triple_score === "number"
                        ? pair.triple_score
                        : 1.0

                  return (
                    <div
                      key={`p5-badge-${pair.id || idx}`}
                      data-interactive="true"
                      style={{
                        left: `${midX}px`,
                        top: `${midY}px`,
                        transform: "translate(-50%, -50%)",
                        opacity: isPhase05 ? (showBadge ? 1 : 0) : 0,
                        pointerEvents: isPhase05 && showBadge ? "auto" : "none",
                        transition:
                          "opacity 280ms ease-out, transform 280ms ease-out",
                      }}
                      className="absolute z-30 pointer-events-auto"
                    >
                      <div
                        onMouseEnter={() => setHoveredP5Id(pair.id)}
                        onMouseLeave={() => setHoveredP5Id(null)}
                        className={`px-3 py-1 rounded-full text-[10.5px] font-mono font-bold tracking-tight shadow-2xs transition-all cursor-default border select-none ${
                          isHighlighted
                            ? "bg-[#3730a3] text-white border-indigo-900 scale-102 shadow-sm"
                            : "bg-[#faf8f4] text-indigo-950 border-[#dfd8c8] hover:border-indigo-500 hover:bg-indigo-50"
                        }`}
                      >
                        {status} · {confVal.toFixed(2)}
                      </div>
                    </div>
                  )
                })}

              {(isPhase05 ||
                (isExitingP4P5 && prevPhaseRef.current === "05")) && (
                <div
                  style={{
                    opacity:
                      isPhase05 &&
                      (p5AnimStage === "STEP_3_LABEL" ||
                        p5AnimStage === "STEP_4_CLASSIFICATION" ||
                        p5AnimStage === "STEP_5_SETTLED")
                        ? 1
                        : 0,
                    pointerEvents: isPhase05 ? "auto" : "none",
                    transition: "opacity 0.4s ease-out",
                  }}
                  className="absolute inset-x-0 pointer-events-none z-20"
                >
                  <div
                    style={{
                      left: "50px",
                      top: `${p5Section2Top}px`,
                      width: "900px",
                    }}
                    className="absolute flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-[11px] font-bold tracking-wider text-[#7a7266] uppercase">
                        Additional Information
                      </span>
                      <span className="text-[#a89e8f] text-[10px]">—</span>
                      <span className="text-[10.5px] text-[#8c8477] font-normal">
                        Unmatched student assertions evaluated for epistemic
                        validity
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-[#8c8477]">
                      {unmatchedStudentProps.length}{" "}
                      {unmatchedStudentProps.length === 1
                        ? "assertion"
                        : "assertions"}
                    </span>
                  </div>

                  {unmatchedStudentProps.length === 0 ? (
                    <div
                      style={{
                        left: "50px",
                        top: `${p5Section2Top + 24}px`,
                        width: "900px",
                      }}
                      className="absolute rounded-xl bg-[#faf8f4] border border-[#dfd8c8] p-4 text-center text-[12px] font-mono text-[#706b63]"
                    >
                      No unmatched student assertions — all student propositions
                      align to reference requirements.
                    </div>
                  ) : (
                    unmatchedStudentProps.map((prop, idx) => {
                      const uRowTop = p5Section2Top + 24 + idx * 114
                      const uEval = getUnmatchedEvaluation(prop)
                      const isSelected = selectedP5UnmatchedId === prop.id
                      const showClassification =
                        p5AnimStage === "STEP_4_CLASSIFICATION" ||
                        p5AnimStage === "STEP_5_SETTLED"

                      const cls = uEval.classification || "UNCERTAIN"
                      const clsBadgeStyle =
                        cls === "CORRECT_ADDITIONAL"
                          ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                          : cls === "INCORRECT"
                            ? "bg-rose-50 text-rose-800 border-rose-300"
                            : cls === "IRRELEVANT"
                              ? "bg-[#f4f0e8] text-[#706b63] border-[#dfd8c8]"
                              : "bg-amber-50 text-amber-800 border-amber-300"

                      const clsLabel =
                        cls === "CORRECT_ADDITIONAL"
                          ? "CORRECT ADDITIONAL"
                          : cls === "INCORRECT"
                            ? "INCORRECT"
                            : cls === "IRRELEVANT"
                              ? "IRRELEVANT"
                              : "UNCERTAIN"

                      const eff =
                        typeof uEval.score_effect === "number"
                          ? uEval.score_effect
                          : 0
                      const effLabel =
                        eff > 0
                          ? `+${eff.toFixed(2)}`
                          : eff < 0
                            ? eff.toFixed(2)
                            : "+0.00"

                      return (
                        <div key={`p5-unmatched-row-${prop.id}`}>
                          <div
                            style={{
                              left: "500px",
                              top: `${uRowTop + 41}px`,
                              transform: "translate(-50%, -50%)",
                              opacity: showClassification ? 1 : 0,
                              transition: "opacity 300ms ease-out",
                            }}
                            className="absolute z-20 pointer-events-none"
                          >
                            <span className="px-2.5 py-0.5 rounded-full text-[9px] font-mono font-semibold tracking-wider bg-[#f4f0e8] text-[#706b63] border border-[#dfd8c8] uppercase shadow-2xs">
                              ADDITIONAL INFO
                            </span>
                          </div>

                          <div
                            data-interactive="true"
                            onClick={() => handleSelectP5StudentCard(prop)}
                            onMouseEnter={() => setHoveredP5Id(prop.id)}
                            onMouseLeave={() => setHoveredP5Id(null)}
                            style={{
                              left: "610px",
                              top: `${uRowTop}px`,
                              width: "340px",
                              height: "82px",
                              opacity: showClassification ? 1 : 0,
                              transform: showClassification
                                ? "translateX(0)"
                                : "translateX(16px)",
                              transition:
                                "opacity 380ms ease-out, transform 380ms cubic-bezier(0.16, 1, 0.3, 1), border-color 0.2s, box-shadow 0.2s, background-color 0.2s",
                            }}
                            className={`absolute rounded-2xl p-3.5 flex flex-col justify-between cursor-pointer pointer-events-auto border ${
                              isSelected
                                ? "bg-[#faf8f4] border-2 border-indigo-700 shadow-md ring-2 ring-indigo-700/15"
                                : "bg-[#fdfcf9] border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs"
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2 mb-1.5 font-mono">
                              <span
                                className={`text-[9.5px] font-bold px-2 py-0.5 rounded border tracking-tight ${clsBadgeStyle}`}
                              >
                                {clsLabel}
                              </span>

                              <span className="text-[9.5px] font-semibold px-2 py-0.5 rounded bg-[#f7f4ed] text-[#706b63] border border-[#dfd8c8]">
                                Score effect: {effLabel}
                              </span>
                            </div>

                            <div
                              className="text-[12px] font-sans text-[#706b63] leading-snug truncate"
                              title={uEval.rationale}
                            >
                              {uEval.rationale}
                            </div>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              )}

              {isPhase05 && selectedP5Unmatched && (
                <div
                  data-interactive="true"
                  style={{
                    left: "610px",
                    top: `${
                      p5Section2Top +
                      24 +
                      (unmatchedStudentProps.findIndex(
                        (p) => p.id === selectedP5Unmatched.prop.id,
                      ) >= 0
                        ? unmatchedStudentProps.findIndex(
                            (p) => p.id === selectedP5Unmatched.prop.id,
                          )
                        : 0) *
                        114 +
                      88
                    }px`,
                  }}
                  className="absolute z-40 w-[310px] sm:w-[340px] bg-[#fdfcf9] border border-[#dfd8c8] rounded-2xl p-4 shadow-xl text-left pointer-events-auto"
                >
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#dfd8c8]">
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-[#7a7266] font-bold block">
                        ADDITIONAL INFORMATION
                      </span>
                      <span className="text-sm font-mono font-bold text-[#1e1c19]">
                        P{selectedP5Unmatched.prop.index + 1}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelectedP5UnmatchedId(null)}
                      className="w-6 h-6 flex items-center justify-center rounded-md text-[#706b63] hover:text-[#1e1c19] hover:bg-[#ede8dc] cursor-pointer text-xs font-mono font-bold"
                    >
                      &times;
                    </button>
                  </div>

                  <div className="space-y-2.5 text-[12px] font-mono">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase text-[#7a7266] font-semibold">
                        Classification
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                          selectedP5Unmatched.evaluation.classification ===
                          "CORRECT_ADDITIONAL"
                            ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                            : selectedP5Unmatched.evaluation.classification ===
                                "INCORRECT"
                              ? "bg-rose-50 text-rose-800 border-rose-300"
                              : selectedP5Unmatched.evaluation
                                    .classification === "IRRELEVANT"
                                ? "bg-[#f4f0e8] text-[#706b63] border-[#dfd8c8]"
                                : "bg-amber-50 text-amber-800 border-amber-300"
                        }`}
                      >
                        {selectedP5Unmatched.evaluation.classification}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase text-[#7a7266] font-semibold">
                        Score Effect
                      </span>
                      <span className="font-bold text-[#1e1c19]">
                        {selectedP5Unmatched.evaluation.score_effect > 0
                          ? `+${selectedP5Unmatched.evaluation.score_effect.toFixed(2)}`
                          : selectedP5Unmatched.evaluation.score_effect < 0
                            ? selectedP5Unmatched.evaluation.score_effect.toFixed(
                                2,
                              )
                            : "+0.00"}
                      </span>
                    </div>

                    {selectedP5Unmatched.evaluation.severity_level && (
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase text-[#7a7266] font-semibold">
                          Severity Level
                        </span>
                        <span className="text-[#1e1c19]">
                          {selectedP5Unmatched.evaluation.severity_level}
                        </span>
                      </div>
                    )}

                    <div className="pt-2 border-t border-[#dfd8c8]/80 text-[11px] font-sans text-[#706b63] leading-relaxed">
                      <span className="font-mono text-[10px] uppercase text-[#7a7266] font-semibold block mb-0.5">
                        Epistemic Rationale
                      </span>
                      <span>{selectedP5Unmatched.evaluation.rationale}</span>
                    </div>
                  </div>
                </div>
              )}

              {isPhase06 && (
                <div
                  style={{
                    position: "absolute",
                    left: `${Math.max(40, (contentWidth - 920) / 2)}px`,
                    top: "4px",
                    width: "920px",
                    opacity: isPhase06 ? 1 : 0,
                    pointerEvents: isPhase06 ? "auto" : "none",
                    transition: "opacity 0.4s ease-out",
                  }}
                  className="z-30 flex flex-col gap-1 pb-16 select-none"
                >
                  <div
                    style={{ height: "20px" }}
                    className="flex items-center justify-between pb-1 px-1"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono uppercase tracking-wider text-[#7a7266] font-bold">
                        GRADING MAP
                      </span>
                      <span className="text-[10px] font-mono text-[#706b63]">
                        ·
                      </span>
                      <span className="text-[11px] font-mono text-[#706b63]">
                        Attribution & Scoring Trace
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-[#7a7266]">
                      {phase06Spans.length} proposition
                      {phase06Spans.length === 1 ? "" : "s"} evaluated
                    </span>
                  </div>

                  <div
                    className="w-full bg-[#fdfcf9] border border-[#dfd8c8] rounded-2xl p-5 shadow-xs transition-all duration-500 mt-1"
                    style={{
                      opacity: p6AnimStage === "STEP_0_ENTER" ? 0.3 : 1,
                      transform:
                        p6AnimStage === "STEP_0_ENTER"
                          ? "translateY(8px)"
                          : "translateY(0)",
                      transition:
                        "all 0.4s cubic-bezier(0.45, 0.05, 0.15, 0.98)",
                    }}
                  >
                    <div className="text-[17px] font-sans leading-relaxed tracking-normal text-[#1e1c19] p-4 bg-[#faf8f4] border border-[#dfd8c8] rounded-xl select-text">
                      {renderedAnswerSegments.map((segment, idx) => {
                        if (!segment.isSpan) {
                          return (
                            <span
                              key={`seg-plain-${idx}`}
                              className="text-[#2b2723]"
                            >
                              {segment.text}
                            </span>
                          )
                        }

                        const span = segment.span
                        const isHovered = hoveredSpanId === span.id
                        const style = getSpanStyle(span.role, isHovered, false)

                        return (
                          <span
                            key={`seg-span-${span.id}-${idx}`}
                            data-interactive="true"
                            onMouseEnter={() => setHoveredSpanId(span.id)}
                            onMouseLeave={() =>
                              setHoveredSpanId((prev) =>
                                prev === span.id ? null : prev,
                              )
                            }
                            className={`relative inline mx-0.5 px-1.5 py-0.5 rounded transition-all cursor-default ${
                              style.bg
                            } ${style.borderStyle} ${style.border} ${style.text}`}
                          >
                            <span className="font-mono text-[10px] font-bold opacity-60 mr-1 select-none pointer-events-none">
                              P{span.index + 1}
                            </span>
                            <span>{segment.text}</span>
                          </span>
                        )
                      })}
                    </div>

                    <div className="flex flex-wrap items-center gap-3.5 text-[11px] font-mono text-[#706b63] pt-3 mt-1">
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-indigo-600 inline-block" />
                        Core
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-600 inline-block" />
                        Correct additional
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#8a8070] inline-block" />
                        Irrelevant
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-rose-600 inline-block" />
                        Incorrect
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-amber-600 inline-block" />
                        Uncertain
                      </span>
                    </div>
                  </div>

                  <div
                    className="w-full bg-[#fdfcf9] border border-[#dfd8c8] rounded-2xl p-5 shadow-xs mt-3"
                    style={{
                      opacity: p6ScoringVisible ? 1 : 0,
                      transform: p6ScoringVisible
                        ? "translateY(0)"
                        : "translateY(16px)",
                      transition:
                        "opacity 0.55s cubic-bezier(0.16, 1, 0.3, 1), transform 0.55s cubic-bezier(0.16, 1, 0.3, 1)",
                    }}
                  >
                    <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#dfd8c8]">
                      <div className="flex items-center gap-2">
                        <span className="text-[10.5px] font-mono uppercase tracking-wider text-[#7a7266] font-bold">
                          SCORING SYNTHESIS
                        </span>
                      </div>
                      <span className="text-[10.5px] font-mono text-[#7a7266]">
                        Proposition-level additive grading equation
                      </span>
                    </div>

                    <div className="flex items-center justify-between w-full text-xs font-mono">
                      <div className="inline-flex items-baseline gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8]">
                        <span className="text-[10px] uppercase text-[#7a7266] font-semibold">
                          Core Score
                        </span>
                        <span className="font-bold text-[#1e1c19]">
                          {baseGrade}
                        </span>
                        <span className="text-[10px] text-[#7a7266]">
                          / {Number(maxPoints).toFixed(1)}
                        </span>
                      </div>

                      <span className="text-[#7a7266] font-bold text-sm select-none px-1">
                        +
                      </span>

                      <div className="inline-flex items-baseline gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8]">
                        <span className="text-[10px] uppercase text-[#7a7266] font-semibold">
                          Additional
                        </span>
                        <span className="font-bold text-emerald-700">
                          +{positiveAdj}
                        </span>
                      </div>

                      <span className="text-[#7a7266] font-bold text-sm select-none px-1">
                        −
                      </span>

                      <div className="inline-flex items-baseline gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#f7f4ed] border border-[#dfd8c8]">
                        <span className="text-[10px] uppercase text-[#7a7266] font-semibold">
                          Penalties
                        </span>
                        <span className="font-bold text-rose-700">
                          {Math.abs(Number(negativeAdj)).toFixed(2)}
                        </span>
                      </div>

                      <span className="text-[#7a7266] font-bold text-sm select-none px-1">
                        =
                      </span>

                      <div
                        className="inline-flex items-baseline gap-2 px-4 py-1.5 rounded-lg bg-gradient-to-r from-indigo-950 via-[#1e1c19] to-indigo-900 text-white border border-indigo-700/60 shadow-xs transition-all duration-500"
                        style={{
                          transform:
                            p6AnimStage === "STEP_4_FINAL_GRADE" ||
                            p6AnimStage === "STEP_5_SETTLED"
                              ? "scale(1)"
                              : "scale(0.97)",
                        }}
                      >
                        <span className="text-[10px] uppercase tracking-wider text-indigo-200 font-bold">
                          Final Grade
                        </span>
                        <span className="text-base font-extrabold text-white tracking-tight">
                          {finalGrade}
                        </span>
                        <span className="text-[10.5px] text-indigo-300">
                          / {Number(maxPoints).toFixed(1)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div
                style={{
                  opacity: isPhase01 ? 0 : 1,
                  transition: isPhase01 ? "opacity 0.22s ease-out" : "none",
                  pointerEvents: isPhase01 ? "none" : "auto",
                }}
                className="absolute inset-0 pointer-events-none z-20"
              >
                {(isPhase02 && stage !== "REVERSE_MOVE") ||
                stage === "PHASE_02" ? (
                  !isPhase01 &&
                  nodes.map((node) =>
                    renderNodeCard({
                      key: `node-${node.id}`,
                      node,
                      x: node.x,
                      y: node.y,
                      opacity: p2FadeIn ? 1 : 0,
                      transition: "opacity 0.4s ease-out",
                      isSelected: selectedNode?.id === node.id,
                      onClick: () => onSelectNode && onSelectNode(node),
                    }),
                  )
                ) : (
                  <>
                    {(stage === "STEP_1_FADE" || stage === "REVERSE_MOVE") &&
                      unusedNodes.map((node) =>
                        renderNodeCard({
                          key: `unused-${node.id}`,
                          node,
                          x: node.x,
                          y: node.y,
                          opacity: stage === "REVERSE_MOVE" ? 1 : 0,
                          transition: "opacity 0.5s ease-out",
                          isSelected: false,
                        }),
                      )}

                    {laneCardItems.map((item) => {
                      const curX =
                        stage === "STEP_1_FADE" || stage === "REVERSE_MOVE"
                          ? item.node.x
                          : item.x
                      const curY =
                        stage === "STEP_1_FADE" || stage === "REVERSE_MOVE"
                          ? item.node.y
                          : item.y

                      const isOriginal = !item.isDuplicate

                      const cardOpacity =
                        isPhase01 || isPhase04 || isPhase05 || isPhase06
                          ? 0
                          : stage === "STEP_1_FADE" || stage === "REVERSE_MOVE"
                            ? isOriginal
                              ? 1
                              : 0
                            : 1

                      return renderNodeCard({
                        key: item.key,
                        node: item.node,
                        x: curX,
                        y: curY,
                        opacity: cardOpacity,
                        transition:
                          isPhase01 || isPhase04 || isPhase05 || isPhase06
                            ? "opacity 0.22s ease-out"
                            : stage === "STEP_1_FADE"
                              ? "none"
                              : "left 1.1s cubic-bezier(0.45, 0.05, 0.15, 0.98), top 1.1s cubic-bezier(0.45, 0.05, 0.15, 0.98), opacity 0.7s cubic-bezier(0.45, 0.05, 0.15, 0.98)",
                        isSelected: false,
                        onClick: () => setSelectedPropId(item.propId),
                      })
                    })}
                  </>
                )}
              </div>
            </div>
          </InfiniteCanvas>
        </div>

        <div
          style={{
            transition: "all 0.7s cubic-bezier(0.45, 0.05, 0.15, 0.98)",
          }}
          className={`h-full flex flex-col overflow-hidden shrink-0 ${
            isPhase02 ? "w-80 opacity-100" : "w-0 opacity-0 pointer-events-none"
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
  )
}
