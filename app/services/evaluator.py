
import json
import math
from datetime import datetime

from app.core.config import EVALUATION_PATH
from app.services.rag import generate_answer
from app.services.llm import get_llm
from app.services.retriever import get_embeddings


DATASET_PATH = EVALUATION_PATH / "evaluation_dataset.json"


def load_evaluation_dataset():
    """Load and validate the evaluation dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {DATASET_PATH}"
        )

    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list) or not data:
        raise ValueError(
            "Evaluation dataset must be a non-empty JSON list."
        )

    for index, item in enumerate(data):
        if not item.get("question") or not item.get("ground_truth"):
            raise ValueError(
                f"Question or ground_truth missing at row {index + 1}"
            )

    return data


def run_evaluation():
    """Run RAGAS evaluation and save actual results."""

    evaluation_data = load_evaluation_dataset()

    # Lazy loading: heavy libraries load only during evaluation
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
    )

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    # Step 1: Generate RAG answers
    for index, item in enumerate(evaluation_data, start=1):

        question = item["question"]

        print(
            f"Generating answer for question {index}/{len(evaluation_data)}"
        )

        result = generate_answer(question)

        questions.append(question)
        answers.append(result["answer"])
        contexts.append(result["retrieved_contexts"])
        ground_truths.append(item["ground_truth"])

    # Step 2: Create RAGAS dataset
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })

    print("Starting RAGAS evaluation...")

    # Step 3: Evaluate chatbot
    evaluation_result = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
        ],
        llm=get_llm(),
        embeddings=get_embeddings(),
    )

    # Step 4: Convert evaluation to records
    df = evaluation_result.to_pandas()

    records = (
        df.astype(object)
        .where(df.notna(), None)
        .to_dict(orient="records")
    )

    # Step 5: Calculate average scores
    numeric_means = df.mean(numeric_only=True).to_dict()

    average_scores = {}

    for key, value in numeric_means.items():

        if value is not None and math.isfinite(float(value)):
            average_scores[key] = round(float(value), 4)
        else:
            average_scores[key] = None

    # Step 6: Prepare final evaluation
    final_result = {
        "total_questions": len(questions),
        "scores": records,
        "average_scores": average_scores,
        "generated_at": datetime.now().isoformat(),
    }

    # Step 7: Save actual evaluation result
    EVALUATION_PATH.mkdir(parents=True, exist_ok=True)

    result_path = EVALUATION_PATH / "latest_evaluation.json"

    with open(result_path, "w", encoding="utf-8") as file:
        json.dump(
            final_result,
            file,
            indent=4,
            ensure_ascii=False,
            allow_nan=False,
        )

    print("RAGAS evaluation completed.")
    print(f"Evaluation saved at: {result_path}")

    return final_result


def load_saved_evaluation():
    """Load previously saved evaluation without calling Groq."""

    result_path = EVALUATION_PATH / "latest_evaluation.json"

    if not result_path.exists():
        raise FileNotFoundError(
            "No saved evaluation found. Run evaluation first."
        )

    with open(result_path, "r", encoding="utf-8") as file:
        return json.load(file)
