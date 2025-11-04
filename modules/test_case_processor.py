import os
import re
import json
import dspy
from dspy import LM
from signatures.test_case_classifier import TestCaseTypeClassifierSignature
from signatures.unified_test_extractor import UnifiedTestCaseExtractorSignature
from signatures.behavioral_synthesizer import BehavioralSynthesizerSignature

# ------------------- SETUP OPENAI MODEL -------------------
#os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-proj-xxx")
lm = LM("openai/gpt-4o-mini")
dspy.configure(lm=lm)

# ✅ Use ChainOfThought instead of Predict
classifier_llm = dspy.ChainOfThought(TestCaseTypeClassifierSignature)
extractor_llm = dspy.ChainOfThought(UnifiedTestCaseExtractorSignature)
synthesizer_llm = dspy.ChainOfThought(BehavioralSynthesizerSignature)


# ------------------- NORMALIZATION HELPERS -------------------
def normalize_text_sentence(s: str) -> str:
    s = re.sub(r"\s*,\s*", ", ", s.strip())
    s = re.sub(r"\s+", " ", s)
    if not s:
        return s
    if not s.endswith((".", "?", "!")):
        s += "."
    return s[0].upper() + s[1:]


def canonicalize_expected_output(raw_expected: str) -> (str, dict):
    text = raw_expected.strip()
    if re.match(r"^\s*agent\s*[:\-]\s*", text, re.I):
        clean = re.sub(r"^\s*agent\s*[:\-]\s*", "", text, flags=re.I).strip()
        return "Agent: " + normalize_text_sentence(clean), {"normalization": "agent_prefix_preserved"}

    if "ask" in text.lower() or "," in text or "and" in text.lower():
        t = re.sub(r"\b(ask|please|provide|give|send|enter)\b", "", text, flags=re.I)
        t = re.sub(r"[:;]+", ",", t)
        t = re.sub(r"\s*,\s*", ", ", t)
        t = re.sub(r"\s+", " ", t).strip(" ,.")
        canonical = f"Agent: To help you, please provide {t}."
        return normalize_text_sentence(canonical), {"normalization": "list_to_agent_reply"}

    return "Agent: " + normalize_text_sentence(text), {"normalization": "fallback_agent_prefix"}


# ------------------- CLASSIFICATION -------------------
def classify_with_rules(text: str):
    t = text.strip().lower()
    if ("question" in t and "answer" in t) or ("?" in t and "answer" in t):
        return {
            "test_case_type": "qa_test",
            "reasoning": "Contains explicit Q&A pattern with a question and answer."
        }
    if re.match(r"^(when|if)\b", t) or "should" in t or "first ask" in t:
        return {
            "test_case_type": "behavioral_test",
            "reasoning": "Rule-based: starts with behavioral cue (when/if/should/first ask)."
        }

    # ⚙️ LLM reasoning using ChainOfThought
    llm_resp = classifier_llm(test_input=text)
    return json.loads(llm_resp.classification_json)


# ------------------- MAIN PROCESS -------------------
def process_test_case(raw_text: str):
    cls = classify_with_rules(raw_text)
    test_type = cls["test_case_type"]

    if test_type == "qa_test":
        out = extractor_llm(test_case_type=test_type, raw_text=raw_text)
        structured = json.loads(out.structured_json)

    elif test_type == "behavioral_test":
        synth = synthesizer_llm(behavior_description=raw_text)
        temp = json.loads(synth.synthesized_json)
        structured = {
            "input_prompt": temp.get("synthetic_input"),
            "expected_output": temp.get("synthetic_expected_output"),
            "metadata": {"generated_from": "behavioral_synthesizer"}
        }
    else:
        structured = {"error": "Unknown test case type."}

    raw_expected = structured.get("expected_output") or structured.get("synthetic_expected_output")
    if raw_expected:
        canonical, meta = canonicalize_expected_output(raw_expected)
        structured["expected_output"] = canonical
        existing_meta = structured.get("metadata", {})
        existing_meta.update(meta)
        structured["metadata"] = existing_meta

    return {
        "original_text": raw_text,
        "test_case_type": test_type,
        "reasoning": cls.get("reasoning", ""),
        "input_prompt": structured.get("input_prompt"),
        "expected_output": structured.get("expected_output"),
        "metadata": structured.get("metadata", {})
    }
