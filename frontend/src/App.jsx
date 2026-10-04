import React, { useState } from 'react';
import Header from './components/Header';
import PhaseNav from './components/PhaseNav';
import WorkbenchInput from './components/WorkbenchInput';
import AnalysisCanvas from './components/AnalysisCanvas';
import ResearchPage from './pages/ResearchPage';
import DocsPage from './pages/DocsPage';
import { analyzeAnswer } from './services/api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('workbench');
  const [activePhase, setActivePhase] = useState('01');

  // Input state
  const [question, setQuestion] = useState('');
  const [referenceAnswer, setReferenceAnswer] = useState('');
  const [studentAnswer, setStudentAnswer] = useState('');

  // Analysis state
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!question.trim()) {
      setError('Please provide a Question prompt.');
      return;
    }
    if (!referenceAnswer.trim()) {
      setError('Please provide an Instructor Reference Answer.');
      return;
    }
    if (!studentAnswer.trim()) {
      setError("Please provide a Student's Answer to analyze.");
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      const data = await analyzeAnswer({
        question,
        referenceAnswer,
        studentAnswer,
        scale: 5.0,
      });
      setAnalysisData(data);
      // Start in Phase 03 Relations or Phase 01 Input
      setActivePhase('03');
    } catch (err) {
      setError(err.message || 'An error occurred during ASAG analysis.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetWorkbench = () => {
    setAnalysisData(null);
    setActivePhase('01');
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#fafaf9] text-slate-800 font-sans selection:bg-indigo-100 selection:text-indigo-900">
      {/* Global Minimal Header */}
      <Header
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        hasActiveAnalysis={!!analysisData}
        onResetWorkbench={handleResetWorkbench}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col">
        {currentTab === 'workbench' && (
          <>
            {analysisData ? (
              <div className="flex-1 flex flex-col">
                <PhaseNav
                  activePhase={activePhase}
                  onSelectPhase={setActivePhase}
                  isAnalysisActive={true}
                />
                <AnalysisCanvas
                  analysisData={analysisData}
                  activePhase={activePhase}
                  onPhaseChange={setActivePhase}
                  onNewAnalysis={handleResetWorkbench}
                />
              </div>
            ) : (
              <div className="flex-1 flex flex-col justify-center">
                <PhaseNav
                  activePhase="01"
                  onSelectPhase={() => {}}
                  isAnalysisActive={false}
                />
                <WorkbenchInput
                  question={question}
                  setQuestion={setQuestion}
                  referenceAnswer={referenceAnswer}
                  setReferenceAnswer={setReferenceAnswer}
                  studentAnswer={studentAnswer}
                  setStudentAnswer={setStudentAnswer}
                  onAnalyze={handleAnalyze}
                  isLoading={isLoading}
                  error={error}
                />
              </div>
            )}
          </>
        )}

        {currentTab === 'research' && <ResearchPage />}
        {currentTab === 'docs' && <DocsPage />}
      </main>

      {/* Subtle Footer */}
      {!analysisData && (
        <footer className="w-full py-4 px-6 border-t border-slate-200/60 bg-white/50 text-[11px] font-mono text-slate-400 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
            <span>ASAG Lab Research</span>
          </div>
          <div>Autonomous Short Answer Grading — Universal Dependencies + Semantic Graphs</div>
        </footer>
      )}
    </div>
  );
}
