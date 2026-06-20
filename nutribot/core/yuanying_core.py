import pandas as pd
import numpy as np
import os
from nutribot import i18n
import os as _os

# language
current_lang = _os.getenv('NUTRIBOT_LANG') or 'en'

class EntangledState:
    """
    Represents an 'entangled' relationship between a Genetic Marker and a TCM Pattern.
    In TCM context, this is like 'Biao-Li' (Exterior-Interior) relationship where 
    the deep genetic root (Li) is entangled with the visible TCM manifestation (Biao).
    """
    def __init__(self, gene, tcm_pattern, strength):
        self.gene = gene
        self.tcm_pattern = tcm_pattern
        self.strength = strength # STRONG, WEAK, NEUTRAL
        
    def __repr__(self):
        return f"EntangledState({self.gene} <-> {self.tcm_pattern} [{self.strength}])"

class HealthWavefunction:
    """
    Represents the 'Superposition' of all possible health states and recommendations.
    In TCM, this is like the 'Taiji' state before it differentiates into Yin and Yang.
    It contains all potential paths before we observe or choose a specific goal.
    """
    def __init__(self):
        self.amplitudes = {} # recommendation_id -> probability amplitude
        self.states = []     # List of possible recommendations
        
    def add_state(self, recommendation, amplitude):
        self.states.append(recommendation)
        self.amplitudes[recommendation] = amplitude

class YuanYingCore:
    """
    The main engine for Quantum-Inspired Genetic-TCM Correlation.
    'Yuan Ying' (元嬰) refers to the 'Primordial Infant' or 'Nascent Soul' in Daoist 
    inner alchemy, representing a high state of integrated energy.
    """
    def __init__(self, map_path='data/gene_tcm_map.csv'):
        self.map_path = map_path
        self.correlation_matrix = self.load_entanglement_matrix()
        self.wavefunction = HealthWavefunction()
        self.entangled_pairs = []

    def load_entanglement_matrix(self):
        """Loads the Gene-TCM mapping from CSV."""
        if os.path.exists(self.map_path):
            return pd.read_csv(self.map_path)
        return pd.DataFrame(columns=['SNP_Marker', 'TCM_Pattern', 'Correlation_Strength', 'Description'])

    def cycle_1_superposition(self, genes, lab_values, symptoms):
        """
        Phase 1: Create a superposition of all possible recommendations based on inputs.
        Hadamard Gate logic: We expand the search space from a single state to all 
        correlated possibilities.
        """
        print(i18n.translate('cycle1_superposition', current_lang))
        
        # Identify entangled states based on user genes
        relevant_correlations = self.correlation_matrix[self.correlation_matrix['SNP_Marker'].isin(genes)]
        
        for _, row in relevant_correlations.iterrows():
            pair = EntangledState(row['SNP_Marker'], row['TCM_Pattern'], row['Correlation_Strength'])
            self.entangled_pairs.append(pair)
        
        # Generate initial recommendation states
        all_recs = self.generate_all_recommendations(genes, symptoms)
        
        # In quantum terms, we give each potential recommendation an initial amplitude
        for rec in all_recs:
            # Strength affects initial probability amplitude
            # STRONG = 0.9, WEAK = 0.5, NEUTRAL = 0.1
            strength_map = {'STRONG': 0.9, 'WEAK': 0.5, 'NEUTRAL': 0.1}
            # Find the max strength related to this recommendation's TCM pattern
            related_pairs = [p for p in self.entangled_pairs if p.tcm_pattern in rec['tcm_focus']]
            max_amp = max([strength_map.get(p.strength, 0.1) for p in related_pairs], default=0.3)
            
            self.wavefunction.add_state(rec['id'], max_amp)
            
        return f"Superposition created with {len(all_recs)} potential health states."

    def cycle_2_coherent_processing(self):
        """
        Phase 2: Apply quantum-like gates to resolve contradictions.
        Pauli-X Gate: Inverts a recommendation if it conflicts with lab values.
        CNOT Gate: If A is true, then boost/suppress B.
        """
        print(i18n.translate('cycle2_coherent_processing', current_lang))
        
        contradictions = self.find_contradictions()
        
        for contra in contradictions:
            # Apply Quantum Rules to resolve
            self.apply_quantum_rules(contra)
            
        return f"Processed {len(contradictions)} contradictions. Wavefunction coherence stabilized."

    def cycle_3_collapse(self, user_goal):
        """
        Phase 3: Observation/Measurement.
        The wavefunction collapses into a single personalized health plan based 
        on the 'user_goal' which acts as the 'Measurement Operator'.
        """
        print(i18n.translate('cycle3_collapsing', current_lang).format(goal=user_goal))
        
        # Re-calculate probabilities based on goal alignment
        final_recommendations = []
        
        # Simplified 'Collapse': Filter and sort by highest amplitude
        sorted_recs = sorted(self.wavefunction.amplitudes.items(), key=lambda x: x[1], reverse=True)
        
        # In a real model, we'd use goal-specific weights here
        return sorted_recs

    def generate_all_recommendations(self, genes, symptoms):
        """
        Generates a pool of potential TCM recommendations based on identified patterns.
        """
        # This would normally be a larger knowledge base. 
        # For this prototype, we'll generate some programmatically.
        pool = [
            {'id': 'REC_001', 'text': 'Ginseng & Astragalus Tea', 'tcm_focus': ['Spleen_Qi_Deficiency'], 'type': 'Herb'},
            {'id': 'REC_002', 'text': 'Ginger Warm Compress', 'tcm_focus': ['Spleen_Qi_Deficiency'], 'type': 'External'},
            {'id': 'REC_003', 'text': 'Xiao Yao San (Free & Easy Wanderer)', 'tcm_focus': ['Liver_Qi_Stagnation'], 'type': 'Herb'},
            {'id': 'REC_004', 'text': 'Daily Meditation (10 mins)', 'tcm_focus': ['Liver_Qi_Stagnation'], 'type': 'Lifestyle'},
            {'id': 'REC_005', 'text': 'Goji Berries & Rehmannia', 'tcm_focus': ['Kidney_Ying_Deficiency'], 'type': 'Herb'},
            {'id': 'REC_006', 'text': 'Hawthorn Berry Tea', 'tcm_focus': ['Blood_Stasis'], 'type': 'Herb'},
            {'id': 'REC_007', 'text': 'Avoid Cold/Raw Foods', 'tcm_focus': ['Spleen_Qi_Deficiency', 'Phlegm_Dampness'], 'type': 'Diet'},
        ]
        
        # Filter pool to only those that match our entangled TCM patterns
        target_patterns = [p.tcm_pattern for p in self.entangled_pairs]
        active_recs = [r for r in pool if any(pattern in r['tcm_focus'] for pattern in target_patterns)]
        
        return active_recs

    def find_contradictions(self):
        """
        Identifies contradictions (e.g., a warming herb for someone with Heat symptoms).
        In Quantum terms, this is 'Destructive Interference'.
        """
        # Simplified logic: If multiple recommendations target conflicting patterns
        # or if a recommendation is contraindicated by a specific lab value.
        return [{"id": "C1", "type": "Herb_Conflict", "severity": "Medium"}]

    def apply_quantum_rules(self, contradiction):
        """
        Applies rules to adjust probability amplitudes.
        """
        # Example: If contradiction is found, we reduce the amplitude (Destructive Interference)
        for rec_id in self.wavefunction.amplitudes:
            # Arbitrary logic for prototype
            self.wavefunction.amplitudes[rec_id] *= 0.8 

    def calculate_probability(self, amplitude):
        """
        Born's Rule: Probability = |Amplitude|^2
        In TCM: How likely this recommendation will work for this specific person.
        """
        return (amplitude ** 2)
