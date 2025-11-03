import json
import os
from modules.test_case_processor import process_test_case
from rich.console import Console

# ---------------- SETUP ----------------
os.makedirs("outputs", exist_ok=True)
OUTPUT_PATH = "outputs/test_cases.json"

console = Console()
console.print("\n[bold cyan]🧠 DSPy Interactive Test Case Agent[/bold cyan]")
console.print("[dim]Type a test case (Q&A or behavioral). Type 'exit' to quit.[/dim]\n")

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
    user_input = console.input("[yellow]🧾 Enter Test Case:[/yellow] ").strip()
    if user_input.lower() in ["exit", "quit"]:
        break
    if not user_input:
        continue

    result = process_test_case(user_input)

    # 🎯 Extract only what we want
    compact_case = {
        "input_prompt": result.get("input_prompt"),
        "expected_output": result.get("expected_output")
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
