function getRoleMetadata(dep, pos) {
  const d = (dep || '').toLowerCase();
  if (d === 'root') {
    return {
      label: 'MAIN ACTION',
      code: 'ROOT',
      bg: 'bg-slate-900',
      text: 'text-white',
      border: 'border-slate-800',
    };
  }
  if (d === 'nsubj' || d === 'csubj') {
    return {
      label: 'SUBJECT',
      code: d,
      bg: 'bg-indigo-50',
      text: 'text-indigo-700',
      border: 'border-indigo-200',
    };
  }
  if (d === 'dobj' || d === 'obj' || d === 'iobj') {
    return {
      label: 'OBJECT',
      code: d,
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      border: 'border-blue-200',
    };
  }
  if (d === 'xcomp' || d === 'ccomp') {
    return {
      label: 'LINKED ACTION',
      code: d,
      bg: 'bg-purple-50',
      text: 'text-purple-700',
      border: 'border-purple-200',
    };
  }
  if (d === 'pobj') {
    return {
      label: 'TARGET OBJECT',
      code: d,
      bg: 'bg-amber-50',
      text: 'text-amber-800',
      border: 'border-amber-200',
    };
  }
  if (d === 'advmod') {
    return {
      label: 'MODIFIER / HOW',
      code: d,
      bg: 'bg-emerald-50',
      text: 'text-emerald-700',
      border: 'border-emerald-200',
    };
  }
  if (d === 'amod') {
    return {
      label: 'DESCRIPTOR',
      code: d,
      bg: 'bg-teal-50',
      text: 'text-teal-700',
      border: 'border-teal-200',
    };
  }
  if (d === 'det') {
    return {
      label: 'DETERMINER',
      code: d,
      bg: 'bg-stone-50',
      text: 'text-stone-700',
      border: 'border-stone-200',
    };
  }
  if (pos && pos.startsWith('V')) {
    return {
      label: 'PREDICATE',
      code: d,
      bg: 'bg-purple-50',
      text: 'text-purple-700',
      border: 'border-purple-200',
    };
  }
  if (pos && pos.startsWith('N')) {
    return {
      label: 'NOMINAL',
      code: d,
      bg: 'bg-indigo-50',
      text: 'text-indigo-700',
      border: 'border-indigo-200',
    };
  }
  return {
    label: 'DEPENDENT',
    code: d || 'dep',
    bg: 'bg-slate-50',
    text: 'text-slate-600',
    border: 'border-slate-200',
  };
}

function getRoleDescription(dep, text, headText) {
  const d = (dep || '').toLowerCase();
  const head = headText || 'ROOT';
  if (d === 'amod') return `Modifies "${head}" to specify the type of ${head}.`;
  if (d === 'nsubj') return `Nominal subject performing or expressing the action of "${head}".`;
  if (d === 'dobj' || d === 'obj') return `Direct grammatical object receiving the action of "${head}".`;
  if (d === 'xcomp') return `Open clausal complement verb subordinate to governor "${head}".`;
  if (d === 'advmod') return `Adverbial modifier characterizing the semantic manner of "${head}".`;
  if (d === 'pobj') return `Object of preposition attached to governor "${head}".`;
  if (d === 'det') return `Determiner specifying the grammatical reference or scope of "${head}".`;
  return `Syntactic dependent attached to governor "${head}" with relation "${dep}".`;
}

function getNodeMeaning(dep, text, headText) {
  const d = (dep || '').toLowerCase();
  const head = headText || 'ROOT';
  if (d === 'amod') return `Modifies "${head}" to specify the type of ${head}.`;
  if (d === 'compound') return `Combines with "${head}" to form the unified concept "${text} ${head}".`;
  if (d === 'nsubj' || d === 'csubj') return `Subject entity performing or instantiating the action denoted by "${head}".`;
  if (d === 'dobj' || d === 'obj') return `Direct object entity receiving or targeted by the action of "${head}".`;
  if (d === 'root') return `Primary predicate establishing the core clausal assertion of the proposition.`;
  if (d === 'advmod') return `Modifies "${head}" to characterize degree, manner, or logical condition.`;
  if (d === 'pobj') return `Object of preposition attached to governor "${head}".`;
  if (d === 'prep') return `Relational preposition linking governor "${head}" to its contextual object.`;
  if (d === 'neg') return `Inverts the truth condition and polarity of predicate "${head}".`;
  if (d === 'det') return `Determiner introducing and scoping the nominal entity "${head}".`;
  return `Syntactic dependent attached to governor "${head}" with relation "${dep}".`;
}

function getNodeAsagRole(dep, pos) {
  const d = (dep || '').toLowerCase();
  if (d === 'amod') return 'Descriptor';
  if (d === 'compound') return 'Compound Qualifier';
  if (d === 'nsubj' || d === 'csubj') return 'Subject Entity';
  if (d === 'dobj' || d === 'obj' || d === 'iobj') return 'Object Entity';
  if (d === 'root') return 'Root Predicate Action';
  if (d === 'advmod') return 'Modifier / Manner';
  if (d === 'prep') return 'Relational Link';
  if (d === 'pobj') return 'Prepositional Object';
  if (d === 'neg') return 'Polarity Inversion';
  if (d === 'xcomp' || d === 'ccomp') return 'Subordinate Predicate';
  if (d === 'det') return 'Determiner / Scope';
  if (pos && pos.startsWith('V')) return 'Predicate Action';
  if (pos && pos.startsWith('N')) return 'Nominal Entity';
  return 'Syntactic Dependent';
}

function getNodePartOf(node, allNodes) {
  const d = (node.dep || '').toLowerCase();
  const head = allNodes.find((n) => n.text === node.headText || (node.headIndex !== undefined && n.globalIndex === node.headIndex));

  if (d === 'amod' || d === 'compound') {
    return head ? `${node.text} ${head.text}` : node.text;
  }
  if (head && (d === 'pobj' || d === 'prep')) {
    return `${head.text} ${node.text}`;
  }
  if (d === 'neg' && head) {
    return `${node.text} ${head.text}`;
  }

  const modifiers = allNodes.filter(
    (n) => (n.headText === node.text || n.headIndex === node.globalIndex) && ['amod', 'compound'].includes((n.dep || '').toLowerCase())
  );
  if (modifiers.length > 0) {
    const phrase = [...modifiers, node].sort((a, b) => (a.tokenIndex ?? 0) - (b.tokenIndex ?? 0));
    return phrase.map((t) => t.text).join(' ');
  }

  if (node.isRoot || d === 'root') {
    const subj = allNodes.find((n) => (n.dep || '').toLowerCase() === 'nsubj' && (n.headText === node.text || n.headIndex === node.globalIndex));
    const obj = allNodes.find((n) => ['dobj', 'obj'].includes((n.dep || '').toLowerCase()) && (n.headText === node.text || n.headIndex === node.globalIndex));
    if (subj && obj) return `${subj.text} ${node.text} ${obj.text}`;
    if (subj) return `${subj.text} ${node.text}`;
    if (obj) return `${node.text} ${obj.text}`;
  }

  return node.text;
}

function layoutHierarchicalGraph(rawNodes, rawEdges = []) {
  if (!rawNodes || rawNodes.length === 0) return { nodes: [], edges: [], maxX: 1000, maxY: 600 };

  const NODE_HEIGHT = 50;
  const HORIZONTAL_GAP = 32;
  const VERTICAL_GAP = 140;

  const nodeMap = new Map();
  const sortedRaw = [...rawNodes].sort((a, b) => (a.tokenIndex ?? 0) - (b.tokenIndex ?? 0));
  sortedRaw.forEach((n, idx) => {
    const dynamicWidth = Math.max(88, Math.round(n.text.length * 9.5 + 40));
    nodeMap.set(n.id, {
      ...n,
      orderIndex: idx,
      width: dynamicWidth,
      height: NODE_HEIGHT,
    });
  });

  const childrenMap = new Map();
  const parentMap = new Map();
  sortedRaw.forEach((n) => {
    childrenMap.set(n.id, []);
  });

  rawEdges.forEach((edge) => {
    if (nodeMap.has(edge.fromId) && nodeMap.has(edge.toId)) {
      const currentChildren = childrenMap.get(edge.fromId);
      if (!currentChildren.includes(edge.toId)) {
        currentChildren.push(edge.toId);
      }
      parentMap.set(edge.toId, edge.fromId);
    }
  });

  for (const [pId, cIds] of childrenMap.entries()) {
    cIds.sort((a, b) => {
      const nodeA = nodeMap.get(a);
      const nodeB = nodeMap.get(b);
      return (nodeA?.tokenIndex ?? 0) - (nodeB?.tokenIndex ?? 0);
    });
  }

  let rootNodes = sortedRaw.filter(
    (n) => n.isRoot || (n.dep || '').toLowerCase() === 'root'
  );
  if (rootNodes.length === 0) {
    rootNodes = sortedRaw.filter((n) => !parentMap.has(n.id));
  }
  if (rootNodes.length === 0) {
    rootNodes = [sortedRaw[0]];
  }

  const subtreeWidths = new Map();
  const calcVisited = new Set();

  function calculateSubtreeWidth(nodeId) {
    calcVisited.add(nodeId);
    const node = nodeMap.get(nodeId);
    const selfWidth = node?.width || 88;
    const validChildren = (childrenMap.get(nodeId) || []).filter(
      (cId) => !calcVisited.has(cId) && nodeMap.has(cId)
    );

    if (validChildren.length === 0) {
      subtreeWidths.set(nodeId, selfWidth);
      return selfWidth;
    }

    let childrenTotalWidth = 0;
    validChildren.forEach((cId, idx) => {
      const w = calculateSubtreeWidth(cId);
      childrenTotalWidth += w;
      if (idx < validChildren.length - 1) {
        childrenTotalWidth += HORIZONTAL_GAP;
      }
    });

    const finalWidth = Math.max(selfWidth, childrenTotalWidth);
    subtreeWidths.set(nodeId, finalWidth);
    return finalWidth;
  }

  rootNodes.forEach((r) => calculateSubtreeWidth(r.id));
  sortedRaw.forEach((n) => {
    if (!calcVisited.has(n.id)) {
      calculateSubtreeWidth(n.id);
      rootNodes.push(n);
    }
  });

  const posVisited = new Set();
  const depthNodes = new Map();

  function positionNode(nodeId, slotLeft, depth) {
    posVisited.add(nodeId);
    const node = nodeMap.get(nodeId);
    node.depth = depth;
    node.y = Math.round(depth * VERTICAL_GAP + 50);

    if (!depthNodes.has(depth)) {
      depthNodes.set(depth, []);
    }
    depthNodes.get(depth).push(node);

    const slotWidth = subtreeWidths.get(nodeId) || node.width;
    const validChildren = (childrenMap.get(nodeId) || []).filter(
      (cId) => !posVisited.has(cId) && nodeMap.has(cId)
    );

    if (validChildren.length === 0) {
      node.x = Math.round(slotLeft + (slotWidth - node.width) / 2);
      return;
    }

    let childrenSpan = 0;
    validChildren.forEach((cId, idx) => {
      childrenSpan += subtreeWidths.get(cId) || nodeMap.get(cId)?.width || 88;
      if (idx < validChildren.length - 1) {
        childrenSpan += HORIZONTAL_GAP;
      }
    });

    let childSlotLeft = slotLeft;
    if (slotWidth > childrenSpan) {
      childSlotLeft += (slotWidth - childrenSpan) / 2;
    }

    validChildren.forEach((cId) => {
      const cWidth = subtreeWidths.get(cId) || nodeMap.get(cId)?.width || 88;
      positionNode(cId, childSlotLeft, depth + 1);
      childSlotLeft += cWidth + HORIZONTAL_GAP;
    });

    const firstChild = nodeMap.get(validChildren[0]);
    const lastChild = nodeMap.get(validChildren[validChildren.length - 1]);
    if (firstChild && lastChild) {
      const childrenCenter = (firstChild.x + firstChild.width / 2 + lastChild.x + lastChild.width / 2) / 2;
      node.x = Math.round(childrenCenter - node.width / 2);
    } else {
      node.x = Math.round(slotLeft + (slotWidth - node.width) / 2);
    }
  }

  let currentForestLeft = 60;
  rootNodes.forEach((root) => {
    const rootWidth = subtreeWidths.get(root.id) || (nodeMap.get(root.id)?.width || 88);
    positionNode(root.id, currentForestLeft, 0);
    currentForestLeft += rootWidth + HORIZONTAL_GAP * 2;
  });

  const maxDepth = Math.max(...Array.from(depthNodes.keys()), 0);
  for (let d = 0; d <= maxDepth; d++) {
    const nodesAtDepth = depthNodes.get(d) || [];
    nodesAtDepth.sort((a, b) => a.x - b.x);

    for (let i = 1; i < nodesAtDepth.length; i++) {
      const prev = nodesAtDepth[i - 1];
      const curr = nodesAtDepth[i];
      const minRequiredX = prev.x + prev.width + HORIZONTAL_GAP;

      if (curr.x < minRequiredX) {
        const shift = minRequiredX - curr.x;
        const shiftQueue = [curr.id];
        const shifted = new Set();

        while (shiftQueue.length > 0) {
          const shiftId = shiftQueue.shift();
          if (shifted.has(shiftId)) continue;
          shifted.add(shiftId);

          const toShiftNode = nodeMap.get(shiftId);
          if (toShiftNode) {
            toShiftNode.x += shift;
            const children = childrenMap.get(shiftId) || [];
            children.forEach((cId) => shiftQueue.push(cId));
          }
        }
      }
    }
  }

  const allPositioned = Array.from(nodeMap.values());
  const minX = Math.min(...allPositioned.map((n) => n.x));
  if (minX < 60) {
    const shift = 60 - minX;
    allPositioned.forEach((n) => {
      n.x += shift;
    });
  }

  const edgesBySource = new Map();
  rawEdges.forEach((edge) => {
    if (nodeMap.has(edge.fromId) && nodeMap.has(edge.toId)) {
      if (!edgesBySource.has(edge.fromId)) {
        edgesBySource.set(edge.fromId, []);
      }
      edgesBySource.get(edge.fromId).push(edge);
    }
  });

  const edges = [];
  for (const [sourceId, sourceEdges] of edgesBySource.entries()) {
    const source = nodeMap.get(sourceId);

    sourceEdges.sort((a, b) => {
      const targetA = nodeMap.get(a.toId);
      const targetB = nodeMap.get(b.toId);
      return (targetA?.x ?? 0) - (targetB?.x ?? 0);
    });

    const N = sourceEdges.length;
    const PADDING = 12;
    const sourceW = source.width || 88;
    const usableWidth = Math.max(20, sourceW - 2 * PADDING);

    sourceEdges.forEach((edge, idx) => {
      const target = nodeMap.get(edge.toId);
      if (!target) return;

      const targetW = target.width || 88;
      const fromX =
        N === 1
          ? source.x + Math.round(sourceW / 2)
          : source.x + PADDING + Math.round((idx + 0.5) * (usableWidth / N));
      const fromY = source.y + NODE_HEIGHT;

      const toX = target.x + Math.round(targetW / 2);
      const toY = target.y - 7;

      const midX = Math.round((fromX + toX) / 2);
      const midY = Math.round((fromY + toY) / 2);

      edges.push({
        id: edge.id,
        fromId: source.id,
        toId: target.id,
        label: edge.label,
        fromX,
        fromY,
        toX,
        toY,
        midX,
        midY,
      });
    });
  }

  const maxNodeX = allPositioned.length > 0 ? Math.max(...allPositioned.map((n) => n.x + n.width)) : 600;
  const maxNodeY = allPositioned.length > 0 ? Math.max(...allPositioned.map((n) => n.y + NODE_HEIGHT)) : 400;
  const maxX = Math.max(maxNodeX + 60, 600);
  const maxY = Math.max(maxNodeY + 60, 360);

  return { nodes: allPositioned, edges, maxX, maxY };
}

export function buildParseGraph(
  rawInput,
  apiParseData,
  targetMode = 'student',
  activeSentenceIndex = 0
) {
  const targetText = (
    targetMode === 'reference'
      ? rawInput?.referenceAnswer || ''
      : rawInput?.studentAnswer || ''
  ).trim();

  const tokenList =
    targetMode === 'reference'
      ? apiParseData?.phase_02_parse?.reference_tokens
      : apiParseData?.phase_02_parse?.student_tokens;

  const rawDependencies =
    targetMode === 'reference'
      ? apiParseData?.phase_02_parse?.reference_dependencies
      : apiParseData?.phase_02_parse?.student_dependencies;

  const sentenceCount =
    targetMode === 'reference'
      ? (apiParseData?.phase_02_parse?.reference_sentence_count || 1)
      : (apiParseData?.phase_02_parse?.student_sentence_count || 1);

  if (!tokenList || tokenList.length === 0) {
    return {
      nodes: [],
      edges: [],
      textTokens: [],
      targetText,
      targetMode,
      sentenceCount: 0,
      activeSentenceIndex: 0,
      isOffline: !apiParseData,
    };
  }

  let activeTokens = tokenList;
  if (sentenceCount > 1 && activeSentenceIndex >= 0) {
    const sentTokens = tokenList.filter((t) => t.sentence_index === activeSentenceIndex);
    if (sentTokens.length > 0) activeTokens = sentTokens;
  }

  const minorDeps = ['punct'];
  const coreFiltered = activeTokens.filter((t) => {
    const d = (t.dep || '').toLowerCase();
    return !minorDeps.includes(d) || t.is_root || d === 'root';
  });
  if (coreFiltered.length >= 2) {
    activeTokens = coreFiltered;
  }

  const tokenByGlobalIdx = new Map();
  activeTokens.forEach((t) => {
    const gIdx = t.global_index !== undefined ? t.global_index : t.token_index;
    tokenByGlobalIdx.set(gIdx, t);
  });

  const rawNodes = activeTokens.map((t) => ({
    id: t.id,
    globalIndex: t.global_index !== undefined ? t.global_index : t.token_index,
    tokenIndex: t.token_index,
    sentenceIndex: t.sentence_index,
    text: t.text,
    lemma: t.lemma || t.text.toLowerCase(),
    pos: t.pos || 'NN',
    dep: t.dep || 'dep',
    headText: t.head_text || 'ROOT',
    headIndex: t.head_index,
    charStart: t.char_start,
    charEnd: t.char_end,
    isRoot: Boolean(t.is_root || (t.dep || '').toLowerCase() === 'root'),
  }));

  const rawEdges = [];
  (rawDependencies || []).forEach((d) => {
    if (tokenByGlobalIdx.has(d.target)) {
      const targetTok = tokenByGlobalIdx.get(d.target);
      const sourceTok = tokenByGlobalIdx.get(d.source);

      if (sourceTok && targetTok && sourceTok.id !== targetTok.id) {
        rawEdges.push({
          id: d.id || `edge-${sourceTok.id}-${targetTok.id}`,
          fromId: sourceTok.id,
          toId: targetTok.id,
          label: d.label || targetTok.dep || 'dep',
        });
      }
    }
  });

  const { nodes: positionedNodes, edges, maxX, maxY } = layoutHierarchicalGraph(rawNodes, rawEdges);

  const nodes = positionedNodes.map((n) => {
    const roleMeta = getRoleMetadata(n.dep, n.pos);
    const description = getRoleDescription(n.dep, n.text, n.headText);
    const meaning = getNodeMeaning(n.dep, n.text, n.headText);
    const asagRole = getNodeAsagRole(n.dep, n.pos);
    const partOf = getNodePartOf(n, positionedNodes);
    const pathTrace = `${n.dep}(${n.headText || 'ROOT'}, ${n.text})`;

    return {
      ...n,
      role: roleMeta.label,
      roleMeta,
      description,
      meaning,
      asagRole,
      partOf,
      pathTrace,
    };
  });

  const sortedTokens = [...rawNodes].sort((a, b) => (a.charStart ?? 0) - (b.charStart ?? 0));
  const textTokens = [];

  if (sortedTokens.length > 0 && sortedTokens[0].charStart !== undefined) {
    let cursor = 0;

    sortedTokens.forEach((tok, idx) => {
      if (tok.charStart > cursor) {
        textTokens.push({
          id: `gap-${idx}`,
          raw: targetText.substring(cursor, tok.charStart),
          isWord: false,
          nodeId: null,
          dep: null,
        });
      }

      textTokens.push({
        id: `tok-${tok.id}`,
        raw: targetText.substring(tok.charStart, tok.charEnd) || tok.text,
        isWord: true,
        nodeId: tok.id,
        dep: tok.dep,
      });

      cursor = tok.charEnd;
    });

    if (cursor < targetText.length) {
      textTokens.push({
        id: `gap-end`,
        raw: targetText.substring(cursor, targetText.length),
        isWord: false,
        nodeId: null,
        dep: null,
      });
    }
  } else {
    const words = targetText.split(/(\s+)/).filter(Boolean);
    words.forEach((chunk, idx) => {
      const cleanWord = chunk.replace(/[.,!?;:()]/g, '').trim().toLowerCase();
      const matchedNode = nodes.find(
        (n) => n.text.toLowerCase() === cleanWord || cleanWord.includes(n.text.toLowerCase())
      );
      textTokens.push({
        id: `tok-${idx}`,
        raw: chunk,
        isWord: /\S/.test(chunk),
        nodeId: matchedNode ? matchedNode.id : null,
        dep: matchedNode ? matchedNode.dep : null,
      });
    });
  }

  return {
    nodes,
    edges,
    maxX,
    maxY,
    textTokens,
    targetText,
    targetMode,
    sentenceCount,
    activeSentenceIndex,
    isOffline: false,
  };
}
