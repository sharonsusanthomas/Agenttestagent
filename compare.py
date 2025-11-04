import json
import os
import dspy
from dspy import LM
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

# ------------------- SETUP -------------------
console = Console()
EXPECTED_PATH = "outputs/expected_results.json"
ACTUAL_PATH = "outputs/agent_responses.json"
COMPARISON_OUTPUT = "outputs/comparison_report.json"

os.makedirs("outputs", exist_ok=True)

# ------------------- SETUP OPENAI MODEL -------------------
#os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
lm = LM("openai/gpt-4o-mini")
dspy.configure(lm=lm)

# ------------------- DSPY SIGNATURE FOR SEMANTIC COMPARISON -------------------
class SemanticComparisonSignature(dspy.Signature):
    """
    Compare two answers semantically to determine if they convey the same meaning.
    
    Output JSON format:
    {
        "are_equivalent": true/false,
        "similarity_score": 0-100,
        "reasoning": "Brief explanation of comparison"
    }
    """
    question: str = dspy.InputField(desc="The original question asked")
    expected_answer: str = dspy.InputField(desc="The expected/reference answer")
    actual_answer: str = dspy.InputField(desc="The actual answer given by the agent")
    comparison_json: str = dspy.OutputField(desc="JSON with are_equivalent, similarity_score, and reasoning")

# Initialize Chain of Thought comparator
semantic_comparator = dspy.ChainOfThought(SemanticComparisonSignature)

# ------------------- LOAD DATA -------------------
console.print("\n[bold cyan]📊 Loading Test Results...[/bold cyan]")

# Load expected results
if not os.path.exists(EXPECTED_PATH):
    console.print(f"[red]❌ Error: {EXPECTED_PATH} not found![/red]")
    exit(1)

with open(EXPECTED_PATH, "r", encoding="utf-8") as f:
    expected_results = json.load(f)

# Load actual results
if not os.path.exists(ACTUAL_PATH):
    console.print(f"[red]❌ Error: {ACTUAL_PATH} not found![/red]")
    console.print("[yellow]💡 Run ask_agent_save_responses.py first.[/yellow]")
    exit(1)

with open(ACTUAL_PATH, "r", encoding="utf-8") as f:
    actual_results = json.load(f)

console.print(f"[green]✅ Loaded {len(expected_results)} expected results[/green]")
console.print(f"[green]✅ Loaded {len(actual_results)} actual results[/green]\n")

# ------------------- SEMANTIC COMPARISON LOGIC -------------------
def compare_answers_semantic(question: str, expected: str, actual: str) -> dict:
    """Use DSPy Chain of Thought to semantically compare answers"""
    try:
        result = semantic_comparator(
            question=question,
            expected_answer=expected,
            actual_answer=actual
        )
        comparison_data = json.loads(result.comparison_json)
        return comparison_data
    except Exception as e:
        console.print(f"[yellow]⚠ Error in semantic comparison: {e}[/yellow]")
        # Fallback to simple word matching
        expected_words = set(expected.lower().split())
        actual_words = set(actual.lower().split())
        if not expected_words:
            similarity = 0
        else:
            intersection = expected_words.intersection(actual_words)
            similarity = (len(intersection) / len(expected_words)) * 100
        
        return {
            "are_equivalent": similarity >= 70,
            "similarity_score": round(similarity, 2),
            "reasoning": "Fallback word-based comparison due to error"
        }


console.print("[bold cyan]🔍 Comparing Results with Chain of Thought...[/bold cyan]\n")

comparison_results = []
passed = 0
failed = 0

for idx, (expected, actual) in enumerate(zip(expected_results, actual_results), 1):
    question = expected["question"]
    expected_answer = expected.get("expected_answer", "")
    actual_answer = actual.get("agent_answer", "")
    
    console.print(f"[dim]Analyzing test {idx}/{len(expected_results)}...[/dim]", end="\r")
    
    # Use semantic comparison with Chain of Thought
    comparison_data = compare_answers_semantic(question, expected_answer, actual_answer)
    
    are_equivalent = comparison_data.get("are_equivalent", False)
    similarity = comparison_data.get("similarity_score", 0)
    reasoning = comparison_data.get("reasoning", "")
    
    # Status determination
    if are_equivalent:
        status = "PASS"
        passed += 1
    elif similarity >= 70:
        status = "PARTIAL"
        passed += 1
    else:
        status = "FAIL"
        failed += 1
    
    comparison_results.append({
        "test_id": idx,
        "question": question,
        "expected_answer": expected_answer,
        "actual_answer": actual_answer,
        "status": status,
        "similarity_score": round(similarity, 2),
        "are_semantically_equivalent": are_equivalent,
        "reasoning": reasoning
    })

console.print(" " * 50, end="\r")  # Clear the progress line

# ------------------- SAVE COMPARISON REPORT -------------------
console.print("[bold cyan]💾 Saving Comparison Report...[/bold cyan]")

report = {
    "timestamp": datetime.now().isoformat(),
    "comparison_method": "DSPy Chain of Thought (Semantic)",
    "summary": {
        "total_tests": len(comparison_results),
        "passed": passed,
        "failed": failed,
        "pass_rate": round((passed / len(comparison_results)) * 100, 2) if comparison_results else 0
    },
    "comparisons": comparison_results
}

with open(COMPARISON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

console.print(f"[green]✅ Report saved to {COMPARISON_OUTPUT}[/green]\n")

# ------------------- DISPLAY SUMMARY TABLE -------------------
console.print("[bold cyan]📋 Comparison Summary[/bold cyan]\n")

table = Table(show_header=True, header_style="bold magenta", show_lines=True)
table.add_column("ID", style="dim", width=4, justify="center")
table.add_column("Question", width=30)
table.add_column("Expected", width=25)
table.add_column("Actual", width=25)
table.add_column("Score", width=8, justify="center")
table.add_column("Status", width=10, justify="center")

for comp in comparison_results:
    # Truncate long text for display
    question_short = comp["question"][:27] + "..." if len(comp["question"]) > 30 else comp["question"]
    expected_short = comp["expected_answer"][:22] + "..." if len(comp["expected_answer"]) > 25 else comp["expected_answer"]
    actual_short = comp["actual_answer"][:22] + "..." if len(comp["actual_answer"]) > 25 else comp["actual_answer"]
    
    # Color code status
    if comp["status"] == "PASS":
        status_display = "[green]✅ PASS[/green]"
    elif comp["status"] == "PARTIAL":
        status_display = "[yellow]⚠ PARTIAL[/yellow]"
    else:
        status_display = "[red]❌ FAIL[/red]"
    
    similarity_display = f"{comp['similarity_score']}%"
    
    table.add_row(
        str(comp["test_id"]),
        question_short,
        expected_short,
        actual_short,
        similarity_display,
        status_display
    )

console.print(table)

# ------------------- DISPLAY STATISTICS -------------------
console.print("\n")
stats_panel = Panel(
    f"""[bold]Total Tests:[/bold] {report['summary']['total_tests']}
[bold green]Passed:[/bold green] {report['summary']['passed']}
[bold red]Failed:[/bold red] {report['summary']['failed']}
[bold]Pass Rate:[/bold] {report['summary']['pass_rate']}%

[dim]Comparison Method: DSPy Chain of Thought (Semantic Analysis)[/dim]""",
    title="[bold cyan]Test Statistics[/bold cyan]",
    border_style="cyan"
)
console.print(stats_panel)

# ------------------- SHOW FAILED CASES -------------------
failed_cases = [c for c in comparison_results if c["status"] == "FAIL"]

if failed_cases:
    console.print("\n[bold red]❌ Failed Test Cases:[/bold red]\n")
    
    for fail in failed_cases:
        fail_panel = Panel(
            f"""[yellow]Question:[/yellow] {fail['question']}

[green]Expected:[/green]
{fail['expected_answer']}

[red]Actual:[/red]
{fail['actual_answer']}

[cyan]AI Reasoning:[/cyan]
{fail['reasoning']}

[dim]Similarity Score: {fail['similarity_score']}%[/dim]""",
            title=f"[bold red]Test #{fail['test_id']} - FAILED[/bold red]",
            border_style="red"
        )
        console.print(fail_panel)
else:
    console.print("\n[bold green]🎉 All tests passed![/bold green]\n")

# ------------------- SHOW PASSED CASES WITH REASONING -------------------
console.print("\n[bold green]✅ Passed Test Cases (Sample):[/bold green]\n")

passed_cases = [c for c in comparison_results if c["status"] in ["PASS", "PARTIAL"]][:3]

for passed_case in passed_cases:
    passed_panel = Panel(
        f"""[yellow]Question:[/yellow] {passed_case['question']}

[green]Expected:[/green]
{passed_case['expected_answer']}

[blue]Actual:[/blue]
{passed_case['actual_answer']}

[cyan]AI Reasoning:[/cyan]
{passed_case['reasoning']}

[dim]Similarity Score: {passed_case['similarity_score']}%[/dim]""",
        title=f"[bold green]Test #{passed_case['test_id']} - {passed_case['status']}[/bold green]",
        border_style="green"
    )
    console.print(passed_panel)