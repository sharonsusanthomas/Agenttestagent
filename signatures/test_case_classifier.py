import dspy

class TestCaseTypeClassifierSignature(dspy.Signature):
    """
    Detect whether a given test case input is a Q&A-style test or a behavioral/expectation test.

    OUTPUT FORMAT
    -------------
    {
        "test_case_type": "qa_test" | "behavioral_test",
        "reasoning": "Brief reasoning for classification"
    }
    """
    test_input: str = dspy.InputField(desc="Raw text of the test case input.")
    classification_json: str = dspy.OutputField(desc="JSON with test_case_type and reasoning.")
