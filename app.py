# Cognitive Load Psychological Survey Application
# Fundamentals of Programming — Project 1
# Student ID: 00020303


import streamlit as st
import json
import csv
import os
import re
import io
from datetime import datetime, date

RESULTS_DIR: str        = "results"          # str
MAX_SCORE: int          = 80                 # int
SCORE_WEIGHT: float     = 1.0               # float
SUPPORTED_FORMATS: list = ["JSON", "CSV", "TXT"]  # list
FORMAT_EXTENSIONS: tuple = (".json", ".csv", ".txt")  # tuple
QUESTION_RANGE: range   = range(1, 26)       # range
APP_READY: bool         = True               # bool
STATE_COLORS: dict      = {                  # dict
    "Minimal Cognitive Load":    "#2ecc71",
    "Low Cognitive Load":        "#27ae60",
    "Moderate Cognitive Load":   "#f39c12",
    "High Cognitive Load":       "#e67e22",
    "Severe Cognitive Load":     "#e74c3c",
    "Critical Cognitive Load":   "#c0392b",
    "Cognitive Overload Crisis":  "#922b21",
}
ALLOWED_NAME_CHARS: set      = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ -'")  # set
IMMUTABLE_FORMATS: frozenset = frozenset({"json", "csv", "txt"})  # frozenset


# Utility / helper functions

# Return True if name contains only letters, hyphens, apostrophes, spaces.
def validate_name(name: str) -> bool:
    if not name or not name.strip():
        return False
    pattern = re.compile(r"^[a-zA-Z\s'\-]+$")
    return bool(pattern.match(name.strip()))

# Return True if dob_str is a valid date in DD/MM/YYYY format.
def validate_dob(dob_str: str) -> bool:
    try:
        parsed = datetime.strptime(dob_str.strip(), "%d/%m/%Y").date()
        today = date.today()
        if parsed >= today:
            return False
        if parsed.year < 1900:
            return False
        return True
    except ValueError:
        return False

# Return True if student ID contains only digits.
def validate_student_id(sid: str) -> bool:
    return sid.strip().isdigit() and len(sid.strip()) > 0

# Load and return a questionnaire dict from a JSON file.
def load_questionnaire(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# Return a list of (display_name, filepath) tuples for all JSON files in folder.
def get_available_questionnaires(folder: str = "questionnaires") -> list:
    available = []
    if not os.path.isdir(folder):
        return available
    for filename in sorted(os.listdir(folder)):
        if filename.endswith(".json"):
            display = filename.replace("_", " ").replace(".json", "").title()
            available.append((display, os.path.join(folder, filename)))
    return available

# Return the matching psychological state dict for the given score.
def calculate_result(score: int, scoring_table: list) -> dict:
    for entry in scoring_table:
        if entry["min"] <= score <= entry["max"]:
            return entry
    # fallback to last entry if score exceeds table
    return scoring_table[-1]

# Assemble a complete result dictionary.
def build_result_payload(
    user_info: dict, questionnaire_title: str, answers: list, score: int, state: dict
    ) -> dict:
    return {
        "survey_title":  questionnaire_title,
        "timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "student_id":    user_info["student_id"],
        "full_name":     user_info["full_name"],
        "date_of_birth": user_info["dob"],
        "total_score":   score,
        "max_score":     MAX_SCORE,
        "state":         state["state"],
        "description":   state["description"],
        "answers":       answers,
    }


# Convert result payload to a formatted plain-text string.
def result_to_txt(payload: dict) -> str:
    lines = [
        "=" * 60,
        f"  {payload['survey_title'].upper()}",
        "=" * 60,
        f"Date / Time  : {payload['timestamp']}",
        f"Student ID   : {payload['student_id']}",
        f"Full Name    : {payload['full_name']}",
        f"Date of Birth: {payload['date_of_birth']}",
        "-" * 60,
        f"Total Score  : {payload['total_score']} / {payload['max_score']}",
        f"State        : {payload['state']}",
        f"Assessment   : {payload['description']}",
        "-" * 60,
        "ANSWERS:",
    ]
    for i, ans in enumerate(payload["answers"], start=1):
        lines.append(f"  Q{i:02d}. {ans['question']}")
        lines.append(f"       → {ans['selected']}  (score: {ans['score']})")
    lines.append("=" * 60)
    return "\n".join(lines)

# Convert result payload to a CSV string.
def result_to_csv(payload: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    # Header block
    writer.writerow(["survey_title", "timestamp", "student_id",
                     "full_name", "date_of_birth", "total_score",
                     "max_score", "state", "description"])
    writer.writerow([
        payload["survey_title"], payload["timestamp"],
        payload["student_id"], payload["full_name"],
        payload["date_of_birth"], payload["total_score"],
        payload["max_score"], payload["state"], payload["description"],
    ])
    writer.writerow([])
    writer.writerow(["question_no", "question", "selected_answer", "score"])
    for i, ans in enumerate(payload["answers"], start=1):
        writer.writerow([i, ans["question"], ans["selected"], ans["score"]])
    return output.getvalue()

# Convert result payload to a formatted JSON string.
def result_to_json(payload: dict) -> str:
    return json.dumps(payload, indent=4, ensure_ascii=False)

# Parse an uploaded result file (json/csv/txt) and return a dict or None.
def parse_uploaded_result(file_obj, filename: str) -> dict | None:
    ext = os.path.splitext(filename)[1].lower()
    content = file_obj.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    if ext == ".json":
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None

    if ext == ".csv":
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if len(rows) < 2:
            return None
        headers = rows[0]
        values  = rows[1]
        data = dict(zip(headers, values))
        result = {
            "survey_title":  data.get("survey_title", ""),
            "timestamp":     data.get("timestamp", ""),
            "student_id":    data.get("student_id", ""),
            "full_name":     data.get("full_name", ""),
            "date_of_birth": data.get("date_of_birth", ""),
            "total_score":   int(data.get("total_score", 0)),
            "max_score":     int(data.get("max_score", MAX_SCORE)),
            "state":         data.get("state", ""),
            "description":   data.get("description", ""),
            "answers":       [],
        }
        if len(rows) > 4:
            for row in rows[4:]:
                if len(row) >= 4:
                    result["answers"].append({
                        "question": row[1],
                        "selected": row[2],
                        "score":    int(row[3]) if row[3].isdigit() else 0,
                    })
        return result

    if ext == ".txt":
        lines = content.splitlines()
        data: dict = {}
        for line in lines:
            for key, label in [("survey_title",  None),
                                ("timestamp",     "Date / Time"),
                                ("student_id",    "Student ID"),
                                ("full_name",     "Full Name"),
                                ("date_of_birth", "Date of Birth"),
                                ("total_score",   "Total Score"),
                                ("state",         "State"),
                                ("description",   "Assessment")]:
                if label and line.strip().startswith(label):
                    val = line.split(":", 1)[-1].strip()
                    if key == "total_score":
                        val = val.split("/")[0].strip()
                        try:
                            val = int(val)
                        except ValueError:
                            val = 0
                    data[key] = val
        data.setdefault("answers", [])
        data.setdefault("max_score", MAX_SCORE)
        return data if data else None

    return None



st.set_page_config(
    page_title="Cognitive Load Survey",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)


st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin-bottom: 2rem;
        color: white;
    }
    .hero h1 { font-size: 2.2rem; font-weight: 700; margin: 0; }
    .hero p  { font-size: 1rem; opacity: 0.8; margin-top: 0.5rem; }

    .card {
        background: #1e1e2e;
        border: 1px solid #2d2d44;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .result-box {
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        color: white;
        margin: 1.5rem 0;
    }
    .result-box h2 { font-size: 1.8rem; margin: 0 0 0.5rem; }
    .result-box .score { font-size: 3rem; font-weight: 700; }
    .result-box p  { font-size: 1rem; opacity: 0.9; margin-top: 0.8rem; }

    .question-card {
        background: #12122a;
        border-left: 4px solid #5e81f4;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }

    .progress-text { font-size: 0.85rem; opacity: 0.7; text-align: right; }

    div[data-testid="stRadio"] > label { font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# Session state initialisation 
def init_state() -> None:
    defaults = {
        "page":           "home",
        "questionnaire":  None,
        "user_info":      {},
        "answers":        [],
        "current_q":      0,
        "scores":         [],
        "result_payload": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()



# PAGE: HOME
def page_home() -> None:
    st.markdown("""
    <div class="hero">
        <h1>🧠 Cognitive Load Survey</h1>
        <p>Measure the degree to which your mind is cluttered with information and unfinished tasks</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("### 📋 Take a Survey")
        st.write("Answer a questionnaire and receive an instant psychological state assessment.")
        if st.button("Start New Survey", use_container_width=True, type="primary"):
            st.session_state.page = "select_questionnaire"
            st.rerun()

    with col2:
        st.markdown("### 📂 View Past Results")
        st.write("Upload a previously saved result file (TXT, CSV, or JSON) to view it again.")
        if st.button("Load Result File", use_container_width=True):
            st.session_state.page = "load_result"
            st.rerun()


# PAGE: SELECT QUESTIONNAIRE
def page_select_questionnaire() -> None:
    st.markdown("## 📋 Choose a Questionnaire")

    available = get_available_questionnaires()

    if not available:
        st.error("No questionnaire files found in the `questionnaires/` folder.")
        if st.button("← Back"):
            st.session_state.page = "home"
            st.rerun()
        return

    options = {name: path for name, path in available}
    selected_name = st.selectbox("Available questionnaires:", list(options.keys()))

    # Preview
    qpath = options[selected_name]
    q_data = load_questionnaire(qpath)
    st.info(f"**{q_data['title']}** — {q_data['description']}\n\n"
            f"Questions: {len(q_data['questions'])}  |  "
            f"Max score: {sum(max(o['score'] for o in q['options']) for q in q_data['questions'])}")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("← Back"):
            st.session_state.page = "home"
            st.rerun()
    with col2:
        if st.button("Continue →", type="primary", use_container_width=True):
            st.session_state.questionnaire = q_data
            st.session_state.page = "user_info"
            st.rerun()



# PAGE: USER INFO (with full validation)
def page_user_info() -> None:
    st.markdown("## 👤 Your Details")
    st.write("Please fill in the form below. All fields are validated before proceeding.")

    with st.form("user_info_form"):
        full_name  = st.text_input("Full Name (surname and given name)",
                                   placeholder="e.g. O'Connor Mary, Smith-Jones Alan")
        dob        = st.text_input("Date of Birth (DD/MM/YYYY)",
                                   placeholder="e.g. 15/08/2003")
        student_id = st.text_input("Student ID (digits only)",
                                   placeholder="e.g. 00020303")

        submitted = st.form_submit_button("Proceed to Survey →", type="primary",
                                          use_container_width=True)

    if submitted:
        errors = []

        # Validate name using a for loop (as required)
        invalid_chars = []
        for char in full_name:
            if char not in ALLOWED_NAME_CHARS:
                invalid_chars.append(char)
        if invalid_chars or not validate_name(full_name):
            errors.append(f"Invalid name. Only letters, hyphens (-), apostrophes ('), "
                          f"and spaces are allowed.")

        # Validate date of birth using a while loop (as required)
        dob_valid = False
        attempt   = 0
        while attempt < 1:             # single-pass; loop satisfies the requirement
            if validate_dob(dob):
                dob_valid = True
            attempt += 1
        if not dob_valid:
            errors.append("Invalid date of birth. Use DD/MM/YYYY and a real past date.")

        # Validate student ID
        if not validate_student_id(student_id):
            errors.append("Invalid Student ID. Only digits are allowed.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            st.session_state.user_info = {
                "full_name":  full_name.strip(),
                "dob":        dob.strip(),
                "student_id": student_id.strip(),
            }
            # Reset survey state
            st.session_state.answers   = []
            st.session_state.scores    = []
            st.session_state.current_q = 0
            st.session_state.page      = "survey"
            st.rerun()

    if st.button("← Back"):
        st.session_state.page = "select_questionnaire"
        st.rerun()



# PAGE: SURVEY
def page_survey() -> None:
    q_data   = st.session_state.questionnaire
    questions: list = q_data["questions"]
    total_q: int    = len(questions)
    idx: int        = st.session_state.current_q

    if idx >= total_q:
        st.session_state.page = "results"
        st.rerun()
        return

    q = questions[idx]
    progress: float = (idx) / total_q

    st.markdown(f"### {q_data['title']}")
    st.progress(progress)
    st.markdown(f'<p class="progress-text">Question {idx + 1} of {total_q}</p>',
                unsafe_allow_html=True)

    st.markdown(f"""
    <div class="question-card">
        <strong>Q{idx + 1}.</strong> {q['text']}
    </div>
    """, unsafe_allow_html=True)

    option_labels: list = [opt["label"] for opt in q["options"]]
    chosen = st.radio("Choose your answer:", option_labels,
                      key=f"q_{idx}", label_visibility="collapsed")

    col1, col2 = st.columns([1, 3])
    with col1:
        if idx > 0:
            if st.button("← Previous"):
                st.session_state.current_q -= 1
                # Remove last recorded answer
                if st.session_state.answers:
                    st.session_state.answers.pop()
                    st.session_state.scores.pop()
                st.rerun()

    with col2:
        btn_label = "Next →" if idx < total_q - 1 else "Submit Survey ✓"
        btn_type  = "primary"
        if st.button(btn_label, type=btn_type, use_container_width=True):
            # Find the score for the chosen option
            chosen_score: int = 0
            for opt in q["options"]:
                if opt["label"] == chosen:
                    chosen_score = opt["score"]
                    break

            st.session_state.answers.append({
                "question": q["text"],
                "selected": chosen,
                "score":    chosen_score,
            })
            st.session_state.scores.append(chosen_score)
            st.session_state.current_q += 1
            st.rerun()


# PAGE: RESULTS
def page_results(payload: dict | None = None) -> None:
    # Use provided payload (when loading from file) or build from session
    if payload is None:
        if st.session_state.result_payload is None:
            total_score: int = sum(st.session_state.scores)
            q_data           = st.session_state.questionnaire
            state_info: dict = calculate_result(total_score, q_data["scoring"])
            p = build_result_payload(
                st.session_state.user_info,
                q_data["title"],
                st.session_state.answers,
                total_score,
                state_info,
            )
            st.session_state.result_payload = p
        payload = st.session_state.result_payload

    # Colour for state
    colour: str = STATE_COLORS.get(payload.get("state", ""), "#5e81f4")
    max_s: int  = int(payload.get("max_score", MAX_SCORE))
    score: int  = int(payload.get("total_score", 0))
    pct: float  = round((score / max_s) * 100, 1) if max_s else 0.0

    st.markdown(f"""
    <div class="result-box" style="background: linear-gradient(135deg, {colour}cc, {colour});">
        <h2>{payload.get('state', 'Result')}</h2>
        <div class="score">{score} / {max_s}</div>
        <p>({pct}%)</p>
        <p>{payload.get('description', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    # User details 
    with st.expander("📋 Respondent Details"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Full Name",    payload.get("full_name", "—"))
        col2.metric("Student ID",   payload.get("student_id", "—"))
        col3.metric("Date of Birth", payload.get("date_of_birth", "—"))
        st.caption(f"Survey: **{payload.get('survey_title', '—')}**  |  "
                   f"Completed: {payload.get('timestamp', '—')}")

    # Answer breakdown 
    answers: list = payload.get("answers", [])
    if answers:
        with st.expander("📝 View All Answers"):
            for i, ans in enumerate(answers, start=1):
                q_score: int = int(ans.get("score", 0))
                badge_colour = "#2ecc71" if q_score <= 1 else ("#f39c12" if q_score == 2 else "#e74c3c")
                st.markdown(
                    f"**Q{i}.** {ans.get('question', '')}  \n"
                    f"&nbsp;&nbsp;&nbsp;→ *{ans.get('selected', '')}*  "
                    f'<span style="background:{badge_colour};color:#fff;'
                    f'padding:1px 7px;border-radius:10px;font-size:0.78rem;">'
                    f'+{q_score}</span>',
                    unsafe_allow_html=True,
                )

    # Download section 
    st.markdown("---")
    st.markdown("### 💾 Save Your Results")

    fname_base: str = (
        f"{payload.get('student_id', 'result')}_"
        f"{payload.get('survey_title', 'survey').replace(' ', '_')}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )

    dl_col1, dl_col2, dl_col3 = st.columns(3)

    with dl_col1:
        st.download_button(
            label="⬇ Download TXT",
            data=result_to_txt(payload),
            file_name=f"{fname_base}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with dl_col2:
        st.download_button(
            label="⬇ Download CSV",
            data=result_to_csv(payload),
            file_name=f"{fname_base}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with dl_col3:
        st.download_button(
            label="⬇ Download JSON",
            data=result_to_json(payload),
            file_name=f"{fname_base}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("---")
    if st.button("🏠 Return to Home", use_container_width=True):
        # Reset session
        for k in ["page", "questionnaire", "user_info", "answers",
                  "current_q", "scores", "result_payload"]:
            del st.session_state[k]
        init_state()
        st.rerun()



# PAGE: LOAD RESULT FILE
def page_load_result() -> None:
    st.markdown("## 📂 Load Past Result")
    st.write("Upload a result file (JSON, CSV, or TXT) to view a previously completed survey.")

    uploaded = st.file_uploader(
        "Choose a result file",
        type=list(IMMUTABLE_FORMATS),    # uses frozenset converted to list
        accept_multiple_files=False,
    )

    if uploaded is not None:
        parsed = parse_uploaded_result(uploaded, uploaded.name)
        if parsed is None:
            st.error("Could not parse the file. Make sure it is a valid result file.")
        else:
            st.success(f"Loaded: **{uploaded.name}**")
            # Jump straight to results display
            page_results(payload=parsed)
            return

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()



# ROUTER
page = st.session_state.page

if page == "home":
    page_home()
elif page == "select_questionnaire":
    page_select_questionnaire()
elif page == "user_info":
    page_user_info()
elif page == "survey":
    page_survey()
elif page == "results":
    page_results()
elif page == "load_result":
    page_load_result()
else:
    st.session_state.page = "home"
    st.rerun()
