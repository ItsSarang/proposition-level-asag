import WorkbenchCard from '../components/WorkbenchCard';
import ParsePhase from '../components/ParsePhase';
import PropositionPhase from '../components/PropositionPhase';

export default function WorkbenchPage({
  activePhase,
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
    <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
      {activePhase === '01' && (
        <main className="flex-1 flex flex-col items-center justify-start py-8 px-6 max-w-[1080px] mx-auto w-full overflow-y-auto">
          <WorkbenchCard
            onAnalyze={onAnalyze}
            loading={loading}
            statusMessage={statusMessage}
          />
        </main>
      )}

      {activePhase === '02' && (
        <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-10 h-10 border-3 border-indigo-700 border-t-transparent rounded-full animate-spin mb-4" />
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                Analyzing Syntactic Dependencies
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md">
                V5 model is parsing clausal triples and building Universal Dependencies trees...
              </p>
            </div>
          ) : parseData.isOffline ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-12 h-12 rounded-full bg-[#f4f0e8] border border-[#dfd8c8] flex items-center justify-center text-[#8c8477] mb-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                ASAG Engine Offline
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md mb-4 leading-relaxed">
                Start the local Flask backend or connect your deployed backend URL to parse syntactic dependency trees:
                <br />
                <code className="text-[#1e1c19] bg-[#eae4d6] px-2.5 py-1 rounded mt-2 inline-block font-mono text-[11px] border border-[#dfd8c8]">
                  PYTHONPATH=. .venv/bin/python3 backend/main.py
                </code>
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
            <ParsePhase
              parseData={parseData}
              parseMode={parseMode}
              onSwitchParseMode={onSwitchParseMode}
              activeSentenceIndex={activeSentenceIndex}
              onSwitchSentence={onSwitchSentence}
              selectedNode={selectedNode}
              onSelectNode={onSelectNode}
              onSelectNodeIndex={onSelectNodeIndex}
              zoom={zoom}
              onZoomChange={onZoomChange}
              showGrid={showGrid}
              fitTrigger={fitTrigger}
              onResetFit={onResetFit}
            />
          )}
        </div>
      )}

      {activePhase === '03' && (
        <div className="flex-1 flex flex-col min-h-0 w-full overflow-hidden">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center select-none bg-[#f7f4ed]">
              <div className="w-10 h-10 border-3 border-indigo-700 border-t-transparent rounded-full animate-spin mb-4" />
              <h3 className="text-base font-semibold text-[#1e1c19] mb-1">
                Extracting Clausal Propositions
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md">
                Decomposing relational triples, clausal arguments, and polarity structures...
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
                No Proposition Data Available
              </h3>
              <p className="text-[12px] font-mono text-[#706b63] max-w-md mb-4 leading-relaxed">
                Run analysis on Phase 01 to extract relational propositions from the candidate answer.
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
            <PropositionPhase
              relationsData={apiResult.phase_03_relations}
              studentAnswer={analysisInput?.studentAnswer || ''}
              referenceAnswer={analysisInput?.referenceAnswer || ''}
            />
          )}
        </div>
      )}
    </div>
  );
}
