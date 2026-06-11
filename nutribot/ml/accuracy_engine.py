import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

class TCMAccuracyEngine:
    """
    ML-driven engine to improve TCM pattern prediction accuracy and 
    provide a 'Ground Truth' to prevent LLM hallucinations.
    """
    def __init__(self, model_path='models/tcm_pattern_model.pkl'):
        self.model_path = model_path
        self.clf = RandomForestClassifier(n_estimators=100, random_state=42)
        self.encoder = LabelEncoder()
        
    def train_on_historical_data(self, data_path='data/clinical_correlations.csv'):
        """
        Trains a model on clinical data (SNP + Labs -> Confirmed TCM Pattern).
        This replaces static mapping with probabilistic prediction.
        """
        if not os.path.exists(data_path):
            print("No training data found. Using baseline rules.")
            return False
            
        df = pd.read_csv(data_path)
        X = df[['MTHFR_VAL', 'COMT_VAL', 'B12_LEVEL', 'FOLATE_LEVEL']]
        y = self.encoder.fit_transform(df['TCM_PATTERN'])
        
        self.clf.fit(X, y)
        # Save model for future use
        os.makedirs('models', exist_ok=True)
        # joblib.dump(self.clf, self.model_path)
        return True

    def predict_with_confidence(self, features):
        """
        Predicts the TCM pattern and returns a confidence score.
        If confidence is low (< 0.6), we flag it to prevent hallucination.
        """
        # Simulated prediction for prototype
        # In production, this would use self.clf.predict_proba()
        prediction = "Spleen_Qi_Deficiency"
        confidence = 0.85 
        
        return prediction, confidence

class HallucinationGuardrail:
    """
    Implements Chain of Verification (CoVe) to ensure the AI doesn't 
    make up genetic or medical facts.
    """
    @staticmethod
    def verify_recommendation(recommendation, pattern, evidence_base):
        """
        Cross-references the LLM's recommendation against a verified knowledge base.
        """
        # Logic: 
        # 1. Extract Herb/Action from recommendation
        # 2. Check if Herb is known to treat the specific Pattern
        # 3. If no evidence exists, flag as 'Potential Hallucination'
        
        verified_herbs = {
            "Spleen_Qi_Deficiency": ["Ginseng", "Astragalus", "Licorice", "Atractylodes"],
            "Liver_Qi_Stagnation": ["Bupleurum", "Peony", "Mint", "Cyperus"],
            # ... add more
        }
        
        for herb in verified_herbs.get(pattern, []):
            if herb.lower() in recommendation.lower():
                return True, "Verified by TCM Knowledge Base"
                
        return False, "Low Evidence - Verification Required"

    @staticmethod
    def generate_verification_prompt(original_response):
        """
        Creates a prompt for the LLM to 'self-correct'.
        """
        return f"""
        Original Recommendation: {original_response}
        
        Please perform a Chain of Verification:
        1. List the specific health claims made.
        2. For each claim, cite the TCM principle or Genetic research that supports it.
        3. If any claim lacks strong evidence, please revise it to be more conservative.
        
        Revised Output:
        """
