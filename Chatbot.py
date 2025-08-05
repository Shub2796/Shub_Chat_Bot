import streamlit as st
import os
import pandas as pd
import random
from openai import OpenAI
from PyPDF2 import PdfReader
import docx
from PIL import Image
import urllib.parse

# ---- CONFIG ----
st.set_page_config(page_title="Career Bot", layout="wide")

# ---- ADVANCED BACKGROUND STYLING ----

background_style = """
<style>
/* Light Background Image or Solid Color */
[data-testid="stAppViewContainer"] {
    background-image: url('https://images.unsplash.com/photo-1581093458791-6c02fc843dc6?auto=format&fit=crop&w=1950&q=80');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}

/* Slight white overlay for readability */
.stApp {
    background-color: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(3px);
}

/* Sidebar and Header light blur */
[data-testid="stHeader"], [data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(4px);
}

/* Set all font colors to black */
h1, h2, h3, h4, h5, h6, p, label, span, div, button, input, textarea {
    color: #000000 !important;
}

/* Input and textarea styling */
input, textarea {
    background-color: rgba(255, 255, 255, 0.9);
    color: #000000;
    border: 1px solid #000000;
}

/* Button styling */
button {
    background-color: #f0f0f0;
    color: #000000 !important;
    border: 1px solid #000000;
}
</style>
"""


st.markdown(background_style, unsafe_allow_html=True)

# ---- CONSTANTS ----
USER_DB = "users.csv"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ---- AUTH FUNCTIONS ----
def load_users():
    if not os.path.exists(USER_DB):
        df = pd.DataFrame(columns=["email_or_phone", "password"])
        df.to_csv(USER_DB, index=False)
    return pd.read_csv(USER_DB)

def save_user(email_or_phone, password):
    df = load_users()
    if email_or_phone not in df["email_or_phone"].values:
        df.loc[len(df)] = [email_or_phone, password]
        df.to_csv(USER_DB, index=False)

def authenticate(email_or_phone, password):
    df = load_users()
    match = df[(df["email_or_phone"] == email_or_phone) & (df["password"] == password)]
    return not match.empty

def get_user_password(email_or_phone):
    df = load_users()
    row = df[df["email_or_phone"] == email_or_phone]
    return row.iloc[0]["password"] if not row.empty else None

# ---- LOGIN PAGE ----
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Welcome to Career Bot")

    tab1, tab2 = st.tabs(["🤖 Login", "📊 Register"])

    with tab1:
        login_method = st.radio("Login with:", ["Email", "Phone"])
        email_or_phone = st.text_input(f"{login_method}")
        password = st.text_input("Password", type="password")

        col1, col2 = st.columns([1, 2])
        if col1.button("Login"):
            if authenticate(email_or_phone, password):
                st.success("✅ Login successful.")
                st.session_state["authenticated"] = True
                st.session_state["user"] = email_or_phone
                st.rerun()
            else:
                st.error("❌ Invalid credentials.")

        if col2.button("Forgot Password?"):
            stored_pw = get_user_password(email_or_phone)
            if stored_pw:
                st.info("📩 Please contact support to retrieve your password.")
            else:
                st.warning("User not found.")

    with tab2:
        new_email = st.text_input("New Email or Phone")
        new_password = st.text_input("Create Password", type="password")

        if st.button("Register"):
            if new_email and new_password:
                save_user(new_email, new_password)
                st.success("✅ Account created! Please login.")
            else:
                st.warning("Please fill both fields.")

    st.stop()

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
    region = "UAE"
    keywords = ["data analyst", "project manager", "software engineer", "business analyst", "healthcare consultant"]
    matches = [role.title() for role in keywords if role in cv_text.lower()]
    if not matches:
        matches = random.sample(keywords, 2)

    return [
        f"🔹 [LinkedIn: {role}](https://www.linkedin.com/jobs/search/?keywords={urllib.parse.quote_plus(role)}&location={region})\n"
        f"🔹 [Google Jobs](https://www.google.com/search?q={urllib.parse.quote_plus(role + ' jobs in ' + region)})\n"
        f"🔹 [Naukri](https://www.naukri.com/{'-'.join(role.lower().split())}-jobs-in-{region.lower()})"
        for role in matches
    ]

# ---- RESUME SCORE ----
def evaluate_resume(cv_text):
    prompt = f"""
You are a resume reviewer. Evaluate the following resume on a 0–100 scale based on current job market standards. Give a score and 5 clear suggestions for improvement.

Resume:
{cv_text[:2000]}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

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
    menu_option = st.radio("Choose a Feature:", [
        "Upload Resume",
        "Generate LinkedIn Summary",
        "Mock Interview Q&A",
        "Interview Prep using JD",
        "Job Suggestions",
        "Download & Preview Sample CVs",
        "Resume Score & Feedback",
        "Premium Career Services"
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

elif menu_option == "Resume Score & Feedback" and cv_text:
    st.subheader("📊 Resume Evaluation")
    with st.spinner("Reviewing resume..."):
        feedback = evaluate_resume(cv_text)
    st.text_area("📈 Score & Suggestions", feedback, height=500)

elif menu_option == "Premium Career Services":
    st.subheader("💼 Premium Career Guidance Services")
    st.markdown("""
    We provide the following premium services:

    - 🔍 Personalized company hiring insights
    - 🧑‍💼 Direct HR contacts and connections
    - 📝 Resume & cover letter 1-on-1 consultations
    - 📞 Mock interview sessions with experts
    - 🎯 Job strategy & application roadmap sessions
    - 🌍 International job market guidance
    - 🗂️ LinkedIn profile review and optimization
    - 🧭 Career transition planning

    👉 For access and pricing, please reach out:
    """)

elif menu_option == "Upload Resume" and not uploaded_file:
    st.warning("📎 Please upload your resume to proceed.")

# ---- FOOTER ----
st.markdown("---")
st.markdown("""
**For career support and consultation Contact:**  
📧 personalizedcareerchatbot@gmail.com  
📱 +971-0556691831 (WhatsApp & Phone)  
🔗 [LinkedIn Profile](https://www.linkedin.com/in/shubham-shinde-27m1996)
""")