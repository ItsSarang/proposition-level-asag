import React, { useState } from 'react';

const PIPELINE_STAGES = [
  {
    step: '01',
    name: 'Input Normalization',
    summary: 'Receives question prompt, gold reference answer, and candidate student answer.',
    details: 'Sentence segmentation and character offset indexing preserving surface provenance for character-level highlight linking.',
  },
  {
    step: '02',
    name: 'Linguistic Preprocessing',
    summary: 'Tokenization, lemmatization, and part-of-speech tagging.',
    details: 'Uses spaCy en_core_web_sm pipeline to generate fine-grained POS tags, morpho-syntactic features, and stopword isolation without losing sentence context.',
  },
  {
    step: '03',
    name: 'Dependency Parsing',
    summary: 'Universal syntactic dependency parsing extracting head-modifier arcs.',
    details: 'Captures grammatical relations (nsubj, dobj, ROOT, ccomp, prep, pobj) and purpose non-finite verb chains (xcomp) to handle complex clausal syntax.',
  },
  {
    step: '04',
    name: 'Dependency Triples / Hybrid Propositions',
    summary: 'Extracts Subject-Predicate-Object triples and nominal/predicate fragments.',
    details: 'Converts grammatical head dependencies into discrete propositional assertions with explicit polarity, modality, and token span ranges.',
  },
  {
    step: '05',
    name: 'Lexical-Semantic Comparator',
    summary: '4-tier semantic hierarchy for slot similarity evaluation.',
    details: 'Tier 1: Exact string match (1.00). Tier 2: Lemma match (0.95). Tier 3: WordNet synset path similarity (0.80). Tier 4: Domain lexicon equivalence.',
  },
  {
    step: '06',
    name: 'Role-Preserving Triple Matching',
    summary: 'Optimal bipartite matching aligning student assertions to reference concepts.',
    details: 'Aligns Subject to Subject, Predicate to Predicate, and Object to Object. Discards cross-slot noise and preserves unmatched student assertions.',
  },
  {
    step: '07',
    name: 'Textual Entailment Analyzer',
    summary: 'Evaluates propositional entailment on matched assertion pairs.',
    details: 'Assigns ENTAILS (1.00), UNCERTAIN (0.50), or CONTRADICTS (0.00) based on slot similarity and structural negation/polarity consistency.',
  },
  {
    step: '08',
    name: 'Core Paraphrase Recovery',
    summary: 'Recovers unmatched student propositions expressing reference core meaning.',
    details: 'Detects converse comparative equivalence (e.g. greater than ↔ less than), unanchored predicate bridging, and coordinate concept splits.',
  },
  {
    step: '09',
    name: 'Contradiction Guard Pipeline',
    summary: 'Filters spurious contradictions on valid conversational variations.',
    details: 'Guards converse relational symmetry, coordinate term enumerations (e.g., public/private), contrastive subjects, and scope qualifiers.',
  },
  {
    step: '10',
    name: 'Additional Information Classification',
    summary: 'Categorizes genuine unmatched information into 4 discrete classes.',
    details: 'CORRECT ADDITIONAL (enriching facts), IRRELEVANT (neutral off-topic context), INCORRECT (genuine factual conflict), and UNCERTAIN.',
  },
  {
    step: '11',
    name: 'Model D2 Severity-Aware Scorer',
    summary: 'Soft-gated nonlinear scoring combining base coverage with bounded adjustments.',
    details: 'Applies smooth sigmoid gating, diminishing returns on additional bonuses, and proportional penalties scaled by misconception severity.',
  },
];

export default function ResearchPage() {
  const [activeStageIndex, setActiveStageIndex] = useState(0);

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-10 space-y-12">
      {/* Title & Identity */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-indigo-50 text-indigo-700 border border-indigo-200">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
          NLP Research Architecture
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          Automatic Short Answer Grading using Semantic and Dependency Analysis
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed font-sans max-w-2xl">
          An interpretable NLP methodology investigating whether proposition-level analysis of unmatched student information can evaluate valid additions, misconceptions, and conversational irrelevance to improve alignment with human grading.
        </p>
      </div>

      {/* Research Question */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200/90 shadow-sm space-y-3">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block">
          CENTRAL RESEARCH QUESTION
        </span>
        <blockquote className="text-base font-medium text-slate-900 italic border-l-3 border-indigo-600 pl-4 leading-relaxed font-serif">
          "Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"
        </blockquote>
        <p className="text-xs text-slate-500 font-mono pt-2">
          Status: Epistemically investigated across 2,273 active responses from the Mohler ASAG benchmark.
        </p>
      </div>

      {/* 3 Systems Comparison */}
      <div className="space-y-4">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block">
          THREE EVALUATED ASAG ARCHITECTURES
        </span>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-2">
            <span className="text-xs font-mono font-semibold text-slate-500">SYSTEM 1</span>
            <div className="font-semibold text-sm text-slate-900">TF-IDF Baseline (V0)</div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              Lexical bag-of-words cosine similarity. Strongest rank correlation against holistic human grades on the full benchmark.
            </p>
            <div className="pt-2 text-[11px] font-mono text-slate-500">
              Pearson r = 0.4184 | Spearman ρ = 0.4424
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs space-y-2">
            <span className="text-xs font-mono font-semibold text-slate-500">SYSTEM 2</span>
            <div className="font-semibold text-sm text-slate-900">Base ASAG (V1)</div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              Basak et al. (2019)-inspired classical dependency triple matching. Reference coverage-driven scoring with zero credit for unmatched information.
            </p>
            <div className="pt-2 text-[11px] font-mono text-slate-500">
              Pearson r = 0.1379 | Spearman ρ = 0.1181
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-white border-2 border-indigo-500/40 bg-indigo-50/20 shadow-xs space-y-2">
            <span className="text-xs font-mono font-semibold text-indigo-600">SYSTEM 3 (PROPOSED)</span>
            <div className="font-semibold text-sm text-slate-900">Final Proposed ASAG (V5)</div>
            <p className="text-xs text-slate-600 font-sans leading-relaxed">
              Proposition-level unmatched information analysis with core recovery, contradiction guards, and Model D2 soft-gated scoring.
            </p>
            <div className="pt-2 text-[11px] font-mono text-indigo-700 font-medium">
              Pearson r = 0.2428 | Spearman ρ = 0.2404
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Pipeline Explorer */}
      <div className="space-y-4">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block">
          INTERACTIVE 11-STAGE PIPELINE EXPLORER
        </span>

        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-6">
          {/* Stage Buttons */}
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
            {PIPELINE_STAGES.map((s, idx) => (
              <button
                key={s.step}
                onClick={() => setActiveStageIndex(idx)}
                className={`px-3 py-2 rounded-xl text-xs font-mono whitespace-nowrap transition-all cursor-pointer ${
                  activeStageIndex === idx
                    ? 'bg-slate-900 text-white font-semibold shadow-xs'
                    : 'bg-slate-50 text-slate-600 hover:bg-slate-100 border border-slate-200/60'
                }`}
              >
                <span>{s.step}</span> {s.name}
              </button>
            ))}
          </div>

          {/* Active Stage Detail */}
          {(() => {
            const current = PIPELINE_STAGES[activeStageIndex];
            return (
              <div className="p-5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-semibold text-indigo-600 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                      STAGE {current.step}
                    </span>
                    <h3 className="text-base font-semibold text-slate-900">
                      {current.name}
                    </h3>
                  </div>
                  <span className="text-xs font-mono text-slate-400">Interpretable NLP</span>
                </div>
                <p className="text-sm font-medium text-slate-800 font-sans">
                  {current.summary}
                </p>
                <p className="text-xs text-slate-600 font-sans leading-relaxed pt-1">
                  {current.details}
                </p>
              </div>
            );
          })()}
        </div>
      </div>

      {/* Benchmark Verification Table */}
      <div className="space-y-4">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block">
          OFFICIAL BENCHMARK EVALUATION (MOHLER CS DATASET, N=2,273)
        </span>

        <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs text-xs font-mono">
          <table className="w-full text-left divide-y divide-slate-200">
            <thead className="bg-slate-50 text-slate-500 font-medium">
              <tr>
                <th className="p-3.5">Model</th>
                <th className="p-3.5">Architecture</th>
                <th className="p-3.5 text-right">Pearson r</th>
                <th className="p-3.5 text-right">Spearman ρ</th>
                <th className="p-3.5 text-right">MAE</th>
                <th className="p-3.5 text-right">RMSE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              <tr>
                <td className="p-3.5 font-semibold text-slate-900">V0</td>
                <td className="p-3.5 font-sans">TF-IDF Lexical Baseline</td>
                <td className="p-3.5 text-right font-bold text-slate-900">0.4184</td>
                <td className="p-3.5 text-right font-bold text-slate-900">0.4424</td>
                <td className="p-3.5 text-right">2.6571</td>
                <td className="p-3.5 text-right">2.9178</td>
              </tr>
              <tr>
                <td className="p-3.5 font-semibold text-slate-900">V1</td>
                <td className="p-3.5 font-sans">Base ASAG (Basak-inspired)</td>
                <td className="p-3.5 text-right">0.1379</td>
                <td className="p-3.5 text-right">0.1181</td>
                <td className="p-3.5 text-right">3.8050</td>
                <td className="p-3.5 text-right">4.0373</td>
              </tr>
              <tr>
                <td className="p-3.5 font-semibold text-slate-900">V2</td>
                <td className="p-3.5 font-sans">Historical Proposition ASAG</td>
                <td className="p-3.5 text-right">0.1342</td>
                <td className="p-3.5 text-right">0.0765</td>
                <td className="p-3.5 text-right">3.2176</td>
                <td className="p-3.5 text-right">3.5179</td>
              </tr>
              <tr>
                <td className="p-3.5 font-semibold text-slate-900">V3</td>
                <td className="p-3.5 font-sans">Enhanced Proposition ASAG</td>
                <td className="p-3.5 text-right">0.2037</td>
                <td className="p-3.5 text-right">0.2007</td>
                <td className="p-3.5 text-right">3.5955</td>
                <td className="p-3.5 text-right">3.8862</td>
              </tr>
              <tr>
                <td className="p-3.5 font-semibold text-slate-900">V4</td>
                <td className="p-3.5 font-sans">Severity-Aware ASAG (Model D)</td>
                <td className="p-3.5 text-right">0.2055</td>
                <td className="p-3.5 text-right">0.2033</td>
                <td className="p-3.5 text-right">3.6288</td>
                <td className="p-3.5 text-right">3.9270</td>
              </tr>
              <tr className="bg-indigo-50/40">
                <td className="p-3.5 font-semibold text-indigo-900">V5</td>
                <td className="p-3.5 font-sans font-medium text-indigo-950">
                  Final Proposed Model (Model D2)
                </td>
                <td className="p-3.5 text-right font-bold text-indigo-700">0.2428</td>
                <td className="p-3.5 text-right font-bold text-indigo-700">0.2404</td>
                <td className="p-3.5 text-right font-bold text-indigo-700">3.4711</td>
                <td className="p-3.5 text-right font-bold text-indigo-700">3.7637</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-[11px] font-mono text-slate-500">
          TF-IDF (V0) remains stronger than the semantic/dependency models on the primary full active benchmark; see the frozen Experiment 5 results for the exact evaluation metrics.
        </p>
      </div>
    </div>
  );
}
