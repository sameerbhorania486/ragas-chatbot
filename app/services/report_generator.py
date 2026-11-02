
import csv
import json
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import REPORTS_PATH


def generate_reports(evaluation):
    """Generate JSON, CSV and PDF evaluation reports."""

    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = REPORTS_PATH / f"evaluation_{timestamp}.json"
    csv_path = REPORTS_PATH / f"evaluation_{timestamp}.csv"
    pdf_path = REPORTS_PATH / f"evaluation_{timestamp}.pdf"

    # 1. JSON REPORT
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(evaluation, file, indent=4, ensure_ascii=False, allow_nan=False)

    # 2. CSV REPORT
    scores = evaluation.get("scores", [])

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:
        fieldnames = [
            "user_input",
            "response",
            "reference",
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
            "retrieved_contexts",
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in scores:
            csv_row = {
                key: row.get(key)
                for key in fieldnames
                if key != "retrieved_contexts"
            }

            csv_row["retrieved_contexts"] = "\n\n".join(
                row.get("retrieved_contexts") or []
            )

            writer.writerow(csv_row)

    # 3. PDF REPORT
    styles = getSampleStyleSheet()
    story = []

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    story.append(
        Paragraph("RAGAS Evaluation Report", styles["Title"])
    )
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Total Questions: {evaluation.get('total_questions', 0)}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 20))

    story.append(
        Paragraph("Average Evaluation Scores", styles["Heading2"])
    )

    average_scores = evaluation.get("average_scores", {})

    table_data = [["Metric", "Average Score"]]

    for metric, score in average_scores.items():
        display_score = (
            f"{score:.4f}" if isinstance(score, (int, float)) else "N/A"
        )
        table_data.append([metric.replace("_", " ").title(), display_score])

    score_table = Table(table_data, colWidths=[3.5 * inch, 2 * inch])

    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243B53")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("ALIGN", (1, 1), (1, -1), "CENTER"),
    ]))

    story.append(score_table)
    story.append(Spacer(1, 20))

    story.append(
        Paragraph("Question-wise Evaluation", styles["Heading2"])
    )

    for index, row in enumerate(scores, start=1):
        story.append(
            Paragraph(
                f"Question {index}: {row.get('user_input', '')}",
                styles["Heading3"],
            )
        )

        story.append(
            Paragraph(
                f"Answer: {row.get('response', '')}",
                styles["BodyText"],
            )
        )

        story.append(
            Paragraph(
                f"Ground Truth: {row.get('reference', '')}",
                styles["BodyText"],
            )
        )

        story.append(Spacer(1, 8))

    document.build(story)

    return {
        "json_report": str(json_path),
        "csv_report": str(csv_path),
        "pdf_report": str(pdf_path),
        "status": "generated",
    }
