import SyntacticPropositionCanvasPhase from '../components/SyntacticPropositionCanvasPhase';
import AlignmentPhase from '../components/AlignmentPhase';
import AssessmentPhase from '../components/AssessmentPhase';
import ScoringPhase from '../components/ScoringPhase';
import BottomHUD from '../components/BottomHUD';

export default function WorkbenchPage({
  activePhase,
  onPhaseChange,
  loading,
  statusMessage,
  onAnalyze,
  apiResult,
  analysisInput,
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
  onRetryConnection,
}) {
  return (
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden relative">
      {(activePhase === '01' || activePhase === '02' || activePhase === '03') && (
        <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
          {loading && activePhase !== '01' ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-10 h-10 border-3 border-indigo-700 border-t-transparent rounded-full animate-spin mb-4" />
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                {activePhase === '02'
                  ? 'Analyzing Syntactic Dependencies'
                  : 'Extracting Clausal Propositions'}
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md">
                {activePhase === '02'
                  ? 'V5 model is parsing clausal triples and building Universal Dependencies trees...'
                  : 'Decomposing relational triples, clausal arguments, and polarity structures...'}
              </p>
            </div>
          ) : (parseData.isOffline || !apiResult) && activePhase !== '01' ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-12 h-12 rounded-full bg-[#f4f0e8] border border-[#dfd8c8] flex items-center justify-center text-[#8c8477] mb-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                {parseData.isOffline ? 'ASAG Engine Offline' : 'No Analysis Data Available'}
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md mb-4 leading-relaxed">
                Run analysis on Phase 01 to parse syntactic trees and extract clausal propositions.
              </p>
              <button
                type="button"
                onClick={onRetryConnection}
                className="px-4 py-2 bg-[#1e1c19] hover:bg-[#343029] text-[#f7f4ed] rounded-lg text-xs font-mono font-medium transition-all cursor-pointer shadow-xs active:scale-95"
              >
                Retry Connection
              </button>
            </div>
          ) : (
            <SyntacticPropositionCanvasPhase
              activePhase={activePhase}
              parseData={parseData}
              parseMode={parseMode}
              onSwitchParseMode={onSwitchParseMode}
              activeSentenceIndex={activeSentenceIndex}
              onSwitchSentence={onSwitchSentence}
              selectedNode={selectedNode}
              onSelectNode={onSelectNode}
              onSelectNodeIndex={onSelectNodeIndex}
              relationsData={apiResult?.phase_03_relations}
              studentAnswer={analysisInput?.studentAnswer || ''}
              referenceAnswer={analysisInput?.referenceAnswer || ''}
              zoom={zoom}
              onZoomChange={onZoomChange}
              showGrid={showGrid}
              fitTrigger={fitTrigger}
              onResetFit={onResetFit}
              onAnalyze={onAnalyze}
              loading={loading}
              statusMessage={statusMessage}
              analysisInput={analysisInput}
            />
          )}
        </div>
      )}

      {activePhase === '04' && (
        <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-10 h-10 border-3 border-indigo-700 border-t-transparent rounded-full animate-spin mb-4" />
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                Aligning Clausal Propositions
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md">
                Computing bipartite lexical and semantic proposition alignments...
              </p>
            </div>
          ) : !apiResult ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-12 h-12 rounded-full bg-[#f4f0e8] border border-[#dfd8c8] flex items-center justify-center text-[#8c8477] mb-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                No Alignment Data Available
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md mb-4 leading-relaxed">
                Run analysis on Phase 01 to align propositions between student and reference answers.
              </p>
              <button
                type="button"
                onClick={onRetryConnection}
                className="px-4 py-2 bg-[#1e1c19] hover:bg-[#343029] text-[#f7f4ed] rounded-lg text-xs font-mono font-medium transition-all cursor-pointer shadow-xs active:scale-95"
              >
                Retry Analysis
              </button>
            </div>
          ) : (
            <AlignmentPhase
              matchData={apiResult.phase_04_match}
              relationsData={apiResult.phase_03_relations}
            />
          )}
        </div>
      )}

      {activePhase === '05' && (
        <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-10 h-10 border-3 border-indigo-700 border-t-transparent rounded-full animate-spin mb-4" />
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                Evaluating Proposition Truth &amp; Information
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md">
                Assessing propositional textual entailment and classifying unmatched assertions...
              </p>
            </div>
          ) : !apiResult ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-12 h-12 rounded-full bg-[#f4f0e8] border border-[#dfd8c8] flex items-center justify-center text-[#8c8477] mb-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                No Assessment Data Available
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md mb-4 leading-relaxed">
                Run analysis on Phase 01 to evaluate proposition assessments.
              </p>
              <button
                type="button"
                onClick={onRetryConnection}
                className="px-4 py-2 bg-[#1e1c19] hover:bg-[#343029] text-[#f7f4ed] rounded-lg text-xs font-mono font-medium transition-all cursor-pointer shadow-xs active:scale-95"
              >
                Retry Analysis
              </button>
            </div>
          ) : (
            <AssessmentPhase
              entailmentData={apiResult.phase_05_entailment}
              additionalData={apiResult.phase_06_additional}
              relationsData={apiResult.phase_03_relations}
            />
          )}
        </div>
      )}

      {activePhase === '06' && (
        <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-10 h-10 border-3 border-indigo-700 border-t-transparent rounded-full animate-spin mb-4" />
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                Synthesizing Final ASAG Score
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md">
                Computing reference coverage, proposition modulations, and attribution traces...
              </p>
            </div>
          ) : !apiResult ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-12 h-12 rounded-full bg-[#f4f0e8] border border-[#dfd8c8] flex items-center justify-center text-[#8c8477] mb-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                No Scoring Data Available
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md mb-4 leading-relaxed">
                Run analysis on Phase 01 to synthesize final proposition-level ASAG scores.
              </p>
              <button
                type="button"
                onClick={onRetryConnection}
                className="px-4 py-2 bg-[#1e1c19] hover:bg-[#343029] text-[#f7f4ed] rounded-lg text-xs font-mono font-medium transition-all cursor-pointer shadow-xs active:scale-95"
              >
                Retry Analysis
              </button>
            </div>
          ) : (
            <ScoringPhase
              scoreData={apiResult.phase_07_score}
            />
          )}
        </div>
      )}

      <BottomHUD
        activePhase={activePhase}
        onPhaseChange={onPhaseChange}
        hasAnalysis={Boolean(apiResult)}
        hasCanvas={activePhase === '01' || activePhase === '02' || activePhase === '03'}
        zoom={zoom}
        onZoomIn={() =>
          onZoomChange &&
          onZoomChange((z) => Math.min(Number((z + 0.1).toFixed(2)), 2.2))
        }
        onZoomOut={() =>
          onZoomChange &&
          onZoomChange((z) => Math.max(Number((z - 0.1).toFixed(2)), 0.45))
        }
        onResetFit={onResetFit}
      />
    </div>
  );
}
