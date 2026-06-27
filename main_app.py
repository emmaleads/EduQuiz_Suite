import io
import re
import pandas as pd
import streamlit as st
from docx import Document

# --- Global Page Configuration ---
st.set_page_config(
    page_title="EduQuiz Assessment Suite", page_icon="🎛️", layout="wide"
)


# =========================================================================
# CORE PROCESSING UTILITIES (Shared Logic)
# =========================================================================
def convert_plain_text_to_html_chem(text):
    """Scans raw strings via Regex to convert plain chemistry notation into HTML formatting.

    Handles chemical formulas, molecular layouts, ionic charges, and electron
    configurations.
    """
    if not text:
        return ""
    # 1. Convert charges (e.g., Zn2+ -> Zn<sup>2+</sup>, Cl- -> Cl<sup>-</sup>)
    text = re.sub(r"([A-Za-z\s\]])(\d*[\+\-])", r"\1<sup>\2</sup>", text)
    # 2. Convert subscripts (e.g., NH3 -> NH<sub>3</sub>, N2O5 -> N<sub>2</sub>O<sub>5</sub>)
    text = re.sub(r"([A-Za-z\)])(\d+)", r"\1<sub>\2</sub>", text)
    # 3. Correct electron configurations (e.g., 4s2 -> 4s<sup>2</sup>)
    text = re.sub(r"([sspdf])<sub>(\d+)</sub>", r"\1<sup>\2</sup>", text)
    # 4. Standardize spacing around operators in structural formulas (e.g., H2C=CH2)
    text = re.sub(r"(=|＋|\+)\s*([A-Za-z])", r"\1 \2", text)
    return text


def text_to_html_chem(paragraph):
    """Combines explicit Microsoft Word sub/superscript styling tracking

    with regex fallback patterns to ensure complete rich text conversion.
    """
    html_text = ""
    for run in paragraph.runs:
        if not run.text:
            continue
        if run.font.subscript:
            html_text += f"<sub>{run.text}</sub>"
        elif run.font.superscript:
            html_text += f"<sup>{run.text}</sup>"
        else:
            html_text += convert_plain_text_to_html_chem(run.text)
    return convert_plain_text_to_html_chem(html_text).strip()


def parse_docx_to_quiz(file_stream):
    """Processes document paragraphs using an anchor-based block state machine.

    Groups content dynamically using 'Ans:' as a delimiter row.
    """
    doc = Document(file_stream)
    raw_lines = []

    for p in doc.paragraphs:
        converted_text = text_to_html_chem(p)
        if converted_text:
            # Skip common standalone title headers
            if converted_text.lower() in ["questions", "question", "quiz"]:
                continue
            raw_lines.append(converted_text)

    questions_data = []
    idx = 0

    while idx < len(raw_lines):
        ans_idx = -1
        # Scan ahead locally to find the bounding answer row
        for j in range(idx, min(idx + 10, len(raw_lines))):
            if "ans:" in raw_lines[j].lower():
                ans_idx = j
                break

        if ans_idx != -1:
            # Cleanly isolate the correct answer string value
            correct_ans = (
                raw_lines[ans_idx]
                .replace("Ans:", "")
                .replace("ans:", "")
                .strip()
            )

            # Sift out the preceding content elements within this block
            block_elements = raw_lines[idx:ans_idx]

            if len(block_elements) >= 5:
                # The final 4 elements are the options
                options = block_elements[-4:]
                # Any trailing blocks above the options are combined into the single question string
                question_text = " ".join(block_elements[:-4])

                # Strips away any hardcoded leading numerals (e.g., "1. What is...")
                question_text = re.sub(r"^\d+\.\s*", "", question_text)

                questions_data.append(
                    [
                        question_text,
                        options[0],
                        options[1],
                        options[2],
                        options[3],
                        correct_ans,
                    ]
                )
            idx = ans_idx + 1
        else:
            idx += 1

    return questions_data


# =========================================================================
# SYSTEM APPLICATION NAVIGATION (Sidebar Panel)
# =========================================================================
st.sidebar.title("🎛️ Navigation Portal")
st.sidebar.write("Switch between tools independently:")
app_mode = st.sidebar.radio(
    "Go To:",
    ["🏠 Home Dashboard", "🧪 Word-to-Excel Parser", "📝 Exam Simulator"],
)


# =========================================================================
# MODULE 1: UNIVERSAL ASSESSMENT PORTAL DASHBOARD
# =========================================================================
if app_mode == "🏠 Home Dashboard":
    st.title("🔬 EduQuiz Multi-Department Assessment Suite")
    st.write(
        "Welcome! This unified ecosystem allows faculty members across all departments to process document files and run interactive mock examinations seamlessly."
    )

    st.markdown(
        """
    ---
    ### Available Software Sub-modules:
    
    1. **🧪 Word-to-Excel Parser:**
       * Upload raw text `.docx` documents containing questions, optional arrays, and answer parameters.
       * Automatically catches and converts chemistry formulas (like subscripts, valencies, subshell configurations) into standard HTML symbols.
       * Generates an structured tabular file layout available for direct spreadsheet download.
       
    2. **📝 Exam Simulator Workspace:**
       * Upload processed database spreadsheet sheets directly.
       * Renders complex mathematical indexes and subscripts natively on user screens without raw HTML tag clutter.
       * Features sandbox progress tracking, submission grading, error evaluation flags, and automated final metric dashboards.
    """
    )


# =========================================================================
# MODULE 2: ASSESSMENT PARSER SYSTEM (Word -> Excel Matrix)
# =========================================================================
elif app_mode == "🧪 Word-to-Excel Parser":
    st.title("🧪 Word to Excel Quiz Converter")
    st.write(
        "Upload any standard `.docx` document file. The engine will run a complete layout pass, translate chemical values into HTML, and produce a structural spreadsheet package."
    )

    uploaded_file = st.file_uploader(
        "Choose a Word (.docx) file", type=["docx"], key="parser_upload"
    )

    if uploaded_file is not None:
        try:
            with st.spinner("Analyzing document mapping architecture..."):
                quiz_data = parse_docx_to_quiz(uploaded_file)

            if quiz_data:
                columns = [
                    "Question",
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D",
                    "Correct Answer",
                ]
                df = pd.DataFrame(quiz_data, columns=columns)

                st.success(
                    f"🎉 Complete! Successfully structured {len(df)} questions from the document layout."
                )

                st.subheader("Data Matrix Preview")
                st.dataframe(df, use_container_width=True)

                # Export parsing array matrix directly to download memory buffer
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Quiz Questions")

                st.markdown(" ")
                st.download_button(
                    label="📥 Download Structured Excel File",
                    data=buffer.getvalue(),
                    file_name="converted_assessment_matrix.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.warning(
                    "Parsing Check Failure: No text blocks matched the standard question framework. Verify document syntax."
                )
        except Exception as e:
            st.error(f"Processing Failure: {e}")


# =========================================================================
# MODULE 3: EXAMINATION SIMULATION PLATFORM (Excel Reader + UI Renders)
# =========================================================================
elif app_mode == "📝 Exam Simulator":
    st.title("📝 Multi-Department Exam Simulator")
    st.write(
        "Upload a previously compiled Excel question sheet. The student terminal interface will render clean rich text components without raw string markup."
    )

    uploaded_file = st.file_uploader(
        "Upload Quiz Excel File", type=["xlsx"], key="exam_upload"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            required_cols = [
                "Question",
                "Option A",
                "Option B",
                "Option C",
                "Option D",
                "Correct Answer",
            ]

            if not all(col in df.columns for col in required_cols):
                st.error(
                    "Invalid Spreadsheet Framework: The uploaded file is missing standard header columns."
                )
                st.stop()

            # Initialize isolated state vectors for individual user sandbox runs
            if "current_index" not in st.session_state:
                st.session_state.current_index = 0
                st.session_state.score = 0
                st.session_state.answers_submitted = {}

            total_questions = len(df)

            # Header Progress bar display configurations
            progress_ratio = (st.session_state.current_index) / total_questions
            st.progress(progress_ratio)
            st.write(
                f"**Question {st.session_state.current_index + 1} of {total_questions}** | Running Score Dashboard: **{st.session_state.score}/{total_questions}**"
            )

            current_idx = st.session_state.current_index
            row = df.iloc[current_idx]

            st.markdown("---")

            # Native clean interface presentation using HTML rendering switches
            st.markdown(
                f"### **Question:** {row['Question']}",
                unsafe_allow_html=True,
            )
            st.markdown(f"**A.** {row['Option A']}", unsafe_allow_html=True)
            st.markdown(f"**B.** {row['Option B']}", unsafe_allow_html=True)
            st.markdown(f"**C.** {row['Option C']}", unsafe_allow_html=True)
            st.markdown(f"**D.** {row['Option D']}", unsafe_allow_html=True)
            st.markdown(" ")

            choices = ["Select an option...", "A", "B", "C", "D"]
            is_answered = current_idx in st.session_state.answers_submitted

            # Streamlit radio tracking user letters exclusively to avoid messing up widget rendering
            selected_letter = st.radio(
                "**Choose your answer letter:**",
                choices,
                index=0,
                key=f"sel_{current_idx}",
                disabled=is_answered,
                horizontal=True,
            )

            # Dynamic Context Action Buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if not is_answered:
                    submit_disabled = selected_letter == "Select an option..."
                    if st.button(
                        "Submit Answer",
                        use_container_width=True,
                        disabled=submit_disabled,
                    ):
                        st.session_state.answers_submitted[current_idx] = (
                            selected_letter
                        )
                        correct_letter = (
                            str(row["Correct Answer"]).strip().upper()
                        )
                        if selected_letter == correct_letter:
                            st.session_state.score += 1
                        st.rerun()

            # Submission verification layout rendering
            if is_answered:
                user_ans = st.session_state.answers_submitted[current_idx]
                correct_letter = str(row["Correct Answer"]).strip().upper()
                if user_ans == correct_letter:
                    st.success(
                        f"🎉 Correct! The designated answer choice is {correct_letter}."
                    )
                else:
                    st.error(
                        f"❌ Incorrect. Your selection was {user_ans}. The validated answer key is {correct_letter}."
                    )

            # Assessment Navigation Rows
            st.markdown(" ")
            prev_btn, next_btn = st.columns(2)
            with prev_btn:
                if current_idx > 0:
                    if st.button(
                        "⬅️ Previous Question", use_container_width=True
                    ):
                        st.session_state.current_index -= 1
                        st.rerun()
            with next_btn:
                if current_idx < total_questions - 1:
                    if st.button("Next Question ➡️", use_container_width=True):
                        st.session_state.current_index += 1
                        st.rerun()
                else:
                    if (
                        st.button("🏁 Finish Exam", use_container_width=True)
                        and not st.session_state.get("exam_finished", False)
                    ):
                        st.balloons()
                        st.session_state.exam_finished = True
                        st.rerun()

            # Final Summary Report Display Layer
            if st.session_state.get("exam_finished", False):
                st.markdown("---")
                st.header("🏆 Performance Report Card")
                final_percentage = (
                    st.session_state.score / total_questions
                ) * 100
                st.metric(
                    label="Final Grade Scale",
                    value=f"{final_percentage:.1f}%",
                    delta=f"{st.session_state.score} Validated Correct Responses",
                )

                if st.button("🔄 Restart Exam Session", use_container_width=True):
                    del st.session_state.current_index
                    del st.session_state.score
                    del st.session_state.answers_submitted
                    del st.session_state.exam_finished
                    st.rerun()

        except Exception as e:
            st.error(f"Error accessing spreadsheet database parameters: {e}")
