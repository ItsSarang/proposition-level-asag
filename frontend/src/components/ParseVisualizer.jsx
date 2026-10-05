export default function ParseVisualizer({
  nodes = [],
  edges = [],
  maxX,
  maxY,
  selectedNode,
  onSelectNode,
}) {
  const canvasWidth = Math.max(maxX || 800, 800);
  const canvasHeight = Math.max(maxY || 500, 500);

  const activePathEdgeIds = new Set();
  if (selectedNode) {
    let currNodeId = selectedNode.id;
    const visited = new Set();
    while (currNodeId && !visited.has(currNodeId)) {
      visited.add(currNodeId);
      const incomingEdge = edges.find((e) => e.toId === currNodeId);
      if (incomingEdge) {
        activePathEdgeIds.add(incomingEdge.id);
        currNodeId = incomingEdge.fromId;
      } else {
        break;
      }
    }
  }

  return (
    <div
      style={{ width: `${canvasWidth}px`, height: `${canvasHeight}px` }}
      className="relative p-6"
    >
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
        <defs>
          <marker
            id="arrowhead-primary"
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
            id="arrowhead-default"
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

        <g className="edge-lines">
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
                strokeDasharray="none"
                markerEnd={
                  isPathActive
                    ? 'url(#arrowhead-primary)'
                    : 'url(#arrowhead-default)'
                }
              />
            );
          })}
        </g>

        <g className="edge-labels">
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

      <div className="relative z-10">
        {nodes.map((node) => {
          const isSelected = selectedNode?.id === node.id;
          const isRoot = (node.dep || '').toLowerCase() === 'root' || node.isRoot;

          return (
            <div
              key={node.id}
              data-interactive="true"
              onClick={() => onSelectNode && onSelectNode(node)}
              style={{
                left: `${node.x}px`,
                top: `${node.y}px`,
                width: `${node.width || 88}px`,
                height: `${node.height || 50}px`,
                position: 'absolute',
              }}
              className={`flex flex-col justify-between p-2 rounded-xl transition-all cursor-pointer select-none ${
                isRoot
                  ? isSelected
                    ? 'bg-[#1e1c19] border-2 border-indigo-500 text-[#f7f4ed] shadow-md z-20'
                    : 'bg-[#1e1c19] border-2 border-[#1e1c19] text-[#f7f4ed] shadow-xs hover:border-[#343029] z-10'
                  : isSelected
                  ? 'bg-[#fdfcf9] border-2 border-indigo-700 shadow-sm z-20'
                  : 'bg-[#fdfcf9] border border-[#dfd8c8] hover:border-indigo-400 hover:shadow-xs z-10'
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
        })}
      </div>
    </div>
  );
}
