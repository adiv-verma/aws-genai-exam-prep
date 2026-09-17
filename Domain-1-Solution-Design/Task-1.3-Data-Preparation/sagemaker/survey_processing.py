import argparse
import json
import os

import pandas as pd

RATING_MAP = {
    "Very Dissatisfied": 1,
    "Dissatisfied": 2,
    "Neutral": 3,
    "Satisfied": 4,
    "Very Satisfied": 5,
}


def generate_summary(row):
    score = row["overall_satisfaction"]
    level = "satisfied" if score >= 4 else "neutral" if score == 3 else "dissatisfied"
    summary = f"Customer {row['customer_id']} was {level} overall (score {score}/5) with their TechSound wireless earbuds experience. "
    summary += f"They rated the product {row['product_rating']}/5 and customer service {row['service_rating']}/5. "
    if pd.notna(row.get("improvement_area")) and str(row.get("improvement_area")).lower() != "none":
        summary += f"They suggested improvement in the area of {row['improvement_area']}. "
    if pd.notna(row.get("comments")) and len(str(row.get("comments"))) > 0:
        summary += f"Comments: \"{row['comments']}\""
    return summary.strip()


def process_survey_data(input_path, output_path):
    # keep_default_na=False: the CSV uses the literal string "None" to mean
    # "no improvement area suggested" - pandas' default na_values list treats
    # "None" as a missing-value token and silently turns it into NaN otherwise.
    df = pd.read_csv(os.path.join(input_path, "surveys.csv"), keep_default_na=False)
    df = df.dropna(subset=["customer_id", "survey_date"])

    for col in df.columns:
        if "rating" in col.lower() or "satisfaction" in col.lower():
            if df[col].dtype == object:
                df[col] = df[col].map(RATING_MAP).fillna(df[col])

    summary_stats = {
        "total_surveys": int(len(df)),
        "avg_satisfaction": round(float(df["overall_satisfaction"].mean()), 2),
        "avg_product_rating": round(float(df["product_rating"].mean()), 2),
        "avg_service_rating": round(float(df["service_rating"].mean()), 2),
        "satisfaction_distribution": {
            str(k): int(v) for k, v in df["overall_satisfaction"].value_counts().to_dict().items()
        },
        "top_improvement_areas": {
            str(k): int(v)
            for k, v in df[df["improvement_area"] != "None"]["improvement_area"]
            .value_counts()
            .head(5)
            .to_dict()
            .items()
        },
    }

    summaries = []
    for _, row in df.iterrows():
        summaries.append(
            {
                "customer_id": row["customer_id"],
                "survey_date": row["survey_date"],
                "summary_text": generate_summary(row),
                "ratings": {
                    "overall_satisfaction": int(row["overall_satisfaction"]),
                    "product_rating": int(row["product_rating"]),
                    "service_rating": int(row["service_rating"]),
                },
                "improvement_area": row.get("improvement_area", ""),
                "comments": row.get("comments", ""),
            }
        )

    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, "survey_summaries.json"), "w") as f:
        json.dump(summaries, f, indent=2)
    with open(os.path.join(output_path, "survey_statistics.json"), "w") as f:
        json.dump(summary_stats, f, indent=2)

    print(f"Processed {len(df)} survey rows.")
    print(json.dumps(summary_stats, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=str, default="/opt/ml/processing/input")
    parser.add_argument("--output-path", type=str, default="/opt/ml/processing/output")
    args = parser.parse_args()

    process_survey_data(args.input_path, args.output_path)
