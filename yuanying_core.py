import pandas as pd
import numpy as np

class YuanYingCore:
    def __init__(self):
        self.correlation_matrix = pd.DataFrame([
            {"SNP_Marker": "MTHFR_CT", "TCM_Pattern": "Blood Deficiency", "Element": "Wood", "Organ": "Liver", "Qi_Impact": 0.85},
            {"SNP_Marker": "COMT_AA",  "TCM_Pattern": "Liver Qi Stagnation", "Element": "Wood", "Organ": "Liver", "Qi_Impact": 0.78},
            {"SNP_Marker": "VDR_TA",   "TCM_Pattern": "Kidney Yang Deficiency", "Element": "Water", "Organ": "Kidney", "Qi_Impact": 0.72},
            {"SNP_Marker": "GSTP1_GG", "TCM_Pattern": "Damp-Heat", "Element": "Earth", "Organ": "Spleen", "Qi_Impact": 0.65},
            {"SNP_Marker": "MTR_AA",   "TCM_Pattern": "Qi Deficiency", "Element": "Metal", "Organ": "Lung", "Qi_Impact": 0.80},
            {"SNP_Marker": "NOS3_CT",  "TCM_Pattern": "Blood Stasis", "Element": "Fire", "Organ": "Heart", "Qi_Impact": 0.70},
        ])
        self.superposition_states = []
        self.coherent_states = []

    def cycle_1_superposition(self, snp_list, lab_values, symptoms):
        matched = self.correlation_matrix[
            self.correlation_matrix["SNP_Marker"].isin(snp_list)
        ]
        self.superposition_states = matched.to_dict("records")
        return f"✅ {len(self.superposition_states)} quantum states initialized for SNPs: {', '.join(snp_list)}"

    def cycle_2_coherent_processing(self):
        self.coherent_states = []
        for state in self.superposition_states:
            score = state["Qi_Impact"] * np.random.uniform(0.9, 1.1)
            self.coherent_states.append({**state, "Coherence_Score": round(score, 3)})
        return f"✅ Coherence achieved across {len(self.coherent_states)} states."

    def cycle_3_collapse(self, health_goal):
        goal_map = {
            "Improve Energy":    ["Qi Deficiency", "Blood Deficiency"],
            "Better Sleep":      ["Liver Qi Stagnation", "Blood Stasis"],
            "Stress Reduction":  ["Liver Qi Stagnation", "Damp-Heat"],
            "Digestive Health":  ["Damp-Heat", "Qi Deficiency"],
            "Skin Radiance":     ["Blood Deficiency", "Blood Stasis"],
        }
        targets = goal_map.get(health_goal, [])
        results = []
        for state in self.coherent_states:
            boost = 1.3 if state["TCM_Pattern"] in targets else 1.0
            prob = min(state["Coherence_Score"] * boost, 1.0)
            results.append((state["SNP_Marker"], round(prob, 3)))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def generate_all_recommendations(self, snp_list, symptoms):
        recs = [
            {"id": "MTHFR_CT", "text": "Supplement with Methylfolate (5-MTHF) + Vitamin B12", "type": "Supplement", "tcm_focus": ["Nourish Blood", "Tonify Liver"]},
            {"id": "COMT_AA",  "text": "Reduce catecholamines: avoid excess caffeine & stress", "type": "Lifestyle",  "tcm_focus": ["Soothe Liver Qi", "Calm Shen"]},
            {"id": "VDR_TA",   "text": "Optimize Vitamin D3 + K2 intake daily", "type": "Supplement", "tcm_focus": ["Warm Kidney Yang", "Strengthen Bones"]},
            {"id": "GSTP1_GG", "text": "Support detox with cruciferous vegetables & NAC", "type": "Nutrition",   "tcm_focus": ["Clear Damp-Heat", "Support Spleen"]},
            {"id": "MTR_AA",   "text": "Add B12 (methylcobalamin) + zinc supplementation", "type": "Supplement", "tcm_focus": ["Tonify Qi", "Support Lung"]},
            {"id": "NOS3_CT",  "text": "Support circulation with L-Arginine + Omega-3", "type": "Nutrition",   "tcm_focus": ["Invigorate Blood", "Open Heart"]},
        ]
        return [r for r in recs if r["id"] in snp_list]