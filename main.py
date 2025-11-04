import json
import os
import re
from modules.test_case_processor import process_test_case
from rich.console import Console

# ---------------- SETUP ----------------
os.makedirs("outputs", exist_ok=True)
OUTPUT_PATH = "outputs/test_cases.json"

console = Console()
console.print("\n[bold cyan]🧠 DSPy Interactive Test Case Agent[/bold cyan]")
console.print("[dim]Type a test case (Q&A or behavioral). Type 'exit' to quit.[/dim]\n")

# ---------------- CLEANING FUNCTIONS ----------------
def clean_to_one_sentence(text,
                          allowed_punct=".,?:-()",
                          normalize_dashes=True):
    """Clean text to a single sentence with normalized punctuation"""
    # 1) normalize common dash characters to ascii hyphen
    if normalize_dashes:
        text = re.sub(r"[\u2012\u2013\u2014\u2015]", "-", text)

    # 2) collapse newlines and tabs to single space
    text = re.sub(r"[\r\n\t]+", " ", text)

    # 3) remove characters NOT in allowed set (letters, digits, spaces, allowed punctuation)
    safe_punct = re.escape(allowed_punct)
    pattern = rf"[^A-Za-z0-9\s{safe_punct}]"
    text = re.sub(pattern, "", text)

    # 4) collapse multiple spaces to single space, trim ends
    text = re.sub(r"\s+", " ", text).strip()

    # 5) keep up to the first sentence terminator (. ? !)
    m = re.search(r"[.?!]", text)
    if m:
        text = text[: m.end()]
    return text


def clean_text(text: str) -> str:
    """Remove 'User:', 'Agent:' prefixes and clean whitespace"""
    if not text:
        return text
    text = text.strip()
    # Remove "User:" or "Agent:" prefix (case insensitive)
    text = re.sub(r'^(user|agent)\s*:\s*', '', text, flags=re.IGNORECASE)
    return text.strip()


# ---------------- LOAD EXISTING DATA ----------------
if os.path.exists(OUTPUT_PATH):
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            all_cases = json.load(f)
            if not isinstance(all_cases, list):
                all_cases = []
    except json.JSONDecodeError:
        all_cases = []
else:
    all_cases = []

# ---------------- INTERACTIVE LOOP ----------------
while True:
    console.print("[yellow]🧾 Enter Test Case (press Enter twice to submit):[/yellow]")
    
    # Collect multi-line input
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    
    user_input = "\n".join(lines).strip()
    
    if user_input.lower() in ["exit", "quit"]:
        break
    if not user_input:
        continue

    result = process_test_case(user_input)

    # 🎯 Extract, CLEAN, and normalize to single sentence
    raw_input = result.get("input_prompt", "")
    raw_output = result.get("expected_output", "")
    
    # First clean prefixes, then normalize to one sentence
    compact_case = {
        "input_prompt": clean_to_one_sentence(clean_text(raw_input)),
        "expected_output": clean_to_one_sentence(clean_text(raw_output))
    }

    console.print(f"\n[green]✅ Saved Case:[/green]\n{json.dumps(compact_case, indent=2)}")

    # Optional: skip duplicates
    if not any(
        c["input_prompt"] == compact_case["input_prompt"]
        and c["expected_output"] == compact_case["expected_output"]
        for c in all_cases
    ):
        all_cases.append(compact_case)
    else:
        console.print("[yellow]⚠ Duplicate case skipped.[/yellow]")

# ---------------- SAVE TO FILE ----------------
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(all_cases, f, indent=2)

console.print(f"\n[bold green]✅ Test cases saved to {OUTPUT_PATH}[/bold green]")