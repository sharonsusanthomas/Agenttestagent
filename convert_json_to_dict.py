import json
import os
from rich.console import Console

# ------------------- SETUP -------------------
console = Console()
INPUT_PATH = "outputs/test_cases.json"
OUTPUT_PATH = "outputs/expected_results.json"

os.makedirs("outputs", exist_ok=True)

# ------------------- LOAD JSON -------------------
console.print("\n[bold cyan]📂 Loading Test Cases JSON...[/bold cyan]")

if not os.path.exists(INPUT_PATH):
    console.print(f"[red]❌ Error: {INPUT_PATH} not found![/red]")
    console.print("[yellow]💡 Run main.py first to generate test cases.[/yellow]")
    exit(1)

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    test_cases_json = json.load(f)

console.print(f"[green]✅ Loaded {len(test_cases_json)} test cases[/green]")

# ------------------- CONVERT TO DICTIONARY -------------------
console.print("\n[bold cyan]🔄 Converting to Dictionary List...[/bold cyan]")

expected_results = []

for tc in test_cases_json:
    expected_results.append({
        "question": tc.get("input_prompt", ""),
        "expected_answer": tc.get("expected_output", "")
    })

console.print(f"[green]✅ Converted {len(expected_results)} entries[/green]")

# ------------------- SAVE DICTIONARY -------------------
console.print("\n[bold cyan]💾 Saving Dictionary...[/bold cyan]")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(expected_results, f, indent=2, ensure_ascii=False)

console.print(f"[green]✅ Dictionary saved to {OUTPUT_PATH}[/green]")

# ------------------- PREVIEW -------------------
console.print("\n[bold cyan]👀 Preview (First 3 entries):[/bold cyan]")
for i, entry in enumerate(expected_results[:3], 1):
    console.print(f"\n[yellow]Entry {i}:[/yellow]")
    console.print(f"  Question: {entry['question']}")
    console.print(f"  Expected: {entry['expected_answer']}")

console.print(f"\n[dim]Total entries: {len(expected_results)}[/dim]\n")