
from app.services.report_generator import generate_reports

# Sample evaluation data (No Groq API required)
sample_evaluation = {
    "total_questions": 1,

    "scores": [
        {
            "user_input": "How many casual leaves?",
            "response": "Employees receive 12 casual leaves each year.",
            "reference": "Employees receive 12 casual leaves every year.",
            "faithfulness": 1.0,
            "answer_relevancy": 0.98,
            "context_precision": 1.0,
            "context_recall": 1.0,
            "retrieved_contexts": [
                "Employees receive 12 casual leaves every year."
            ]
        }
    ],

    "average_scores": {
        "faithfulness": 1.0,
        "answer_relevancy": 0.98,
        "context_precision": 1.0,
        "context_recall": 1.0
    }
}

# Generate reports
result = generate_reports(sample_evaluation)

print("\nREPORT GENERATION RESULT")
print(result)
