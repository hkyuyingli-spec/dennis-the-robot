"""
NutriBot consultation-hint module (experimental, numpy only).

What it does
------------
1. A rule-based SAFETY GATE reads the user's text (English + Indonesian) and
   flags pregnancy, children, medication, cancer treatment, emergencies and
   crisis wording. These always win over everything else.
2. An optional quantum-inspired scoring step (DCE + MCC) that combines a
   genetic channel and a TCM channel. It is UNTRAINED, so while
   trained=False it can never pick "recommend_herb" or "recommend_supplement".
3. get_consultation_hint() returns ONE short sentence that app.py can append
   to the Groq system prompt. The LLM stays in charge of the answer.

Fixes versus the original script
--------------------------------
- No qutip (the original also crashed: H_C had the wrong dims).
- No process-dependent hash(); the personality uses a fixed mapping.
- Phase and salience are clamped instead of wrapping around with %.
- Coherence is computed from the two channels, not passed in.
- Expectation values are normalized to 0..1 (the original gave negatives).
- Inputs are validated; seeds are passed in, not global.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

ACTIONS = (
    "recommend_supplement",
    "recommend_herb",
    "suggest_diet",
    "refer_to_doctor",
    "ask_clarifying_question",
)
SAFE_WHEN_UNTRAINED = ("suggest_diet", "refer_to_doctor", "ask_clarifying_question")
PERSONALITIES = ("holistic", "analytical", "gentle", "direct")
MIN_CONFIDENCE = 0.35

# --------------------------------------------------------------------------
# 1. SAFETY GATE  (conservative on purpose; tune the lists as needed)
# --------------------------------------------------------------------------
_RULES = {
    "crisis": [
        r"\bsuicid\w*", r"\bkill myself\b", r"\bend my life\b", r"\bself[- ]harm\b",
        r"\bbunuh diri\b", r"\bingin mati\b", r"\bmelukai diri\b", r"\bmengakhiri hidup\b",
    ],
    "emergency": [
        r"\bchest pain\b", r"\bshortness of breath\b", r"\bblood in (my )?(stool|urine)\b",
        r"\bseizures?\b", r"\bfaint(ed|ing)?\b", r"\bstroke\b", r"\bsevere pain\b",
        r"\bnyeri dada\b", r"\bsakit dada\b", r"\bsesak napas\b", r"\bkejang\b",
        r"\bpingsan\b", r"\bdarah di (tinja|urin)\b", r"\bbab berdarah\b",
        r"\bkencing berdarah\b", r"\bnyeri hebat\b",
    ],
    "pregnancy": [
        r"\bpregnan\w*", r"\bbreast ?feeding\b", r"\bhamil\b", r"\bmengandung\b",
        r"\bmenyusui\b",
    ],
    "child": [
        r"\bchild(ren)?\b", r"\bkids?\b", r"\bbab(y|ies)\b", r"\binfants?\b",
        r"\btoddlers?\b", r"\banak\b", r"\bbayi\b", r"\bbalita\b",
    ],
    "medication": [
        r"\bblood thinners?\b", r"\banticoagulants?\b", r"\bwarfarin\b", r"\binsulin\b",
        r"\bmetformin\b", r"\bantidepressants?\b", r"\bprescription\b",
        r"\bpengencer darah\b", r"\bantikoagulan\b", r"\bobat resep\b",
        r"\bobat diabetes\b", r"\bobat hipertensi\b", r"\bobat tekanan darah\b",
        r"\bminum obat\b",
    ],
    "cancer_treatment": [
        r"\bchemo\w*", r"\bkemo\w*", r"\bradiotherap\w*", r"\bradioterap\w*",
        r"\bimmunotherap\w*", r"\bimunoterap\w*",
        r"\b(have|has|diagnosed with|undergoing|suffering from)\s+(a\s+)?(\w+\s+)?cancer\b",
        r"\b(menderita|terkena|kena|didiagnosis|mengidap)\s+(\w+\s+)?kanker\b",
    ],
}
# order = priority (crisis first)
_PRIORITY = ("crisis", "emergency", "pregnancy", "child", "medication", "cancer_treatment")
_COMPILED = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in _RULES.items()}


@dataclass(frozen=True)
class GateResult:
    triggered: bool
    reason: str = ""


def safety_gate(user_text: str) -> GateResult:
    """Return the highest-priority safety reason found in the text, if any."""
    text = (user_text or "").lower()
    for reason in _PRIORITY:
        if any(p.search(text) for p in _COMPILED[reason]):
            return GateResult(True, reason)
    return GateResult(False)


def quantum_safety_decision(user_text: str, enabled: bool = True) -> GateResult:
    """Fail open to the existing tab behavior if disabled or the gate errors."""
    if not enabled:
        return GateResult(False)
    try:
        return safety_gate(user_text)
    except Exception:
        return GateResult(False)


def quantum_tab_permissions(user_text: str, enabled: bool = True) -> dict:
    """Return the gate outcome and whether sensitive tab outputs are allowed."""
    gate = quantum_safety_decision(user_text, enabled)
    allowed = not gate.triggered
    return {
        "gate": gate,
        "show_recommendations": allowed,
        "call_groq": allowed,
        "build_pdf": allowed,
    }


def format_association_strength(label: str, strength: str) -> str:
    """Format the curated categorical association label without a score."""
    return f"{label}: {strength}"


# --------------------------------------------------------------------------
# 2. QUANTUM-INSPIRED SCORING (classical simulation, numpy only)
# --------------------------------------------------------------------------
def _validate_features(name: str, features, dim: int) -> np.ndarray:
    arr = np.asarray(features, dtype=float)
    if arr.ndim != 1 or arr.shape[0] != dim:
        raise ValueError(f"{name}: expected exactly {dim} values, got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name}: contains NaN or infinity")
    if np.any(arr < 0) or np.any(arr > 1):
        raise ValueError(f"{name}: values must be between 0 and 1")
    if not np.any(arr > 0):
        raise ValueError(f"{name}: all values are zero")
    return arr


def amplitude_encode(features: np.ndarray) -> np.ndarray:
    """Normalize to a unit vector (the 'quantum state')."""
    return features.astype(complex) / np.linalg.norm(features)


def _random_hermitian(dim: int, rng: np.random.Generator) -> np.ndarray:
    m = rng.standard_normal((dim, dim)) + 1j * rng.standard_normal((dim, dim))
    h = (m + m.conj().T) / 2
    return h / np.max(np.abs(np.linalg.eigvalsh(h)))  # eigenvalues now in [-1, 1]


def _score(state: np.ndarray, observable: np.ndarray) -> float:
    """Expectation value mapped from [-1, 1] to [0, 1]."""
    e = float(np.real(state.conj() @ observable @ state))
    return float(np.clip((e + 1.0) / 2.0, 0.0, 1.0))


@dataclass
class ConsultationState:
    """Where the user is in the consultation."""
    consultation_phase: int = 0       # 0 = new ... 8 = long-term follow-up
    knowledge_salience: int = 0       # 0-80
    personality: str = "holistic"

    def to_features(self, coherence: float) -> np.ndarray:
        phase = int(np.clip(self.consultation_phase, 0, 8))
        sal = int(np.clip(self.knowledge_salience, 0, 80))
        p_idx = PERSONALITIES.index(self.personality) if self.personality in PERSONALITIES else 0
        p_frac = p_idx / len(PERSONALITIES)
        return np.array([
            np.sin(2 * np.pi * phase / 9), np.cos(2 * np.pi * phase / 9),
            np.sin(2 * np.pi * sal / 81), np.cos(2 * np.pi * sal / 81),
            float(np.clip(coherence, 0, 1)),
            np.sin(2 * np.pi * p_frac), np.cos(2 * np.pi * p_frac),
        ])


class NutribotDCE_MCC:
    """Dual-Channel Evaluator + Meta-Cognitive Controller (untrained placeholder)."""

    def __init__(self, n_genetic_qubits: int = 3, n_tcm_qubits: int = 3,
                 hidden_dim: int = 24, seed: int = 42, trained: bool = False):
        self.dim_w = 2 ** n_genetic_qubits
        self.dim_x = 2 ** n_tcm_qubits
        self.trained = trained
        rng = np.random.default_rng(seed)
        self.H_W = _random_hermitian(self.dim_w, rng)
        self.H_X = _random_hermitian(self.dim_x, rng)
        self.H_C = _random_hermitian(self.dim_w * self.dim_x, rng)
        self.W_gate1 = rng.standard_normal((7, hidden_dim)) * 0.1
        self.b_gate1 = np.zeros(hidden_dim)
        self.W_gate2 = rng.standard_normal((hidden_dim, 3)) * 0.1
        self.b_gate2 = np.zeros(3)
        self.W_pol1 = rng.standard_normal((3, hidden_dim)) * 0.1
        self.b_pol1 = np.zeros(hidden_dim)
        self.W_pol2 = rng.standard_normal((hidden_dim, len(ACTIONS))) * 0.1
        self.b_pol2 = np.zeros(len(ACTIONS))

    def forward(self, genetic_features, tcm_features, state: ConsultationState,
                user_text: str = "") -> dict:
        gate = safety_gate(user_text)

        w_feat = _validate_features("genetic_features", genetic_features, self.dim_w)
        x_feat = _validate_features("tcm_features", tcm_features, self.dim_x)
        w, x = amplitude_encode(w_feat), amplitude_encode(x_feat)

        # Scores in 0..1, scaled by feature intensity so size is not lost
        e_w = _score(w, self.H_W) * float(w_feat.mean())
        e_x = _score(x, self.H_X) * float(x_feat.mean())
        e_c = _score(np.kron(w, x), self.H_C) * float(np.sqrt(w_feat.mean() * x_feat.mean()))

        coherence = 1.0 - abs(e_w - e_x)          # computed, not supplied

        h_gate = np.tanh(state.to_features(coherence) @ self.W_gate1 + self.b_gate1)
        gates = 1 / (1 + np.exp(-(h_gate @ self.W_gate2 + self.b_gate2)))
        gated = gates * np.array([e_w, e_x, e_c])

        logits = np.tanh(gated @ self.W_pol1 + self.b_pol1) @ self.W_pol2 + self.b_pol2
        probs = np.exp(logits - logits.max())
        probs /= probs.sum()

        if gate.triggered:
            action = "refer_to_doctor"
        elif not self.trained:
            # Transparent rule until real outcome data exists
            action = "ask_clarifying_question" if (coherence < 0.5 or e_x < 0.15) else "suggest_diet"
        elif probs.max() < MIN_CONFIDENCE:
            action = "ask_clarifying_question"
        else:
            action = ACTIONS[int(np.argmax(probs))]

        if not self.trained and action not in SAFE_WHEN_UNTRAINED:
            action = "ask_clarifying_question"

        return {
            "selected_action": action,
            "safety": {"triggered": gate.triggered, "reason": gate.reason},
            "action_probs": probs,   # not meaningful until trained=True
            "expectations": {"E_W": e_w, "E_X": e_x, "E_C": e_c},
            "gates": {"g_W": float(gates[0]), "g_X": float(gates[1]), "g_C": float(gates[2])},
            "coherence": coherence,
            "trained": self.trained,
        }


# --------------------------------------------------------------------------
# 3. HINT FOR THE LLM SYSTEM PROMPT (about 40 tokens at most)
# --------------------------------------------------------------------------
_HINTS = {
    "crisis": ("The user may be in distress: reply with warmth, urge them to contact local "
               "emergency services or a trusted person now, and give no herb or diet advice."),
    "emergency": ("Possible emergency symptoms: advise seeking urgent medical care first; "
                  "do not recommend herbs or supplements."),
    "pregnancy": ("User mentions pregnancy/breastfeeding: give only general guidance, "
                  "no specific herbs or supplements, and advise seeing a doctor."),
    "child": ("User mentions a child: give only general guidance, no herb or supplement "
              "doses, and advise seeing a pediatrician."),
    "medication": ("User mentions medication: warn about herb-drug interactions, recommend no "
                   "specific herbs or supplements, and advise checking with a doctor or pharmacist."),
    "cancer_treatment": ("User mentions cancer treatment: educational info only, no herbs or "
                         "supplements, and advise discussing with their oncology team."),
}
_CLARIFY = ("Query is vague: ask ONE short clarifying question (age, main symptom, how long) "
            "before giving advice.")


def get_consultation_hint(user_text: str, turn_count: int = 0) -> str:
    """Return one short sentence to append to the system prompt, or ''."""
    gate = safety_gate(user_text)
    if gate.triggered:
        return _HINTS[gate.reason]
    words = len((user_text or "").split())
    if turn_count == 0 and 0 < words <= 4:
        return _CLARIFY
    return ""
