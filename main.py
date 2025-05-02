import streamlit as st
import plotly.express as px
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Connect to Google Sheets
@st.cache_resource
def get_gsheet_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(creds)
    return client

# App config
st.set_page_config(page_title="Data Maturity Survey", layout="centered")
with st.sidebar:
    st.image("Sapiedata.png", width=150)
    st.markdown("### Data Maturity Survey")

# Questions
survey_questions = [
    {
        "domain": "Strategy & Leadership",
        "question": "Does your organization have a documented, reviewed data strategy?",
        "options": [
            ("No strategy at all", 1),
            ("Informal ideas but nothing documented", 2),
            ("A documented strategy exists but isn’t well used", 3),
            ("We have a clear, reviewed data strategy aligned to business goals", 4),
        ]
    },
    {
        "domain": "People & Skills",
        "question": "How would you rate your team’s data literacy and confidence?",
        "options": [
            ("Most people are uncomfortable with data", 1),
            ("Some people are learning, but skills are patchy", 2),
            ("Teams can interpret dashboards, but not build them", 3),
            ("Teams are confident using data tools and making decisions", 4),
        ]
    },
    {
        "domain": "Tools & Infrastructure",
        "question": "What best describes your data infrastructure?",
        "options": [
            ("Data is stored in spreadsheets and scattered systems", 1),
            ("We have some cloud tools but no integration", 2),
            ("We use a centralized data platform (e.g., data warehouse)", 3),
            ("Our tools are integrated, scalable, and automated", 4),
        ]
    },
    {
        "domain": "Governance & Compliance",
        "question": "How do you manage data access, quality, and compliance?",
        "options": [
            ("No formal policies", 1),
            ("Some access rules, but not enforced", 2),
            ("Defined ownership and some monitoring", 3),
            ("Strong governance with audits, monitoring, and training", 4),
        ]
    },
    {
        "domain": "Culture & Adoption",
        "question": "How ingrained is data-driven thinking in your organization?",
        "options": [
            ("Gut feel drives most decisions", 1),
            ("Some teams use data occasionally", 2),
            ("Data informs key decisions across functions", 3),
            ("Data is the foundation for strategy and daily ops", 4),
        ]
    },
    {
        "domain": "Measurement & Performance",
        "question": "How do you measure and communicate business performance?",
        "options": [
            ("Little or no tracking", 1),
            ("Basic dashboards/reports", 2),
            ("Regular reporting but not action-oriented", 3),
            ("Clear KPIs tracked in real time and discussed weekly", 4),
        ]
    },
    {
        "domain": "Innovation Readiness",
        "question": "Are you leveraging AI, automation, or predictive analytics?",
        "options": [
            ("Not at all", 1),
            ("It's on our radar", 2),
            ("We’re running experiments", 3),
            ("We actively use smart tools for decision support", 4),
        ]
    }
]

# Session state
if "responses" not in st.session_state:
    st.session_state.responses = []
if "step" not in st.session_state:
    st.session_state.step = 0

# Progress
st.title("📊 Data Maturity Assessment")
progress = int((st.session_state.step / len(survey_questions)) * 100)
st.progress(progress)

# Survey flow
if st.session_state.step < len(survey_questions):
    q = survey_questions[st.session_state.step]
    st.subheader(q["question"])
    selected = st.radio("Choose one:", [opt[0] for opt in q["options"]], key=f"q{st.session_state.step}")
    if st.button("Next", key=f"next{st.session_state.step}"):
        score = dict(q["options"])[selected]
        st.session_state.responses.append({
        "domain": q["domain"],
        "question": q["question"],
        "answer": selected,
        "score": score
        })

        st.session_state.step += 1
        st.rerun()

# Show results
else:
    st.success("🎉 Survey complete! Here's your data maturity snapshot.")

    df = pd.DataFrame(st.session_state.responses)
    domain_scores = df.groupby("domain")["score"].sum().reset_index()
    total_score = int(df["score"].sum())

    if total_score <= 10:
        tier = "📉 Beginner"
    elif total_score <= 18:
        tier = "📈 Emerging"
    elif total_score <= 24:
        tier = "📊 Developing"
    else:
        tier = "🚀 Mature"

    # Bubble chart
    fig = px.scatter(domain_scores,
                     x="domain",
                     y="score",
                     size="score",
                     color="domain",
                     size_max=60,
                     title="🫧 Data Maturity by Domain")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"### 🧠 Your Maturity Tier: **{tier}**")
    st.caption(f"Total Score: {total_score} out of {len(survey_questions) * 4}")

    # Recommendations
    st.markdown("### 📌 Recommendations:")
    for _, row in domain_scores.iterrows():
        if row["score"] <= 2:
            st.warning(f"**{row['domain']}**: Needs foundational work — consider starting here.")
        elif row["score"] <= 3:
            st.info(f"**{row['domain']}**: On the right track — refine your strategy and execution.")
        else:
            st.success(f"**{row['domain']}**: Looking strong!")

    # Workshop offer
    st.markdown("---")
    st.subheader("🎁 Want tailored help?")
    interest = st.radio("Would you like a free data strategy workshop?", ["Yes", "No"])
    if interest == "Yes":
        name = st.text_input("Your Name")
        email = st.text_input("Your Email")
        if st.button("Request Workshop"):
            if name and email:
                st.success("✅ Thanks! We'll reach out to you shortly.")

                # Build full data row
                row = [name, email, total_score, tier]
                for r in st.session_state.responses:
                    row.append(r["question"])
                    row.append(r["answer"])
                
                # Push to Google Sheet
                try:
                    client = get_gsheet_client()
                    sheet = client.open("Data Maturity Leads").sheet1
                    sheet.append_row(row)
                except Exception as e:
                    st.error(f"❌ Failed to save: {e}")
            else:
                st.error("Please enter your name and email.")