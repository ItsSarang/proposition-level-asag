import { useState, useEffect, Component } from 'react';
import Header from './components/Header';
import WorkbenchPage from './pages/WorkbenchPage';
import ResearchPage from './pages/ResearchPage';
import { analyzeAnswer } from './services/api';
import { buildParseGraph } from './services/dependencyParser';
import { PRESETS } from './data/presets';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ASAG Workbench Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-[#f7f4ed]">
          <div className="max-w-lg bg-[#fdfcf9] p-6 rounded-2xl border border-rose-300 shadow-sm text-left">
            <h3 className="text-base font-bold text-rose-800 mb-1">
              Workbench Render Issue
            </h3>
            <p className="text-xs font-mono text-[#706b63] mb-3">
              {this.state.error?.message || 'An unexpected error occurred while rendering the canvas.'}
            </p>
            <button
              type="button"
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-3.5 py-1.5 bg-[#1e1c19] text-[#f7f4ed] rounded-lg text-xs font-mono cursor-pointer"
            >
              Retry Render
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const initialInput = {
  question: PRESETS[0].question,
  referenceAnswer: PRESETS[0].referenceAnswer,
  studentAnswer: PRESETS[0].studentAnswer,
};

const initialGraph = {
  nodes: [],
  edges: [],
  textTokens: [],
  targetText: initialInput.studentAnswer,
  targetMode: 'student',
  sentenceCount: 1,
  activeSentenceIndex: 0,
  isOffline: false,
};

export default function App() {
  const [activeTab, setActiveTab] = useState('workbench');
  const [activePhase, setActivePhase] = useState('01');
  const [hasAnalysis, setHasAnalysis] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const [analysisInput, setAnalysisInput] = useState(initialInput);
  const [apiResult, setApiResult] = useState(null);
  const [parseMode, setParseMode] = useState('student');
  const [activeSentenceIndex, setActiveSentenceIndex] = useState(0);

  const [parseData, setParseData] = useState(initialGraph);
  const [zoom, setZoom] = useState(1);
  const [showGrid] = useState(true);
  const [fitTrigger, setFitTrigger] = useState(0);
  const [selectedNode, setSelectedNode] = useState(null);

  const runAnalysis = async (inputData) => {
    setLoading(true);
    setStatusMessage('Running V5 proposition & dependency analysis engine...');
    setAnalysisInput(inputData);

    try {
      const apiResponse = await analyzeAnswer({
        question: inputData.question,
        referenceAnswer: inputData.referenceAnswer,
        studentAnswer: inputData.studentAnswer,
      });

      if (apiResponse && apiResponse.status === 'SUCCESS') {
        setApiResult(apiResponse);
        const graph = buildParseGraph(inputData, apiResponse, parseMode, activeSentenceIndex);
        setParseData(graph);
        setSelectedNode(graph.nodes[0] || null);
        setFitTrigger((c) => c + 1);
      } else {
        setApiResult(null);
        setParseData({
          nodes: [],
          edges: [],
          textTokens: [],
          targetText: inputData.studentAnswer,
          targetMode: parseMode,
          sentenceCount: 0,
          activeSentenceIndex: 0,
          isOffline: true,
        });
        setSelectedNode(null);
      }
    } catch {
      setApiResult(null);
      setParseData({
        nodes: [],
        edges: [],
        textTokens: [],
        targetText: inputData.studentAnswer,
        targetMode: parseMode,
        sentenceCount: 0,
        activeSentenceIndex: 0,
        isOffline: true,
      });
      setSelectedNode(null);
    } finally {
      setLoading(false);
      setStatusMessage('');
      setHasAnalysis(true);
    }
  };

  useEffect(() => {
    runAnalysis(initialInput);
  }, []);

  const handleAnalyze = (inputData) => {
    setActivePhase('02');

    const isSameInput =
      apiResult &&
      analysisInput?.question === inputData.question &&
      analysisInput?.referenceAnswer === inputData.referenceAnswer &&
      analysisInput?.studentAnswer === inputData.studentAnswer;

    if (!isSameInput) {
      runAnalysis(inputData);
    } else {
      const graph = buildParseGraph(inputData, apiResult, parseMode, activeSentenceIndex);
      setParseData(graph);
      setSelectedNode(graph.nodes[0] || null);
      setFitTrigger((c) => c + 1);
    }
  };

  const handleSwitchParseMode = (mode) => {
    setParseMode(mode);
    setActiveSentenceIndex(0);
    if (apiResult) {
      const graph = buildParseGraph(analysisInput, apiResult, mode, 0);
      setParseData(graph);
      setSelectedNode(graph.nodes[0] || null);
    }
  };

  const handleSwitchSentence = (sentIdx) => {
    setActiveSentenceIndex(sentIdx);
    if (apiResult) {
      const graph = buildParseGraph(analysisInput, apiResult, parseMode, sentIdx);
      setParseData(graph);
      setSelectedNode(graph.nodes[0] || null);
    }
  };

  const handleResetFit = () => {
    setFitTrigger((c) => c + 1);
  };

  const handleSelectNodeIndex = (index) => {
    if (parseData?.nodes?.[index]) {
      setSelectedNode(parseData.nodes[index]);
    }
  };

  return (
    <div className="h-screen flex flex-col text-[#1e1c19] overflow-hidden bg-[#f7f4ed]">
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        activePhase={activePhase}
        onPhaseChange={setActivePhase}
        hasAnalysis={hasAnalysis}
      />

      {activeTab === 'workbench' && (
        <ErrorBoundary>
          <WorkbenchPage
            activePhase={activePhase}
            loading={loading}
            statusMessage={statusMessage}
            onAnalyze={handleAnalyze}
            parseData={parseData}
            parseMode={parseMode}
            onSwitchParseMode={handleSwitchParseMode}
            activeSentenceIndex={activeSentenceIndex}
            onSwitchSentence={handleSwitchSentence}
            selectedNode={selectedNode}
            onSelectNode={setSelectedNode}
            onSelectNodeIndex={handleSelectNodeIndex}
            zoom={zoom}
            onZoomChange={setZoom}
            showGrid={showGrid}
            fitTrigger={fitTrigger}
            onResetFit={handleResetFit}
            onRetryConnection={() => runAnalysis(analysisInput)}
          />
        </ErrorBoundary>
      )}

      {activeTab === 'research' && <ResearchPage />}

      {activePhase === '01' && activeTab === 'workbench' && (
        <footer className="w-full border-t border-[#dfd8c8] py-4 bg-transparent mt-auto shrink-0">
          <div className="max-w-[1080px] mx-auto px-6 flex items-center justify-between text-[11px] font-mono text-[#8c8477]">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
              <span>ASAG Lab Research</span>
            </div>
            <span>Autonomous Short Answer Grading — Universal Dependencies + Semantic Graphs</span>
          </div>
        </footer>
      )}
    </div>
  );
}
