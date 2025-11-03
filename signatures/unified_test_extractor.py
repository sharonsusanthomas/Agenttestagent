import dspy

class UnifiedTestCaseExtractorSignature(dspy.Signature):
    """
    Extracts question and expected answer from a Q&A-style test case.

    Expected Output JSON:
    {
        "input_prompt": "<question>",
        "expected_output": "<agent's expected answer>"
    }
    """
    test_case_type: str = dspy.InputField(desc="Type of test case.")
    raw_text: str = dspy.InputField(desc="Raw text containing the question and answer.")
    structured_json: str = dspy.OutputField(desc="Structured JSON output.")
