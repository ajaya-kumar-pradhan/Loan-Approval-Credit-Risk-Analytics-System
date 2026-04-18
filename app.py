import streamlit as st
import pandas as pd
import numpy as np
import joblib
import json
import os

# Configure the Streamlit page
st.set_page_config(
    page_title="Credit Risk IQ",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium design
st.markdown("""
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Outfit', sans-serif;
    }
    .stApp {
        background-image: 
            radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
            radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
    }
    .stButton>button {
        background-color: #6366f1;
        color: white;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: bold;
        transition: all 0.3s ease;
        border: none;
        width: 100%;
        padding: 0.75rem;
    }
    .stButton>button:hover {
        background-color: #4f46e5;
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.4);
    }
    .result-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    h1 {
        background: linear-gradient(to right, #fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. LOAD ARTIFACTS
# -------------------------------------------------------------
@st.cache_resource
def load_models():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "models", "model.joblib")
    scaler_path = os.path.join(base_dir, "models", "scaler.joblib")
    features_path = os.path.join(base_dir, "models", "features.json")
    
    if not (os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(features_path)):
        return None, None, []
        
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    with open(features_path, "r") as f:
        feature_names = json.load(f)
        
    return model, scaler, feature_names

model, scaler, feature_names = load_models()

# -------------------------------------------------------------
# 2. UI HEADER
# -------------------------------------------------------------
st.title("Credit Risk IQ")
st.markdown("<p style='color: #94a3b8; font-size: 1.2rem; margin-bottom: 2rem;'>Real-time Loan Default Prediction System</p>", unsafe_allow_html=True)

if model is None:
    st.error("Error: Could not load the machine learning models. Please ensure the models/ directory exists with model.joblib and scaler.joblib.")
    st.stop()

# -------------------------------------------------------------
# 3. INPUT FORM
# -------------------------------------------------------------
with st.container():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        loan_amount = st.number_input("Loan Amount ($)", min_value=500.0, max_value=100000.0, value=10000.0, step=500.0)
        annual_inc = st.number_input("Annual Income ($)", min_value=1000.0, max_value=1000000.0, value=50000.0, step=1000.0)
        dti = st.number_input("Debt-to-Income (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)

    with col2:
        interest_rate = st.number_input("Interest Rate (%)", min_value=1.0, max_value=40.0, value=12.5, step=0.1)
        installment = st.number_input("Monthly Installment ($)", min_value=10.0, max_value=5000.0, value=320.0, step=10.0)
        term = st.selectbox("Loan Term", options=["36 months", "60 months"])

    with col3:
        emp_length_int = st.number_input("Employment (Years)", min_value=0.0, max_value=50.0, value=5.0, step=1.0)
        grade = st.selectbox("Credit Grade", options=["A", "B", "C", "D", "E", "F", "G"])

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("Run Risk Assessment")

# -------------------------------------------------------------
# 4. PREDICTION LOGIC
# -------------------------------------------------------------
if analyze_btn:
    # Feature engineering (Human style: step by step)
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

    # Prepare input dataframe
    input_data = {
        'loan_amount': [loan_amount],
        'annual_inc': [annual_inc],
        'interest_rate': [interest_rate],
        'dti': [dti],
        'installment': [installment],
        'log_annual_inc': [log_annual_inc],
        'income_to_loan_ratio': [inc_loan_ratio],
        'lti_ratio': [lti_ratio],
        'is_long_term': [is_long_term],
        'is_high_dti': [is_high_dti],
        'is_stable_emp': [is_stable_emp],
        'grade_rank': [grade_rank]
    }
    
    X_test = pd.DataFrame(input_data)
    X_test = X_test[feature_names] # Ensure exactly the features seen during training
    
    # Scale Data
    X_scaled = scaler.transform(X_test)
    
    # Run Prediction
    prob_bad = float(model.predict_proba(X_scaled)[0][1])
    is_risky = prob_bad > 0.20
    
    # Risk labeling logic
    if prob_bad > 0.30:
        risk_label = "Very High"
        color = "#f87171"
        bg_color = "rgba(239, 68, 68, 0.2)"
    elif prob_bad > 0.22:
        risk_label = "High"
        color = "#fbbf24"
        bg_color = "rgba(245, 158, 11, 0.2)"
    elif prob_bad > 0.18:
        risk_label = "Medium"
        color = "#818cf8"
        bg_color = "rgba(99, 102, 241, 0.2)"
    else:
        risk_label = "Low"
        color = "#4ade80"
        bg_color = "rgba(34, 197, 94, 0.2)"

    # Display Results
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="result-card">
            <h2 style='margin-bottom: 20px; font-weight: 600;'>Analysis Results</h2>
            <div style='display: flex; align-items: center; gap: 2rem;'>
                <div style='width: 120px; height: 120px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; border: 4px solid #6366f1; margin-bottom: 1rem;'>
                  <span style='font-size: 1.8rem; font-weight: 700; color: white;'>{round(prob_bad*100, 1)}%</span>
                  <span style='font-size: 0.7rem; color: #94a3b8;'>Default Prob</span>
                </div>
                <div>
                    <div style='display: inline-block; padding: 0.5rem 1rem; border-radius: 9999px; font-weight: 700; text-transform: uppercase; font-size: 0.8rem; margin-bottom: 1rem; background: {bg_color}; color: {color}; border: 1px solid {color};'>
                        Risk Level: {risk_label}
                    </div>
                    <p style='font-size: 1.2rem; color: white;'>
                        The application was evaluated as <strong>{'High Risk' if is_risky else 'Low Risk'}</strong>.
                    </p>
                    <p style='color: #94a3b8; margin-top: 0.5rem;'>
                        Prediction based on Random Forest classifier artifacts.
                    </p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
