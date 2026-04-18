import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import os

# Configure the Streamlit page
st.set_page_config(
    page_title="Loan Default Prediction",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium design
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #0f172a 50%, #020617);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Global Sidebar Color Fix */
    [data-testid="stSidebar"] {
        background-color: #020617 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Force all text in sidebar to be white */
    [data-testid="stSidebar"] section[data-testid="stSidebarNav"] span,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown li {
        color: #ffffff !important;
    }

    /* Sidebar Navigation Labels and Radio Text */
    [data-testid="stSidebar"] .stRadio label, 
    [data-testid="stSidebar"] .stRadio label p,
    [data-testid="stSidebar"] div[role="radiogroup"] label,
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #ffffff !important;
        font-weight: 500 !important;
    }

    /* Target the navigation radio buttons container */
    div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px;
        padding: 12px 18px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    
    div[role="radiogroup"] > label:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: #6366f1 !important;
    }
    
    div[role="radiogroup"] > label[data-selected="true"] {
        background: #4338ca !important;
        border-color: #6366f1 !important;
        box-shadow: 0 4px 15px rgba(67, 56, 202, 0.5);
    }
    
    div[role="radiogroup"] [data-testid="stMarkdownArmchair"] p {
        color: white !important;
    }

    /* Result Card Styling (Glassmorphism) */
    .result-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2.5rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
    }

    /* Input Field Styling */
    .stNumberInput input, .stSelectbox div {
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Primary Button */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
        color: white;
        border-radius: 14px;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 0.8rem 2rem;
        border: none;
        box-shadow: 0 10px 20px -5px rgba(67, 56, 202, 0.5);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 30px -5px rgba(67, 56, 202, 0.6);
        background: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
    }

    /* White text for all standard Streamlit elements in sidebar */
    .css-17l2puu, .css-17l2puu p, [data-testid="stWidgetLabel"] p {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. LOAD ARTIFACTS
# -------------------------------------------------------------
@st.cache_resource
def load_models(_version=2):
    """Load ML artifacts. Increment _version to bust the cache if models change."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "models", "model.joblib")
    scaler_path = os.path.join(base_dir, "models", "scaler.joblib")
    features_path = os.path.join(base_dir, "models", "features.json")

    missing = [p for p in [model_path, scaler_path, features_path] if not os.path.exists(p)]
    if missing:
        st.error(f"Missing model files: {[os.path.basename(p) for p in missing]}")
        return None, None, []

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    with open(features_path, "r") as f:
        feature_names = json.load(f)

    return model, scaler, feature_names

model, scaler, feature_names = load_models()

# -------------------------------------------------------------
# 2. SIDEBAR NAVIGATION
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("<div style='text-align: center; margin-top: -20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='color: white; font-size: 2rem;'>🛡️ LoanGuard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94a3b8; font-size: 0.9rem;'>Portfolio Risk Management</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    page = st.radio("Navigation", ["📝 Loan Evaluation", "📈 Performance Insights"], index=0)
    st.markdown("---")
    
    st.markdown("""
        <div style='padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);'>
            <p style='font-size: 0.85rem; color: #94a3b8;'>
                <b>System Status:</b> Active<br>
                <b>Model:</b> CreditSentry v2.1<br>
                <b>Confidence:</b> 85.4%
            </p>
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. PAGE LOGIC: LOAN EVALUATION
# -------------------------------------------------------------
if page == "📝 Loan Evaluation":
    st.title("Borrower Risk Analysis")
    st.markdown("<p style='color: #94a3b8; font-size: 1.2rem; margin-bottom: 2rem;'>Intelligent Financial Evaluation System</p>", unsafe_allow_html=True)

    if model is None:
        st.error("Error: Could not load the evaluation engine. Please contact system administrator.")
        st.stop()

    # INPUT FORM
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            loan_amount = st.number_input("Loan Amount ($)", min_value=500.0, max_value=100000.0, value=10000.0, step=500.0)
            annual_inc = st.number_input("Annual Income ($)", min_value=1000.0, max_value=1000000.0, value=50000.0, step=1000.0)
            dti = st.number_input("Debt Obligations (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)

        with col2:
            interest_rate = st.number_input("Interest Rate (%)", min_value=1.0, max_value=40.0, value=12.5, step=0.1)
            installment = st.number_input("Expected Monthly Payment ($)", min_value=10.0, max_value=5000.0, value=320.0, step=10.0)
            term = st.selectbox("Repayment Period", options=["36 months", "60 months"])

        with col3:
            emp_length_int = st.number_input("Employment (Years)", min_value=0.0, max_value=50.0, value=5.0, step=1.0)
            grade = st.selectbox("Credit Rating", options=["A", "B", "C", "D", "E", "F", "G"])

        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("Finalize Evaluation")

    # PREDICTION LOGIC
    if analyze_btn:
        # (Internal logic remains the same)
        log_annual_inc = np.log1p(annual_inc)
        inc_loan_ratio = annual_inc / loan_amount if loan_amount > 0 else 0
        inc_loan_ratio = min(inc_loan_ratio, 500)
        lti_ratio = loan_amount / annual_inc if annual_inc > 0 else 1
        lti_ratio = min(lti_ratio, 5)
        is_long_term = 1 if "60" in term else 0
        is_high_dti = 1 if dti > 35 else 0
        is_stable_emp = 1 if emp_length_int >= 5 else 0
        grade_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6}
        grade_rank = grade_map.get(grade.upper(), 2) 

        input_data = {
            'loan_amount': [loan_amount], 'annual_inc': [annual_inc], 'interest_rate': [interest_rate],
            'dti': [dti], 'installment': [installment], 'log_annual_inc': [log_annual_inc],
            'income_to_loan_ratio': [inc_loan_ratio], 'lti_ratio': [lti_ratio], 'is_long_term': [is_long_term],
            'is_high_dti': [is_high_dti], 'is_stable_emp': [is_stable_emp], 'grade_rank': [grade_rank]
        }
        
        X_test = pd.DataFrame(input_data)
        X_test = X_test[feature_names]
        X_scaled = scaler.transform(X_test)
        prob_bad = float(model.predict_proba(X_scaled)[0][1])
        is_risky = prob_bad > 0.20
        
        if prob_bad > 0.30:
            risk_label, color, bg_color = "Critical Risk", "#f87171", "rgba(239, 68, 68, 0.2)"
        elif prob_bad > 0.22:
            risk_label, color, bg_color = "High Exposure", "#fbbf24", "rgba(245, 158, 11, 0.2)"
        elif prob_bad > 0.18:
            risk_label, color, bg_color = "Elevated Risk", "#818cf8", "rgba(99, 102, 241, 0.2)"
        else:
            risk_label, color, bg_color = "Preferred Profile", "#4ade80", "rgba(34, 197, 94, 0.2)"

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="result-card">
                <h2 style='margin-bottom: 20px; font-weight: 600;'>Evaluation Summary</h2>
                <div style='display: flex; align-items: center; gap: 2rem;'>
                    <div style='width: 120px; height: 120px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; border: 4px solid #6366f1; margin-bottom: 1rem;'>
                      <span style='font-size: 1.8rem; font-weight: 700; color: white;'>{round(prob_bad*100, 1)}%</span>
                      <span style='font-size: 0.7rem; color: #94a3b8;'>Risk Score</span>
                    </div>
                    <div>
                        <div style='display: inline-block; padding: 0.5rem 1rem; border-radius: 9999px; font-weight: 700; text-transform: uppercase; font-size: 0.8rem; margin-bottom: 1rem; background: {bg_color}; color: {color}; border: 1px solid {color};'>
                            Profile Rank: {risk_label}
                        </div>
                        <p style='font-size: 1.2rem; color: white;'>
                            The application has been flagged as <strong>{'Cautionary' if is_risky else 'Approved Entry'}</strong>.
                        </p>
                        <p style='color: #94a3b8; margin-top: 0.5rem;'>
                            Analysis based on historical lending benchmarks and credit scoring metrics.
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. PAGE LOGIC: PERFORMANCE INSIGHTS
# -------------------------------------------------------------
elif page == "📈 Performance Insights":
    st.title("Operations Command Center")
    st.markdown("<p style='color: #94a3b8; font-size: 1.2rem; margin-bottom: 2rem;'>Portfolio Monitoring & Risk Intelligence</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="result-card" style="padding: 10px; height: 800px;">
            <iframe title="Banking Operations & Risk Dashboard" 
                    width="100%" 
                    height="100%" 
                    src="https://app.powerbi.com/view?r=eyJrIjoiNGYzMTM1ZDItODQ3Mi00ZWVhLWE3MjQtOGYxYmZjOGRmZDYyIiwidCI6IjdlMzEwODQ1LTg0ZTEtNGRiOC1hZjk4LTcwNDA0MTkwZDhkZSJ9" 
                    frameborder="0" 
                    allowFullScreen="true"
                    style="border-radius: 15px;">
            </iframe>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 Tip: Use the 'Drillthrough' feature on the charts to see granular customer details.")
