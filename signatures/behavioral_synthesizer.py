import dspy

class BehavioralSynthesizerSignature(dspy.Signature):
    """
    Generate a synthetic Q&A pair for a behavioral description.

    Example:
    Input: "When the user asks to book without details, ask for campus."
    Output:
    {
        "synthetic_input": "User: I would like to book a venue.",
        "synthetic_expected_output": "Agent: Which campus would you like to book at?"
    }
    """
    behavior_description: str = dspy.InputField(desc="Behavioral test description text.")
    synthesized_json: str = dspy.OutputField(desc="JSON with synthetic_input and synthetic_expected_output.")
