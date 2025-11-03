import json
import os
from booking_agent import BookingAgent
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# ------------------- SETUP -------------------
console = Console()
INPUT_PATH = "outputs/expected_results.json"
OUTPUT_PATH = "outputs/agent_responses.json"

os.makedirs("outputs", exist_ok=True)

# ------------------- LOAD QUESTIONS -------------------
console.print("\n[bold cyan]📂 Loading Questions...[/bold cyan]")

if not os.path.exists(INPUT_PATH):
    console.print(f"[red]❌ Error: {INPUT_PATH} not found![/red]")
    console.print("[yellow]💡 Run convert_json_to_dict.py first.[/yellow]")
    exit(1)

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    expected_results = json.load(f)

console.print(f"[green]✅ Loaded {len(expected_results)} questions[/green]")

# ------------------- INITIALIZE AGENT -------------------
console.print("\n[bold cyan]🤖 Initializing Booking Agent...[/bold cyan]")
agent = BookingAgent()
console.print("[green]✅ Agent ready[/green]\n")

# ------------------- ASK AGENT FOR EACH QUESTION -------------------
console.print("[bold cyan]💬 Asking Agent Questions...[/bold cyan]\n")

agent_responses = []

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console,
) as progress:
    
    task = progress.add_task("[cyan]Processing questions...", total=len(expected_results))
    
    for idx, entry in enumerate(expected_results, 1):
        question = entry["question"]
        
        progress.update(task, description=f"[cyan]Processing {idx}/{len(expected_results)}: {question[:50]}...")
        
        # Ask the agent
        agent_answer = agent.respond(question)
        
        # Save the response
        agent_responses.append({
            "question": question,
            "agent_answer": agent_answer
        })
        
        progress.update(task, advance=1)

console.print(f"\n[green]✅ Collected {len(agent_responses)} responses[/green]")

# ------------------- SAVE AGENT RESPONSES -------------------
console.print("\n[bold cyan]💾 Saving Agent Responses...[/bold cyan]")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(agent_responses, f, indent=2, ensure_ascii=False)

console.print(f"[green]✅ Responses saved to {OUTPUT_PATH}[/green]")

# ------------------- PREVIEW -------------------
console.print("\n[bold cyan]👀 Preview (First 3 responses):[/bold cyan]")
for i, entry in enumerate(agent_responses[:3], 1):
    console.print(f"\n[yellow]Response {i}:[/yellow]")
    console.print(f"  Question: {entry['question']}")
    console.print(f"  Agent Answer: {entry['agent_answer']}")

console.print(f"\n[dim]Total responses: {len(agent_responses)}[/dim]\n")