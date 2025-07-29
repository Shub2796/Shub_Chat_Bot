import streamlit as st
import os
from PyPDF2 import PdfReader
import docx
import random
from openai import OpenAI
from PIL import Image

# ---- CONFIG ----
st.set_page_config(page_title="Career Bot", layout="wide")

# ---- BACKGROUND STYLING ----
background_style = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #f2f4f6;
    padding: 2rem;
    border: 2px solid #ccc;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
[data-testid="stHeader"] {
    background-color: rgba(255,255,255,0.5);
}
[data-testid="stSidebar"] {
    background-color: #f9f9f9;
}
</style>
"""
st.markdown(background_style, unsafe_allow_html=True)

st.title("🤖 Personalized Career Chatbot")

# ---- OPENAI CLIENT ----
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ---- PARSERS ----
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# ---- LINKEDIN SUMMARY ----
def generate_linkedin_summaries(cv_text):
    prompt = f"""
You are a career coach. Based on the resume below, write 10 short LinkedIn summary variations. Each should be 3–4 lines, professional, and unique.
Resume:
{cv_text[:2000]}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# ---- INTERVIEW Q&A ----
def generate_custom_interview_questions(cv_text, role, level):
    prompt = f"""
You are an interview expert. Based on this resume and the role of {role}, generate 30 interview questions with answers for a {level} level role. Include technical, behavioral, and situational questions.
Resume:
{cv_text[:2000]}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# ---- JD-BASED INTERVIEW ----
def generate_questions_from_jd(cv_text, jd_text):
    prompt = f"""
You're an interview coach. Based on the resume and job description, generate 15 interview questions with expert answers.

Resume:
{cv_text[:1500]}

Job Description:
{jd_text[:1500]}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# ---- JOB MATCHING ----
def suggest_jobs(cv_text):
    keywords = ["data analyst", "project manager", "software engineer", "business analyst", "healthcare consultant"]
    matches = [role.title() for role in keywords if role in cv_text.lower()]
    if not matches:
        matches = random.sample(keywords, 2)
    return [
        f"🔹 [{role} at ABC Corp](https://www.linkedin.com/jobs/search/?keywords={role.replace(' ', '%20')})"
        for role in matches
    ]

# ---- SAMPLE CVs ----
def get_sample_cv():
    sample_dir = "sample_cvs"
    os.makedirs(sample_dir, exist_ok=True)
    files = [f for f in os.listdir(sample_dir) if f.endswith((".pdf", ".docx"))]
    return files, sample_dir

# ---- SIDEBAR ----
with st.sidebar:
    st.image("https://img.icons8.com/nolan/64/ai.png", width=60)
    st.header("Career Bot Menu")
    user_email = st.text_input("📧 Enter your Email (optional):")
    menu_option = st.radio("Choose a Feature:", [
        "Upload Resume",
        "Generate LinkedIn Summary",
        "Mock Interview Q&A",
        "Interview Prep using JD",
        "Job Suggestions",
        "Download & Preview Sample CVs"
    ])

# ---- FILE UPLOAD ----
uploaded_file = st.file_uploader("📤 Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])
cv_text = ""
if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        cv_text = extract_text_from_pdf(uploaded_file)
    else:
        cv_text = extract_text_from_docx(uploaded_file)

# ---- MAIN FUNCTIONALITY ----
if menu_option == "Generate LinkedIn Summary" and cv_text:
    st.subheader("💼 Top 10 LinkedIn Summary Suggestions")
    with st.spinner("Generating summaries..."):
        summaries = generate_linkedin_summaries(cv_text)
    st.markdown(summaries)

elif menu_option == "Mock Interview Q&A" and cv_text:
    st.subheader("🎤 Mock Interview Preparation")
    role = st.text_input("Enter the Target Role:")
    level = st.selectbox("Interview Level:", ["Entry Level", "Mid Level", "Senior Level"])
    if role:
        with st.spinner("Generating 30 questions..."):
            questions = generate_custom_interview_questions(cv_text, role, level)
        st.text_area("📌 Interview Questions & Answers", questions, height=600)

elif menu_option == "Interview Prep using JD" and cv_text:
    st.subheader("📄 Paste Job Description")
    jd_input = st.text_area("Enter the JD here:")
    if jd_input:
        with st.spinner("Generating questions..."):
            output = generate_questions_from_jd(cv_text, jd_input)
        st.text_area("🧠 Interview Questions", output, height=500)

elif menu_option == "Job Suggestions" and cv_text:
    st.subheader("🔍 Job Recommendations for You")
    with st.spinner("Analyzing your profile..."):
        job_links = suggest_jobs(cv_text)
    for link in job_links:
        st.markdown(link, unsafe_allow_html=True)

elif menu_option == "Download & Preview Sample CVs":
    st.subheader("📁 Sample CV Templates")
    files, path = get_sample_cv()
    if files:
        for file in files:
            icon = "📄" if file.endswith(".pdf") else "📝"
            with open(os.path.join(path, file), "rb") as f:
                st.download_button(
                    label=f"{icon} {file}",
                    data=f,
                    file_name=file,
                    mime="application/octet-stream"
                )
    else:
        st.warning("No sample CVs found. Please add files to the `sample_cvs` folder.")

elif menu_option == "Upload Resume" and not uploaded_file:
    st.warning("📎 Please upload your resume to proceed.")
