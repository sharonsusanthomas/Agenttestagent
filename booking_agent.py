import os
import dspy
from dspy import LM

# ------------------- SETUP OPENAI MODEL -------------------
#os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "sk-xxx")
lm = LM("openai/gpt-4o-mini")
dspy.configure(lm=lm)


# ------------------- BOOKING AGENT SIGNATURE -------------------
class BookingAgentSignature(dspy.Signature):
    """
    A helpful booking agent that assists users with venue/room bookings.
    
    The agent should:
    - Ask for missing information (campus, date, time, room type)
    - Provide helpful responses
    - Confirm bookings when all details are provided
    """
    user_query: str = dspy.InputField(desc="The user's booking-related query or request.")
    agent_response: str = dspy.OutputField(desc="The agent's helpful response to the user.")


# ------------------- BOOKING AGENT CLASS -------------------
class BookingAgent:
    def __init__(self):
        self.agent = dspy.ChainOfThought(BookingAgentSignature)
    
    def respond(self, user_query: str) -> str:
        """
        Process a user query and return the agent's response.
        
        Args:
            user_query: The user's input/question
            
        Returns:
            The agent's response string (without "Agent:" prefix)
        """
        try:
            result = self.agent(user_query=user_query)
            response = result.agent_response.strip()
            
            # Remove "Agent:" prefix if present (case insensitive)
            import re
            response = re.sub(r'^(agent)\s*:\s*', '', response, flags=re.IGNORECASE)
            
            return response.strip()
        except Exception as e:
            return f"I apologize, I encountered an error: {str(e)}"


# ------------------- STANDALONE USAGE -------------------
if __name__ == "__main__":
    from rich.console import Console
    
    console = Console()
    agent = BookingAgent()
    
    console.print("\n[bold cyan]🎯 Booking Agent Interactive Mode[/bold cyan]")
    console.print("[dim]Type your booking queries. Type 'exit' to quit.[/dim]\n")
    
    while True:
        user_input = console.input("[yellow]User:[/yellow] ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break
        if not user_input:
            continue
        
        response = agent.respond(user_input)
        console.print(f"[green]{response}[/green]\n")