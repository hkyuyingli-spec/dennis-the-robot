import ast
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest

from nutribot import dce_mcc as m
from nutribot.core.translations import TRANSLATIONS

G = np.array([0.9, 0.3, 0.7, 0.5, 0.4, 0.6, 0.2, 0.8])
X = np.array([0.85, 0.3, 0.2, 0.6, 0.45, 0.7, 0.35, 0.5])


def run(text="", **kw):
    return m.NutribotDCE_MCC(**kw).forward(G, X, m.ConsultationState(2, 30, "analytical"), text)


def test_runs_and_probabilities_valid():
    r = run()
    assert np.isclose(r["action_probs"].sum(), 1.0)
    assert not np.any(np.isnan(r["action_probs"]))
    assert 0 <= r["coherence"] <= 1
    assert all(0 <= v <= 1 for v in r["expectations"].values())


def test_same_input_same_output():
    assert run()["selected_action"] == run()["selected_action"]
    assert np.allclose(run()["action_probs"], run()["action_probs"])


def test_reproducible_across_processes():
    code = ("import numpy as np; from nutribot import dce_mcc as m;"
            "G=np.array([.9,.3,.7,.5,.4,.6,.2,.8]);X=np.array([.85,.3,.2,.6,.45,.7,.35,.5]);"
            "r=m.NutribotDCE_MCC().forward(G,X,m.ConsultationState(2,30,'analytical'));"
            "print(round(float(r['action_probs'][0]),10), r['selected_action'])")
    outs = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           env={"PYTHONHASHSEED": s, "PATH": ""}, check=True).stdout
            for s in ("1", "999")}
    assert len(outs) == 1


@pytest.mark.parametrize("text", [
    "I am pregnant, what herbs can I take?", "Saya sedang hamil, herbal apa yang aman?",
    "my baby has a cough", "anak saya demam", "I take blood thinners daily",
    "saya minum obat diabetes", "I am undergoing chemotherapy", "sedang kemoterapi",
    "I have chest pain", "nyeri dada sejak pagi", "I want to kill myself", "ingin mati saja",
    "I was diagnosed with breast cancer", "saya didiagnosis kanker payudara",
])
def test_safety_gate_refers(text):
    assert run(text)["selected_action"] == "refer_to_doctor"
    assert m.get_consultation_hint(text) != ""


@pytest.mark.parametrize("text", [
    "What foods help Qi deficiency?", "kidney health tips", "What is cancer?",
    "Makanan apa yang baik untuk pencernaan?",
])
def test_no_false_positive(text):
    assert not m.safety_gate(text).triggered


def test_untrained_never_recommends_herbs_or_supplements():
    for seed in range(30):
        assert run(seed=seed)["selected_action"] in m.SAFE_WHEN_UNTRAINED


@pytest.mark.parametrize("bad", [
    np.ones(5), np.array([np.nan] + [0.5] * 7), np.array([np.inf] + [0.5] * 7),
    np.zeros(8), np.array([2.0] + [0.5] * 7), [],
])
def test_invalid_inputs_raise(bad):
    with pytest.raises(ValueError):
        m.NutribotDCE_MCC().forward(bad, X, m.ConsultationState())


def test_phase_clamped_not_wrapped():
    a = m.ConsultationState(9).to_features(0.5)
    b = m.ConsultationState(8).to_features(0.5)
    c = m.ConsultationState(0).to_features(0.5)
    assert np.allclose(a, b) and not np.allclose(a, c)


def test_hints_short_and_empty_when_not_needed():
    assert m.get_consultation_hint("Explain how Qi relates to digestion in detail please") == ""
    for t in ("pregnant", "I want to kill myself", "chest pain", "blood thinners"):
        assert len(m.get_consultation_hint(t)) <= 200
    assert m.get_consultation_hint("tired", 0) != ""
    assert m.get_consultation_hint("tired", 3) == ""


def test_imports_without_qutip():
    code = "import sys; sys.modules['qutip']=None; from nutribot import dce_mcc"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0


@pytest.mark.parametrize("text", [
    "I am pregnant", "saya sedang hamil", "my baby is sick", "anak saya sakit",
    "I take warfarin", "saya minum obat diabetes", "I am in chemotherapy",
    "saya menjalani kemoterapi", "I have chest pain", "saya sesak napas",
    "I want to kill myself", "saya ingin bunuh diri",
])
def test_quantum_tab_gate_blocks_recommendations_groq_and_pdf(text):
    recommendation_work = Mock()
    groq_call = Mock()
    pdf_build = Mock()
    permissions = m.quantum_tab_permissions(text, enabled=True)
    if permissions["show_recommendations"]:
        recommendation_work()
    if permissions["call_groq"]:
        groq_call()
    if permissions["build_pdf"]:
        pdf_build()
    assert permissions["gate"].triggered
    recommendation_work.assert_not_called()
    groq_call.assert_not_called()
    pdf_build.assert_not_called()


def test_quantum_tab_gate_allows_normal_text():
    permissions = m.quantum_tab_permissions("Occasional fatigue after work", enabled=True)
    assert not permissions["gate"].triggered
    assert permissions["show_recommendations"]
    assert permissions["call_groq"]


def test_quantum_tab_flag_off_skips_gate(monkeypatch):
    gate = Mock(side_effect=AssertionError("gate should not run when disabled"))
    monkeypatch.setattr(m, "safety_gate", gate)
    permissions = m.quantum_tab_permissions("pregnant", enabled=False)
    assert not permissions["gate"].triggered
    assert permissions["call_groq"]
    gate.assert_not_called()


def test_quantum_tab_gate_error_fails_open(monkeypatch):
    monkeypatch.setattr(m, "safety_gate", Mock(side_effect=RuntimeError("test failure")))
    permissions = m.quantum_tab_permissions("chest pain", enabled=True)
    assert not permissions["gate"].triggered
    assert permissions["show_recommendations"]
    assert permissions["call_groq"]


def _mock_quantum_pdf(language, explanation_text="AI explanation 😀 with 中文"):
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    app_tree = ast.parse(app_path.read_text(encoding="utf-8"))
    helper_nodes = [
        node for node in app_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"_pdf_latin1_text", "_build_quantum_pdf"}
    ]
    namespace = {}
    exec(compile(ast.Module(body=helper_nodes, type_ignores=[]), str(app_path), "exec"), namespace)

    class FakePdf:
        def __init__(self):
            self.text = []

        def add_page(self): pass
        def set_font(self, *args, **kwargs): pass
        def ln(self, *args, **kwargs): pass
        def cell(self, *args, **kwargs): self.text.append(kwargs["txt"])
        def multi_cell(self, *args, **kwargs): self.text.append(kwargs["txt"])
        def output(self, dest): return "\n".join(self.text)

    fake_pdf = FakePdf()
    result = namespace["_build_quantum_pdf"](
        lambda: fake_pdf,
        language,
        TRANSLATIONS[language],
        TRANSLATIONS,
        "Better Sleep",
        ["MTHFR_CT"],
        "Herbal text 🌿 with 中文",
        explanation_text,
    )
    return result, "\n".join(fake_pdf.text)


def test_quantum_disclaimer_is_used_in_result_and_pdf_content():
    app_source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert 'st.markdown(quantum_strings["footer_disclaimer"])' in app_source
    for language in ("en", "id", "zh"):
        _, pdf_content = _mock_quantum_pdf(language)
        disclaimer = TRANSLATIONS["en"]["footer_disclaimer"] if language == "zh" else TRANSLATIONS[language]["footer_disclaimer"]
        expected = "".join(char for char in disclaimer if ord(char) <= 255 and (char >= " " or char in "\n\r\t"))
        assert expected in pdf_content


def test_quantum_goal_is_not_printed_to_stdout():
    core_source = (Path(__file__).resolve().parents[1] / "nutribot/core/yuanying_core.py").read_text(encoding="utf-8")
    assert "format(goal=user_goal)" not in core_source


def test_association_label_has_no_percent_or_numeric_score():
    label = m.format_association_strength("Association strength (from curated table)", "STRONG")
    assert label.endswith("STRONG")
    assert "%" not in label
    assert not any(character.isdigit() for character in label)
    app_source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    assert "prob*100" not in app_source
    assert "Confidence Level:" not in app_source


def test_all_new_quantum_texts_exist_in_all_supported_languages():
    keys = (
        "quantum_safety_notice", "quantum_crisis_notice", "quantum_unused_inputs",
        "quantum_privacy_note", "quantum_association_strength",
    )
    for language in ("en", "id", "zh"):
        assert all(TRANSLATIONS[language].get(key) for key in keys)


def test_mocked_quantum_pdf_generation_is_latin1_safe_for_all_languages():
    for language in ("en", "id", "zh"):
        result, _ = _mock_quantum_pdf(language)
        decoded = result.decode("latin-1")
        assert decoded
        assert "🌿" not in decoded and "😀" not in decoded and "中文" not in decoded
