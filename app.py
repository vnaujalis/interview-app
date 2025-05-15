import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv



load_dotenv()  # Load from .env file

# Use st.secrets if running in Streamlit Cloud, fallback to .env locally
api_key = None
try:
    # Try to get the key from Streamlit Cloud
    api_key = st.secrets["OPENAI_API_KEY"]
except st.runtime.secrets.StreamlitSecretNotFoundError:
    # Fallback to local .env file
    api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

# ---- INITIALIZE SESSION STATE ----
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = []
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

# ---- FUNCTION TO GENERATE QUESTIONS ----
def generate_questions(position, difficulty, num_questions):
    prompt = (
        f"Generate {num_questions} {difficulty.lower()} level interview questions "
        f"for the position of {position}. Only return the questions as a numbered list."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are a professional technical interviewer."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()

    return [line.split(". ", 1)[1] for line in content.split("\n") if ". " in line]

# ---- FUNCTION TO GET FEEDBACK ----
def get_feedback(questions, answers):
    qa_list = "\n".join(
        f"{i+1}. Q: {q}\n   A: {a}" for i, (q, a) in enumerate(zip(questions, answers))
    )

    prompt = (
        "You are an expert interview coach.\n\n"
        "I will give you a list of interview questions and my answers.\n"
        "Please provide:\n"
        "1. An executive summary of my performance\n"
        "2. Detailed feedback for each answer\n"
        "3. Recommendations to improve future interviews\n\n"
        f"Questions and Answers:\n{qa_list}"
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        messages=[
            {"role": "system", "content": "You are an expert interview coach."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
# ---- FUNCTION TO CHECK IF THIS IS REAL QUESTION ----
def is_valid_profession(profession):
    prompt = (
        f'Is "{profession}" a real job or profession? '
        'Just answer with Yes or No.'
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    reply = response.choices[0].message.content.strip().lower()
    return "yes" in reply

# ---- PAGE TITLE ----
st.title("🎯 Interview Practice App")

# ---- SETUP FORM ----
if not st.session_state.interview_started:
    with st.form("setup_form"):
        position = st.text_input("Position you're interviewing for:")
        difficulty = st.selectbox("Select difficulty level:", ["Easy", "Medium", "Hard"])
        num_questions = st.slider("How many questions?", 1, 10, 3)
        submitted = st.form_submit_button("Start Interview")

        if submitted and position:
           with st.spinner("Checking position validity..."):
                if is_valid_profession(position):
                    st.session_state.questions = generate_questions(position, difficulty, num_questions)
                    st.session_state.interview_started = True
                    st.session_state.current_question_index = 0
                    st.session_state.answers = [""] * num_questions
                    st.rerun()
                else:
                    st.error(f"❌ Sorry, '{position}' does not appear to be a valid profession. Please enter a real job title.")



    # ---- INTERVIEW IN PROGRESS ----
if st.session_state.interview_started:
    idx = st.session_state.current_question_index
    total = len(st.session_state.questions)

    st.subheader(f"Question {idx + 1} of {total}")
    st.write(st.session_state.questions[idx])

    # 🟩 This is the new answer input block (correctly indented!)
    answer_input = st.text_area(
        label="Your Answer:",
        value=st.session_state.answers[idx],
        key=f"answer_input_{idx}"
    )
    st.session_state.answers[idx] = answer_input

    # Navigation buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Previous", disabled=idx == 0):
            st.session_state.current_question_index -= 1
            st.rerun()

    with col2:
        if idx < total - 1:
            if st.button("Next"):
                st.session_state.current_question_index += 1
                st.rerun()
        else:
            if st.button("Finish Interview"):
                st.success("You've finished all the questions! 🎉 Generating feedback...")

                with st.spinner("Analyzing your answers..."):
                    feedback = get_feedback(st.session_state.questions, st.session_state.answers)

                st.markdown("## 📋 Interview Feedback Summary")
                st.markdown(feedback)

# Re-do button: reset all session state and restart interview
                if st.button("🔄 Re-do Interview"):
                     st.session_state.interview_started = False
                     st.session_state.questions = []
                     st.session_state.answers = []
                     st.session_state.current_question_index = 0
                     st.rerun()

  

