import streamlit as st
import openai
import pdfplumber
import json

openai.api_key = st.secrets["OPENAI_API_KEY"]

st.title("AI Recruitment Assistant — Resume Screening Demo")
st.markdown("""
Upload a Job Description and resumes (PDF). The app will use GPT-4 to screen resumes against the JD and provide match scores and recommendations.
""")

job_description = st.text_area("Paste Job Description Here", height=300)

uploaded_resumes = st.file_uploader(
    "Upload Resume PDFs (you can upload multiple)",
    accept_multiple_files=True,
    type=["pdf"]
)

def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)

def call_gpt_screening(resume_text, job_description):
    prompt = f"""
You are a Recruitment Assistant AI.

Here is the Job Description for a Marketing Intern role:

{job_description}

Here is a candidate's resume text:

{resume_text}

Please:
1. Check if the candidate meets all basic qualifications:
   - Currently enrolled as a full-time undergraduate
   - Eligible to work in the U.S.
   - Available in the U.S. for the internship period
   - GPA 3.0 or higher
   - Willing to relocate if necessary

2. Evaluate the preferred qualifications:
   - Communication skills
   - Familiarity with marketing tools (Canva, Mailchimp, Google Analytics)
   - Interest in marketing, communications, or business
   - Teamwork and growth mindset

3. For this candidate, provide:
- Basic qualifications met? Yes/No and why
- Preferred qualifications summary
- Match score (0-100%)
- Strengths and gaps summary
- Recommendation: Strong Match / Partial Match / Not a Match

Format response as JSON with keys:
basic_qualified, preferred_qualifications, match_score, summary, recommendation
"""

    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500
    )
    return resp.choices[0].message.content

if st.button("Run Screening"):
    if not job_description.strip():
        st.error("Please enter a job description!")
    elif not uploaded_resumes:
        st.error("Please upload at least one resume PDF.")
    else:
        results = []
        for resume in uploaded_resumes:
            st.write(f"🔎 Screening **{resume.name}**...")
            resume_text = extract_text_from_pdf(resume)
            raw = call_gpt_screening(resume_text, job_description)
            try:
                data = json.loads(raw)
            except:
                st.warning(f"Could not parse GPT response for {resume.name}. Showing raw output.")
                st.code(raw)
                data = {
                    "basic_qualified": "Error",
                    "preferred_qualifications": "{}",
                    "match_score": "0",
                    "summary": "Parsing failed",
                    "recommendation": "Unknown"
                }
            results.append({
                "Candidate": resume.name,
                "Basic Qualified": data.get("basic_qualified"),
                "Preferred Qualifications": data.get("preferred_qualifications"),
                "Match Score": data.get("match_score"),
                "Summary": data.get("summary"),
                "Recommendation": data.get("recommendation"),
            })
        st.header("Screening Results")
        st.table(results)
