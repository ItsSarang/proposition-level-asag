"""
Interactive one-cell laboratory interface for ASAG testing and inspection.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from IPython.display import HTML, clear_output, display

from asag_lab.results import (
    BatchEvaluationResult,
    SingleEvaluationRecord,
    derive_system_observation,
    format_dependency_relations_tables,
    format_entailment_table,
    format_preprocessing_tables,
    format_score_contributions_table,
    format_semantic_matching_table,
    format_unmatched_reference_table,
    format_unmatched_student_table,
)
from base_asag.pipeline import BaseASAGPipeline
from baseline.tfidf_cosine.baseline import TfidfCosineBaseline

try:
    import ipywidgets as widgets
    HAS_WIDGETS = True
except ImportError:
    HAS_WIDGETS = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default demonstration setup from GEMINI.md
DEFAULT_EXPERIMENT_NAME = "Primary Key Baseline vs Base ASAG Test"
DEFAULT_QUESTION = "What is the purpose of a primary key?"
DEFAULT_REFERENCE = "A primary key uniquely identifies each record in a table."

DEFAULT_DEMO_ANSWERS = [
    "A primary key uniquely identifies each record in a table.",
    "A primary key uniquely identifies every row in a table.",
    "A primary key identifies records in a table.",
    "A primary key uniquely identifies each record in a table and cannot contain NULL values.",
    "A primary key uniquely identifies each record in a table. SQL was developed in the 1970s.",
    "A primary key uniquely identifies each record in a table and can contain duplicate values.",
    "A primary key never uniquely identifies each record in a table.",
    "Photosynthesis requires sunlight, water, and carbon dioxide to produce food for plants.",
]


class ASAGLabInterface:
    """
    Interactive ASAG Experiment Laboratory widget manager.
    """

    def __init__(self):
        self.tfidf_baseline = TfidfCosineBaseline()
        self.base_pipeline = BaseASAGPipeline()

        self.current_batch: Optional[BatchEvaluationResult] = None
        self.answer_textareas: List[widgets.Textarea] = []

        # Widgets
        self.w_exp_name = widgets.Text(
            value=DEFAULT_EXPERIMENT_NAME,
            description="Experiment:",
            layout=widgets.Layout(width="60%"),
        )

        self.w_question = widgets.Textarea(
            value=DEFAULT_QUESTION,
            description="Question:",
            layout=widgets.Layout(width="98%", height="70px"),
        )

        self.w_reference = widgets.Textarea(
            value=DEFAULT_REFERENCE,
            description="Reference:",
            layout=widgets.Layout(width="98%", height="70px"),
        )

        self.answers_box = widgets.VBox([], layout=widgets.Layout(width="100%"))

        # Action Buttons
        self.btn_add_answer = widgets.Button(
            description="+ ADD ANSWER",
            button_style="success",
            icon="plus",
            layout=widgets.Layout(width="160px", margin="4px"),
        )

        self.btn_remove_answer = widgets.Button(
            description="REMOVE LAST ANSWER",
            button_style="danger",
            icon="trash",
            layout=widgets.Layout(width="190px", margin="4px"),
        )

        self.btn_reset_demo = widgets.Button(
            description="Reset to 8 Demo Answers",
            button_style="",
            icon="history",
            layout=widgets.Layout(width="210px", margin="4px"),
        )

        self.btn_clear_to_three = widgets.Button(
            description="Clear to 3 Blank Boxes",
            button_style="",
            icon="eraser",
            layout=widgets.Layout(width="190px", margin="4px"),
        )

        self.btn_run_all = widgets.Button(
            description="RUN ALL ANSWERS",
            button_style="primary",
            icon="play",
            layout=widgets.Layout(width="240px", height="42px", margin="10px 5px"),
        )

        self.btn_export = widgets.Button(
            description="EXPORT RESULTS TO CSV",
            button_style="info",
            icon="download",
            layout=widgets.Layout(width="240px", height="42px", margin="10px 5px"),
        )

        # Output areas
        self.out_summary = widgets.Output()
        self.out_export_msg = widgets.Output()
        self.out_inspector = widgets.Output()

        # Inspector controls
        self.w_inspect_dropdown = widgets.Dropdown(
            options=["Answer 1"],
            description="Select Answer:",
            layout=widgets.Layout(width="35%"),
        )

        self.btn_inspect = widgets.Button(
            description="Inspect Detailed Analysis",
            button_style="warning",
            icon="search",
            layout=widgets.Layout(width="210px"),
        )

        # Connect event handlers
        self.btn_add_answer.on_click(lambda b: self.add_answer_box())
        self.btn_remove_answer.on_click(lambda b: self.remove_last_answer_box())
        self.btn_reset_demo.on_click(lambda b: self.populate_answers(DEFAULT_DEMO_ANSWERS))
        self.btn_clear_to_three.on_click(lambda b: self.populate_answers(["", "", ""]))
        self.btn_run_all.on_click(lambda b: self.run_all())
        self.btn_export.on_click(lambda b: self.export_results())
        self.btn_inspect.on_click(lambda b: self.inspect_selected_answer())
        self.w_inspect_dropdown.observe(lambda change: self.inspect_selected_answer(), names="value")

        # Initially populate default demo answers
        self.populate_answers(DEFAULT_DEMO_ANSWERS)

    def populate_answers(self, answers_list: List[str]):
        """Populate the answer box collection with a given list of strings."""
        self.answer_textareas.clear()
        for i, text in enumerate(answers_list, start=1):
            ta = widgets.Textarea(
                value=text,
                description=f"Student {i}:",
                placeholder=f"Paste Student Answer {i} here...",
                layout=widgets.Layout(width="98%", height="65px", margin="3px 0"),
            )
            self.answer_textareas.append(ta)
        self._refresh_answers_box()

    def add_answer_box(self, initial_text: str = ""):
        """Add a new student answer box."""
        next_num = len(self.answer_textareas) + 1
        ta = widgets.Textarea(
            value=initial_text,
            description=f"Student {next_num}:",
            placeholder=f"Paste Student Answer {next_num} here...",
            layout=widgets.Layout(width="98%", height="65px", margin="3px 0"),
        )
        self.answer_textareas.append(ta)
        self._refresh_answers_box()

    def remove_last_answer_box(self):
        """Remove the last student answer box if more than 1 exist."""
        if len(self.answer_textareas) > 1:
            self.answer_textareas.pop()
            self._refresh_answers_box()

    def _refresh_answers_box(self):
        """Re-index and update the VBox display of answer textareas."""
        for i, ta in enumerate(self.answer_textareas, start=1):
            ta.description = f"Student {i}:"
        self.answers_box.children = tuple(self.answer_textareas)

    def run_all(self):
        """Execute validation, evaluate all non-empty answers, and display results."""
        with self.out_summary:
            clear_output(wait=True)

            q_val = self.w_question.value.strip()
            ref_val = self.w_reference.value.strip()
            exp_val = self.w_exp_name.value.strip() or "ASAG Experiment"

            if not q_val:
                display(HTML("<div style='color: red; font-weight: bold;'>ERROR: Question cannot be empty.</div>"))
                return
            if not ref_val:
                display(HTML("<div style='color: red; font-weight: bold;'>ERROR: Reference Answer cannot be empty.</div>"))
                return

            records: List[SingleEvaluationRecord] = []
            non_empty_indices: List[int] = []

            for idx, ta in enumerate(self.answer_textareas, start=1):
                ans_text = ta.value.strip()
                if not ans_text:
                    continue  # Ignore completely empty answer boxes

                # Run System 1: TF-IDF
                t_score = self.tfidf_baseline.similarity(ref_val, ans_text) if ans_text else 0.0

                # Run System 2: Base ASAG Pipeline
                p_res = self.base_pipeline.grade(q_val, ref_val, ans_text)

                # Derive objective observation
                obs = derive_system_observation(p_res)

                rec = SingleEvaluationRecord(
                    answer_id=f"Answer {idx}",
                    student_answer=ans_text,
                    tfidf_score=t_score,
                    base_asag_score=p_res.normalized_score,
                    matched_count=len(p_res.matched_relations),
                    missing_reference_count=len(p_res.unmatched_reference_relations),
                    unmatched_student_count=p_res.unmatched_student_count,
                    entails_count=p_res.entailed_count,
                    uncertain_count=p_res.uncertain_count,
                    contradicts_count=p_res.contradicted_count,
                    system_observation=obs,
                    pipeline_result=p_res,
                )
                records.append(rec)
                non_empty_indices.append(idx)

            if not records:
                display(HTML("<div style='color: red;'>No student answers provided. Please enter at least one answer.</div>"))
                return

            ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.current_batch = BatchEvaluationResult(
                experiment_name=exp_val,
                question=q_val,
                reference_answer=ref_val,
                timestamp=ts_now,
                records=records,
            )

            # Update inspector dropdown options
            answer_ids = [r.answer_id for r in records]
            self.w_inspect_dropdown.options = answer_ids
            if answer_ids:
                self.w_inspect_dropdown.value = answer_ids[0]

            # Display Experiment Metadata Banner
            meta_html = f"""
            <div style="background-color: #f8f9fa; border-left: 5px solid #0d6efd; padding: 12px 16px; margin: 10px 0; border-radius: 4px;">
                <h3 style="margin: 0 0 6px 0; color: #0d6efd;">Experiment Results: {exp_val}</h3>
                <div style="font-size: 0.95em; line-height: 1.5;">
                    <b>Question:</b> {q_val}<br>
                    <b>Reference Answer:</b> {ref_val}<br>
                    <b>Evaluated Answers:</b> {len(records)} &nbsp;|&nbsp; <b>Timestamp:</b> {ts_now}
                </div>
            </div>
            """
            display(HTML(meta_html))

            # Display Summary Table
            df_summary = self.current_batch.to_summary_dataframe()
            display(df_summary)

            display(HTML("""
            <div style="font-size: 0.85em; color: #6c757d; margin-top: 6px;">
                <b>Notice:</b> Model scores are automated algorithmic approximations and NOT human grades.<br>
                <b>System Observations:</b> Derived strictly from structural relations, coverage, and entailment metrics computed by Base ASAG.
            </div>
            """))

        # Automatically inspect the first answer
        self.inspect_selected_answer()

    def inspect_selected_answer(self):
        """Render the complete 11-part diagnostic inspection for the selected answer."""
        with self.out_inspector:
            clear_output(wait=True)

            if not self.current_batch or not self.current_batch.records:
                print("No results to inspect. Click [ RUN ALL ANSWERS ] first.")
                return

            target_id = self.w_inspect_dropdown.value
            target_rec = next((r for r in self.current_batch.records if r.answer_id == target_id), None)

            if not target_rec:
                print(f"Record for '{target_id}' not found.")
                return

            p_res = target_rec.pipeline_result

            # 1. Answer Overview Header
            header_html = f"""
            <div style="background: #e9ecef; padding: 12px 16px; border-radius: 6px; margin: 8px 0;">
                <h3 style="margin: 0 0 6px 0; color: #212529;">Detailed Analysis: {target_rec.answer_id}</h3>
                <p style="margin: 0; font-size: 1.05em;"><b>Student Answer:</b> <i>"{target_rec.student_answer}"</i></p>
            </div>
            """
            display(HTML(header_html))

            # 2. Score & Proposition Metric Summary
            score_summary = pd.DataFrame([
                {"Metric": "TF-IDF Cosine Baseline (Sys 1)", "Value": f"{target_rec.tfidf_score:.4f}"},
                {"Metric": "Base ASAG Normalized Score (Sys 2)", "Value": f"{target_rec.base_asag_score:.4f}"},
                {"Metric": "Base ASAG Scaled (5.0 Scale)", "Value": f"{p_res.scale_score(5.0):.2f} / 5.00"},
                {"Metric": "Optional Letter Grade", "Value": p_res.map_to_letter_grade()},
                {"Metric": "Total Reference Propositions", "Value": p_res.total_reference_propositions},
                {"Metric": "Matched Proposition Pairs", "Value": target_rec.matched_count},
                {"Metric": "Entailed Propositions (Full 1.0 Credit)", "Value": target_rec.entails_count},
                {"Metric": "Uncertain Propositions (Partial 0.5 Credit)", "Value": target_rec.uncertain_count},
                {"Metric": "Contradicted Propositions (Zero 0.0 Credit)", "Value": target_rec.contradicts_count},
                {"Metric": "Missing Reference Propositions (Zero 0.0 Credit)", "Value": target_rec.missing_reference_count},
                {"Metric": "Unmatched Student Relations (Neutral 0.00 Effect)", "Value": target_rec.unmatched_student_count},
                {"Metric": "System Observation", "Value": target_rec.system_observation},
            ])
            display(HTML("<h4>1. Scores & Evaluation Summary</h4>"))
            display(score_summary)

            # 3. Itemized Proposition Score Contribution
            display(HTML("<h4>2. Reference Proposition Coverage & Score Contributions</h4>"))
            df_contrib = format_score_contributions_table(p_res)
            display(df_contrib if not df_contrib.empty else "No reference propositions.")

            # 4. VISUALLY PROMINENT UNMATCHED STUDENT INFORMATION
            unmatched_stu_banner = """
            <div style="background-color: #fff3cd; border: 2px solid #ffeeba; border-left: 6px solid #ffc107; padding: 14px 18px; margin: 16px 0; border-radius: 6px;">
                <h3 style="margin: 0 0 6px 0; color: #856404; text-transform: uppercase; letter-spacing: 0.5px;">
                    ⚠ UNMATCHED STUDENT INFORMATION
                </h3>
                <div style="color: #856404; font-size: 0.95em; line-height: 1.5;">
                    <b>Classification Status:</b> <span style="background: #e2e3e5; padding: 2px 6px; border-radius: 3px; font-weight: bold;">NOT EVALUATED BY BASE ASAG</span><br>
                    <b>Base ASAG Score Effect:</b> <span style="font-weight: bold; color: #495057;">0.00 (Strictly Neutral — Neither Bonus nor Penalty)</span><br>
                    <i>This extra propositional information was detected in the student answer but has no counterpart in the reference answer. Base ASAG currently ignores unmatched student statements during scoring. The proposed extension (Stages 11–14) will investigate whether evaluating this information improves agreement with human grades.</i>
                </div>
            </div>
            """
            display(HTML(unmatched_stu_banner))

            df_unmatched_stu = format_unmatched_student_table(p_res)
            if not df_unmatched_stu.empty:
                display(df_unmatched_stu)
            else:
                display(HTML("<p><i>No unmatched student propositions were detected for this answer.</i></p>"))

            # 5. Semantic Matching Evidence
            display(HTML("<h4>3. Role-Preserving Semantic Alignment (Stage 7)</h4>"))
            df_matched = format_semantic_matching_table(p_res)
            display(df_matched if not df_matched.empty else "No relations met the alignment threshold (0.50).")

            # 6. Entailment Decisions & Polarity Evidence
            display(HTML("<h4>4. Textual Entailment Decisions & Polarity Evidence (Stage 8)</h4>"))
            df_entail = format_entailment_table(p_res)
            display(df_entail if not df_entail.empty else "No propositions evaluated for entailment.")

            # 7. Unmatched Reference Information (Omissions)
            display(HTML("<h4>5. Unmatched Reference Information (Missing from Student Answer)</h4>"))
            df_unmatched_ref = format_unmatched_reference_table(p_res)
            display(df_unmatched_ref if not df_unmatched_ref.empty else "All reference propositions were addressed by the student.")

            # 8. Canonical Relational Triples (Stage 5)
            display(HTML("<h4>6. Canonical Relational Triples (Stage 5 SPO / SP Structures)</h4>"))
            rel_tables = format_dependency_relations_tables(p_res)
            display(HTML("<b>Reference Triples:</b>"))
            display(rel_tables["reference_relations"])
            display(HTML("<b>Student Triples:</b>"))
            display(rel_tables["student_relations"])

            # 9. Preprocessed Tokens & Linguistic Annotations (Stage 3 & 4)
            display(HTML("<h4>7. Linguistic Preprocessing & Dependency Tokens (Stages 3 & 4)</h4>"))
            prep_tables = format_preprocessing_tables(p_res)
            display(HTML("<b>Reference Tokens:</b>"))
            display(prep_tables["reference_tokens"])
            display(HTML("<b>Student Tokens:</b>"))
            display(prep_tables["student_tokens"])

    def export_results(self):
        """Export structured results of the current batch to CSV."""
        with self.out_export_msg:
            clear_output(wait=True)
            if not self.current_batch or not self.current_batch.records:
                display(HTML("<div style='color: red;'>No batch results available to export. Run all answers first.</div>"))
                return

            export_dir = PROJECT_ROOT / "data" / "demo"
            export_path = export_dir / "asag_lab_results.csv"

            self.current_batch.export_csv(export_path)
            success_html = f"""
            <div style="background: #d1e7dd; border-left: 5px solid #198754; color: #0f5132; padding: 10px 14px; border-radius: 4px; margin: 8px 0;">
                <b>Export Successful!</b> Saved {len(self.current_batch.records)} records to: <code>{export_path}</code>
            </div>
            """
            display(HTML(success_html))

    def render(self):
        """Render the complete interactive laboratory interface."""
        top_banner = """
        <div style="background: #1e293b; color: #f8fafc; padding: 18px 24px; border-radius: 8px; margin-bottom: 14px;">
            <h2 style="margin: 0 0 6px 0; color: #38bdf8; font-size: 1.6em;">ASAG EXPERIMENT LAB</h2>
            <div style="font-size: 0.95em; color: #cbd5e1; line-height: 1.5;">
                Interactive research workbench for classical Automated Short Answer Grading.<br>
                <b>System 1:</b> TF-IDF Cosine Baseline &nbsp;|&nbsp; <b>System 2:</b> Base ASAG Pipeline (Stages 3–10)
            </div>
        </div>
        """

        research_boundary_notice = """
        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 5px solid #64748b; padding: 10px 16px; margin: 10px 0; border-radius: 4px; font-size: 0.9em; color: #334155;">
            <b>CURRENT BASE ASAG RESEARCH BOUNDARY:</b><br>
            Unmatched student information is detected and preserved in diagnostics, but is <b>not classified</b>.<br>
            Categories such as <i>Correct Additional</i>, <i>Irrelevant Additional</i>, and <i>Incorrect Additional</i> are currently <b>NOT EVALUATED</b> (Score Effect = 0.00).<br>
            This is intentional and establishes the foundational baseline before the proposed proposition-level extension (Stages 11–14).
        </div>
        """

        manage_buttons = widgets.HBox([
            self.btn_add_answer,
            self.btn_remove_answer,
            self.btn_reset_demo,
            self.btn_clear_to_three,
        ], layout=widgets.Layout(margin="6px 0 10px 0"))

        action_buttons = widgets.HBox([
            self.btn_run_all,
            self.btn_export,
        ], layout=widgets.Layout(margin="10px 0"))

        inspector_controls = widgets.HBox([
            self.w_inspect_dropdown,
            self.btn_inspect,
        ], layout=widgets.Layout(margin="12px 0 6px 0"))

        main_ui = widgets.VBox([
            widgets.HTML(top_banner),
            widgets.HTML(research_boundary_notice),
            widgets.HTML("<hr style='margin: 12px 0;'>"),
            self.w_exp_name,
            self.w_question,
            self.w_reference,
            widgets.HTML("<h4 style='margin: 14px 0 6px 0;'>Student Answers to Evaluate:</h4>"),
            manage_buttons,
            self.answers_box,
            widgets.HTML("<hr style='margin: 14px 0;'>"),
            action_buttons,
            self.out_export_msg,
            self.out_summary,
            widgets.HTML("<hr style='margin: 16px 0;'>"),
            widgets.HTML("<h3 style='margin: 0 0 6px 0;'>Answer Inspector</h3>"),
            widgets.HTML("<p style='margin: 0 0 8px 0; font-size: 0.9em; color: #64748b;'>Select any student answer below to inspect its complete internal ASAG representation and diagnostic trace.</p>"),
            inspector_controls,
            self.out_inspector,
        ], layout=widgets.Layout(width="100%"))

        return main_ui


def launch_asag_lab():
    """
    Primary one-cell entry point to launch the ASAG Experiment Laboratory.
    """
    if HAS_WIDGETS:
        lab = ASAGLabInterface()
        display(lab.render())
        # Automatically run once so default demonstration results are immediately visible
        lab.run_all()
    else:
        # Fallback for environments lacking ipywidgets
        print("ipywidgets is not installed. Running in non-widget batch mode:")
        pipeline = BaseASAGPipeline()
        tfidf = TfidfCosineBaseline()

        records = []
        for i, ans in enumerate(DEFAULT_DEMO_ANSWERS, start=1):
            t_score = tfidf.similarity(DEFAULT_REFERENCE, ans)
            p_res = pipeline.grade(DEFAULT_QUESTION, DEFAULT_REFERENCE, ans)
            obs = derive_system_observation(p_res)
            records.append(SingleEvaluationRecord(
                answer_id=f"Answer {i}",
                student_answer=ans,
                tfidf_score=t_score,
                base_asag_score=p_res.normalized_score,
                matched_count=len(p_res.matched_relations),
                missing_reference_count=len(p_res.unmatched_reference_relations),
                unmatched_student_count=p_res.unmatched_student_count,
                entails_count=p_res.entailed_count,
                uncertain_count=p_res.uncertain_count,
                contradicts_count=p_res.contradicted_count,
                system_observation=obs,
                pipeline_result=p_res,
            ))

        batch = BatchEvaluationResult(
            experiment_name=DEFAULT_EXPERIMENT_NAME,
            question=DEFAULT_QUESTION,
            reference_answer=DEFAULT_REFERENCE,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            records=records,
        )
        display(batch.to_summary_dataframe())
