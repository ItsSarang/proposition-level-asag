export default function ResearchPage() {
  return (
    <main className="flex-1 flex flex-col items-center justify-start py-8 px-6 max-w-[1080px] mx-auto w-full overflow-y-auto">
      <div className="w-full bg-[#fdfcf9] rounded-2xl border border-[#dfd8c8] shadow-[0_4px_24px_-4px_rgba(50,40,30,0.06)] p-8 sm:p-10">
        <div className="mb-6 pb-6 border-b border-[#dfd8c8]">
          <span className="text-[11px] font-mono text-indigo-800 font-semibold uppercase tracking-wider">
            Research Foundation &amp; Methodology
          </span>
          <h1 className="text-2xl font-bold text-[#1e1c19] mt-1 mb-2 tracking-tight">
            Interpretable Proposition-Level Automated Short Answer Grading
          </h1>
          <p className="text-xs font-mono text-[#8c8477]">
            Based on Basak et al. (2019) Dependency &amp; Entailment Framework
          </p>
        </div>

        <div className="flex flex-col gap-6 text-[14px] text-[#2c2925] leading-relaxed font-sans">
          <section>
            <h2 className="text-base font-bold text-[#1e1c19] mb-2">
              Research Objective
            </h2>
            <p>
              This investigation evaluates whether an interpretable proposition-level extension of a classical
              semantic/dependency-based ASAG system can classify unmatched student information as correct
              additional, irrelevant, or incorrect information, and whether incorporating this evaluation
              improves agreement with human grading.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-[#1e1c19] mb-2">
              Methodological Foundation
            </h2>
            <p className="mb-3">
              The architecture builds upon the textual entailment and dependency triple approach proposed by
              Basak, Naskar, &amp; Gelbukh (2019, DOI: 10.3233/JIFS-179038). The pipeline decomposes into
              seven transparent phases:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-[#f4f0e8] border border-[#dfd8c8]">
                <span className="font-semibold text-[#1e1c19] block mb-1">Phase 01–02: Syntactic Dependencies</span>
                Universal Dependencies parsing extracts relational arcs and governor-dependent roles.
              </div>
              <div className="p-3 rounded-xl bg-[#f4f0e8] border border-[#dfd8c8]">
                <span className="font-semibold text-[#1e1c19] block mb-1">Phase 03: Clausal Propositions</span>
                Relational subject-predicate-object triples and argument structures are isolated.
              </div>
              <div className="p-3 rounded-xl bg-[#f4f0e8] border border-[#dfd8c8]">
                <span className="font-semibold text-[#1e1c19] block mb-1">Phase 04–05: Matching &amp; Entailment</span>
                Lexical-semantic alignment computes proposition satisfaction and polarity agreement.
              </div>
              <div className="p-3 rounded-xl bg-[#f4f0e8] border border-[#dfd8c8]">
                <span className="font-semibold text-[#1e1c19] block mb-1">Phase 06–07: Proposition Grading</span>
                Unmatched propositions are classified into additional or misconception categories.
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
