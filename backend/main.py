from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import joblib
import pandas as pd
import numpy as np
import os
import json

# Define the FastAPI application
app = FastAPI(
    title="Loan Prediction API",
    description="A simple API to predict the likelihood of loan default."
)

# Enable CORS so our frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you'd specify your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths to our saved model files
# We go up one level since main.py is in the 'backend' folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.joblib")
SCALER_PATH = os.path.join(BASE_DIR, "models", "scaler.joblib")
FEATURES_PATH = os.path.join(BASE_DIR, "models", "features.json")

# Global variables to hold our model parts
model = None
scaler = None
feature_names = []

# Load everything when the script starts
try:
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        with open(FEATURES_PATH, "r") as f:
            feature_names = json.load(f)
        print("Successfully loaded model and artifacts.")
    else:
        print(f"Warning: Model file not found at {MODEL_PATH}. Prediction will not work.")
except Exception as e:
    print(f"Error loading model: {e}")

# This class defines what data we expect from the user
class LoanRequest(BaseModel):
    loan_amount: float
    annual_inc: float
    interest_rate: float
    dti: float
    installment: float
    term: str  # "36 months" or "60 months"
    emp_length_int: float
    grade: str # "A", "B", "C", etc.

@app.get("/")
def home():
    """Simple welcome message."""
    return {"message": "Loan Prediction API is running!"}

@app.get("/health")
def health():
    """Checks if the model is loaded and ready."""
    return {
        "status": "online",
        "model_ready": model is not None
    }

@app.post("/predict")
def predict_loan(request: LoanRequest):
    """Takes loan data and returns the probability of default."""
    
    # Safety check: make sure the model is actually there
    if model is None:
        raise HTTPException(status_code=500, detail="Prediction model is not available.")

    try:
        # Preprocessing: we need to match exactly how we trained the model
        
        # 1. Feature engineering (Human style: step by step)
        log_annual_inc = np.log1p(request.annual_inc)
        
        # Income to loan ratio (capped at 500)
        inc_loan_ratio = request.annual_inc / request.loan_amount if request.loan_amount > 0 else 0
        inc_loan_ratio = min(inc_loan_ratio, 500)
        
        # Loan to income ratio (capped at 5)
        lti_ratio = request.loan_amount / request.annual_inc if request.annual_inc > 0 else 1
        lti_ratio = min(lti_ratio, 5)
        
        # Helper flags
        is_long_term = 1 if "60" in request.term else 0
        is_high_dti = 1 if request.dti > 35 else 0
        is_stable_emp = 1 if request.emp_length_int >= 5 else 0
        
        # Map grade to rank
        grade_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6}
        grade_rank = grade_map.get(request.grade.upper(), 2) # Default to 'C'
        
        # 2. Put features in the correct order for the model
        input_data = {
            'loan_amount': [request.loan_amount],
            'annual_inc': [request.annual_inc],
            'interest_rate': [request.interest_rate],
            'dti': [request.dti],
            'installment': [request.installment],
            'log_annual_inc': [log_annual_inc],
            'income_to_loan_ratio': [inc_loan_ratio],
            'lti_ratio': [lti_ratio],
            'is_long_term': [is_long_term],
            'is_high_dti': [is_high_dti],
            'is_stable_emp': [is_stable_emp],
            'grade_rank': [grade_rank]
        }
        
        # Convert to DataFrame
        X_test = pd.DataFrame(input_data)
        
        # Ensure the columns are in the exact order the model expects
        X_test = X_test[feature_names]
        
        # 3. Apply the scaler we saved during training
        X_scaled = scaler.transform(X_test)
        
        # 4. Make the prediction
        # predict_proba returns [prob_good, prob_bad]
        prob_bad = float(model.predict_proba(X_scaled)[0][1])
        
        # Decide on a human-friendly risk level
        risk_label = "Low"
        if prob_bad > 0.65:
            risk_label = "Very High"
        elif prob_bad > 0.45:
            risk_label = "High"
        elif prob_bad > 0.25:
            risk_label = "Medium"
            
        return {
            "success": True,
            "default_probability": round(prob_bad * 100, 2), # Percentage format
            "risk_level": risk_label,
            "is_risky": prob_bad > 0.5
        }

    except Exception as e:
        # If anything goes wrong, return a helpful error
        print(f"Prediction error: {e}")
        raise HTTPException(status_code=400, detail=f"Could not process prediction: {str(e)}")

# Serve the frontend
# We assume the React build files will be in 'frontend/dist' after npm run build
if os.path.exists(os.path.join(BASE_DIR, "frontend", "dist")):
    app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "frontend", "dist"), html=True), name="frontend")
else:
    print("Warning: Frontend build folder not found. API only mode.")

if __name__ == "__main__":
    import uvicorn
    # Start the server (for testing locally)
    uvicorn.run(app, host="0.0.0.0", port=8000)
