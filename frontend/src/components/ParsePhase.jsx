import InfiniteCanvas from './InfiniteCanvas';
import ParseVisualizer from './ParseVisualizer';
import DetailPanel from './DetailPanel';
import CanvasControls from './CanvasControls';
import AnswerBar from './AnswerBar';

export default function ParsePhase({
  parseData,
  parseMode,
  onSwitchParseMode,
  activeSentenceIndex,
  onSwitchSentence,
  selectedNode,
  onSelectNode,
  onSelectNodeIndex,
  zoom,
  onZoomChange,
  showGrid,
  fitTrigger,
  onResetFit,
}) {
  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
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

      <div className="flex-1 flex min-h-0 relative w-full overflow-hidden">
        <div className="relative flex-1 h-full min-w-0 overflow-hidden">
          <CanvasControls
            zoom={zoom}
            onZoomIn={() => onZoomChange((z) => Math.min(z + 0.1, 2.2))}
            onZoomOut={() => onZoomChange((z) => Math.max(z - 0.1, 0.45))}
            onResetFit={onResetFit}
          />

          <div className="absolute bottom-5 right-6 z-20 pointer-events-none">
            <div className="h-9 px-3.5 flex items-center bg-[#f4f0e8]/95 backdrop-blur-md rounded-xl border border-[#dfd8c8] shadow-xs text-[#706b63] font-mono text-[11.5px] font-medium pointer-events-auto">
              {parseData.nodes.length} Constituent Nodes
            </div>
          </div>

          <InfiniteCanvas
            zoom={zoom}
            onZoomChange={onZoomChange}
            showGrid={showGrid}
            contentWidth={parseData.maxX}
            contentHeight={parseData.maxY}
            fitTrigger={fitTrigger}
          >
            <ParseVisualizer
              nodes={parseData.nodes}
              edges={parseData.edges}
              maxX={parseData.maxX}
              maxY={parseData.maxY}
              selectedNode={selectedNode}
              onSelectNode={onSelectNode}
            />
          </InfiniteCanvas>
        </div>

        <DetailPanel
          selectedNode={selectedNode}
          nodes={parseData.nodes}
          onSelectNodeIndex={onSelectNodeIndex}
        />
      </div>
    </div>
  );
}
