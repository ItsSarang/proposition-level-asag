import React from 'react';

export default function DocsPage() {
  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-10 space-y-12">
      {/* Title */}
      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-indigo-50 text-indigo-700 border border-indigo-200">
          <span className="w-1.5 h-1.5 rounded-full bg-indigo-600" />
          Technical Documentation
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
          ASAG Lab Documentation
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed font-sans max-w-2xl">
          Complete guide to the interpretable ASAG research engine, understanding proposition-level analysis, additional-information classifications, and scoring mechanics.
        </p>
      </div>

      {/* 1. What is ASAG Lab? */}
      <section className="space-y-3 border-t border-slate-200/80 pt-8">
        <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
          1. What is ASAG Lab?
        </h2>
        <p className="text-sm text-slate-700 leading-relaxed font-sans">
          ASAG Lab is an interactive natural language processing (NLP) research instrument designed for Automated Short Answer Grading (ASAG). Rather than functioning as an opaque neural black box that outputs an uncalibrated grade, ASAG Lab exposes the internal structural evidence across every stage of evaluation: from Universal Dependencies and proposition alignment to textual entailment, misconception detection, and bounded grade modulation.
        </p>
      </section>

      {/* 2. The 7 Analysis Phases */}
      <section className="space-y-4 border-t border-slate-200/80 pt-8">
        <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
          2. The Seven Analysis Phases
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1">
            <span className="font-semibold text-indigo-600">01 INPUT</span>
            <p className="text-slate-600 font-sans">
              Displays verbatim question prompt, instructor reference target, and student candidate text without modification.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1">
            <span className="font-semibold text-indigo-600">02 PARSE</span>
            <p className="text-slate-600 font-sans">
              Universal Dependency parsing extracting syntactic arcs (nsubj, dobj, ROOT, prep, amod) and token part-of-speech tags.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1">
            <span className="font-semibold text-indigo-600">03 RELATIONS</span>
            <p className="text-slate-600 font-sans">
              Extracts clausal Subject-Predicate-Object triples and hybrid propositions preserving character span offsets.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1">
            <span className="font-semibold text-indigo-600">04 MATCH</span>
            <p className="text-slate-600 font-sans">
              Role-preserving bipartite alignment matching student assertions against reference propositions.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1">
            <span className="font-semibold text-indigo-600">05 ENTAILMENT</span>
            <p className="text-slate-600 font-sans">
              Proposition-level entailment evaluation assigning ENTAILS, UNCERTAIN, or CONTRADICTS with slot evidence.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1">
            <span className="font-semibold text-indigo-600">06 ADDITIONAL</span>
            <p className="text-slate-600 font-sans">
              Evaluates unmatched student assertions against domain knowledge rules, contradiction guards, and question relevance.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200/80 space-y-1 sm:col-span-2">
            <span className="font-semibold text-indigo-600">07 SCORE</span>
            <p className="text-slate-600 font-sans">
              Synthesizes effective base coverage with Model D2 soft-gated scoring, producing the final grade and full itemized trace.
            </p>
          </div>
        </div>
      </section>

      {/* 3. Unmatched Information Classifications */}
      <section className="space-y-4 border-t border-slate-200/80 pt-8">
        <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
          3. Additional-Information Classifications
        </h2>
        <p className="text-sm text-slate-700 font-sans leading-relaxed">
          The core research contribution is the explicit evaluation of information in the student's answer that does not align directly with the reference answer. These propositions are categorized into four standardized classes:
        </p>

        <div className="space-y-3 text-xs font-mono">
          <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-200 space-y-1">
            <span className="font-semibold text-indigo-800">MATCHED BY BASE ASAG</span>
            <p className="text-slate-700 font-sans">
              Core reference information that was directly recognized by the triple matcher or recovered via core paraphrase recovery. Forms the foundation of base coverage.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-emerald-50/60 border border-emerald-200 space-y-1">
            <span className="font-semibold text-emerald-800">CORRECT ADDITIONAL</span>
            <p className="text-slate-700 font-sans">
              Information not directly present in the reference answer, but verified as technically correct, domain-relevant, and enriching relative to the question prompt. May provide a modest score bonus under saturating bounds.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="font-semibold text-slate-700">IRRELEVANT</span>
            <p className="text-slate-700 font-sans">
              Peripheral, conversational, or off-topic information that neither supports nor contradicts the core concepts. Produces zero score effect (neither bonus nor penalty).
            </p>
          </div>

          <div className="p-4 rounded-xl bg-rose-50/60 border border-rose-200 space-y-1">
            <span className="font-semibold text-rose-800">INCORRECT</span>
            <p className="text-slate-700 font-sans">
              Factual misconceptions, contradictory claims, or invalid statements relative to the subject matter. Incur proportional penalties according to severity hierarchies.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200 space-y-1">
            <span className="font-semibold text-amber-800">UNCERTAIN</span>
            <p className="text-slate-700 font-sans">
              Information where available domain evidence or syntactic alignment is insufficient to establish truth or falsehood conclusively. Treated neutrally with zero score effect.
            </p>
          </div>
        </div>
      </section>

      {/* 4. Research Foundation */}
      <section className="space-y-3 border-t border-slate-200/80 pt-8">
        <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
          4. Research Foundation
        </h2>
        <p className="text-sm text-slate-700 leading-relaxed font-sans">
          The methodological foundation is inspired by Basak, Naskar, & Gelbukh (2019), <em>"Short-answer grading using textual entailment"</em> (Journal of Intelligent & Fuzzy Systems). The Base ASAG pipeline faithfully mirrors their dependency-triple matching and textual entailment approach. The proposition-level extension (Stages 11–14, Experiment 4, and Experiment 5) investigates whether evaluating unmatched student information improves grading performance over strict reference coverage.
        </p>
      </section>

      {/* 5. Empirical Findings & Limitations */}
      <section className="space-y-3 border-t border-slate-200/80 pt-8">
        <h2 className="text-xl font-semibold text-slate-900 tracking-tight">
          5. Empirical Findings & Research Integrity
        </h2>
        <p className="text-sm text-slate-700 leading-relaxed font-sans">
          Across the official Mohler ASAG benchmark (2,273 active records across 81 computer science questions), our experimental evaluation revealed:
        </p>
        <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1.5 font-sans leading-relaxed">
          <li>
            <strong>Structural Interpretability</strong>: Proposition-level extraction, alignment, and explanation traces are completely feasible and fully verifiable.
          </li>
          <li>
            <strong>Base ASAG vs Proposed ASAG</strong>: The final proposed model (V5, Pearson r = 0.2428) significantly outperforms Base ASAG (V1, Pearson r = 0.1379) and improves absolute error (MAE reduced from 3.8050 to 3.4711).
          </li>
          <li>
            <strong>Lexical Baseline Status</strong>: TF-IDF (V0, Pearson r = 0.4184) remains stronger on overall rank correlation against holistic human grades due to human graders rewarding exact keyword matches.
          </li>
        </ul>
      </section>
    </div>
  );
}
