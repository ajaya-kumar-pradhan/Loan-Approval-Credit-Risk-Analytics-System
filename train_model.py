import pandas as pd
import numpy as np
import joblib
import os
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score

# Configuration
DATA_PATH = "data/loan_data.csv"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

def load_data():
    """Reads the loan dataset from the data directory."""
    print(f"Loading data from {DATA_PATH}...")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Missing data file at {DATA_PATH}. Please make sure to copy it first.")
    return pd.read_csv(DATA_PATH)

def engineer_features(df):
    """Performs basic data cleaning and adds helpful risk ratios."""
    print("Performing feature engineering...")
    # We work on a copy to keep the original dataframe safe
    data = df.copy()
    
    # Calculate key financial ratios that help predict default
    data['log_annual_inc'] = np.log1p(data['annual_inc'])
    # Income to loan ratio - capped to 500 to avoid extreme outliers
    data['income_to_loan_ratio'] = (data['annual_inc'] / data['loan_amount']).clip(upper=500)
    # Loan to income ratio - capped to 5 to keep it reasonable
    data['lti_ratio'] = (data['loan_amount'] / data['annual_inc']).clip(upper=5)
    
    # Convert text terms to simple numeric flags
    data['is_long_term'] = (data['term'].str.strip() == '60 months').astype(int)
    # High debt-to-income flag (usually a threshold of 35% is significant in banking)
    data['is_high_dti'] = (data['dti'] > 35.0).astype(int)
    # Stability flag: 5 or more years at current employment
    data['is_stable_emp'] = (data['emp_length_int'] >= 5.0).astype(int)
    
    # Map letter grades (A, B, C...) to numbers so the model can understand them
    grade_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6}
    data['grade_rank'] = data['grade'].map(grade_map)
    # Fill any missing grades with a neutral middle value (C)
    data['grade_rank'] = data['grade_rank'].fillna(2)
    
    # Our target: 1 if the loan is bad (Default), 0 if it's good
    data['default_flag'] = (data['loan_condition'] == 'Bad Loan').astype(int)
    
    return data

def prepare_modeling_data(df):
    """Selects relevant columns and splits data for training and testing."""
    print("Preparing features and target...")
    
    # We choose features that have the most predictive power for risk
    feature_columns = [
        'loan_amount', 'annual_inc', 'interest_rate', 'dti', 'installment',
        'log_annual_inc', 'income_to_loan_ratio', 'lti_ratio',
        'is_long_term', 'is_high_dti', 'is_stable_emp', 'grade_rank'
    ]
    
    X = df[feature_columns]
    y = df['default_flag']
    
    # Ensure there are no missing values in our features
    X = X.fillna(X.median())
    
    # Split the data properly (80% for training, 20% for testing)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scaling ensures all features are on a similar range (-1 to 1 or similar)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_columns

def train_and_evaluate(X_train, X_test, y_train, y_test):
    """Trains the Random Forest model and prints performance metrics."""
    print("Training Random Forest model (this might take a minute)...")
    
    # We use 'balanced' class weights because bad loans are rarer than good ones
    model = RandomForestClassifier(
        n_estimators=100, 
        max_depth=10, 
        random_state=42, 
        class_weight='balanced',
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Check how well we did
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]
    
    print("\n--- Model Evaluation Results ---")
    print(classification_report(y_test, predictions))
    print(f"Final ROC-AUC Score: {roc_auc_score(y_test, probabilities):.4f}")
    
    return model

def save_artifacts(model, scaler, features):
    """Saves everything needed for the web app to make predictions later."""
    print(f"Saving model artifacts to '{MODEL_DIR}' folder...")
    joblib.dump(model, os.path.join(MODEL_DIR, "model.joblib"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
    
    # Save the list of features so the API knows what inputs it needs
    with open(os.path.join(MODEL_DIR, "features.json"), "w") as f:
        json.dump(features, f)
    print("Successfully saved all artifacts!")

if __name__ == "__main__":
    try:
        # Step 1: Load
        data_df = load_data()
        
        # Step 2: Clean & Engineer
        processed_df = engineer_features(data_df)
        
        # Step 3: Prepare for ML
        X_train, X_test, y_train, y_test, scaler, feature_list = prepare_modeling_data(processed_df)
        
        # Step 4: Train
        final_model = train_and_evaluate(X_train, X_test, y_train, y_test)
        
        # Step 5: Save
        save_artifacts(final_model, scaler, feature_list)
        
    except Exception as e:
        print(f"An error occurred during training: {e}")
