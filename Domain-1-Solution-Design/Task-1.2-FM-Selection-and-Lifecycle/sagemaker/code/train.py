"""
Task 1.2 - Part 4, Step 13: fine-tune a small open model (distilgpt2) on the
financial Q&A dataset from Step 12, via a SageMaker training job (script mode).

Runs on a plain PyTorch CPU training container - distilgpt2 is small enough
(~82M params) to fine-tune on CPU in a few minutes on 35 examples, which
keeps this PoC's training cost to a few cents instead of renting a GPU.
"""
import argparse
import json
import os

from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", type=str, default="distilgpt2")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR"))
    parser.add_argument("--training-dir", type=str, default=os.environ.get("SM_CHANNEL_TRAINING"))
    return parser.parse_args()


def load_examples(training_dir):
    path = os.path.join(training_dir, "financial_qa_dataset.jsonl")
    examples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            # Same structured instruction format as the brief's own example
            # train.py, so the model learns a consistent Q/A shape.
            text = f"Question: {row['prompt']}\nAnswer: {row['completion']}"
            examples.append({"text": text})
    return examples


def main():
    args = parse_args()

    examples = load_examples(args.training_dir)
    print(f"Loaded {len(examples)} training examples from {args.training_dir}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    tokenizer.pad_token = tokenizer.eos_token  # GPT-2 has no pad token by default

    dataset = Dataset.from_list(examples)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=256, padding="max_length")

    tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])

    model = AutoModelForCausalLM.from_pretrained(args.model_name)

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir="/tmp/checkpoints",
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        logging_steps=5,
        save_strategy="no",
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=collator,
    )

    trainer.train()

    trainer.save_model(args.model_dir)
    tokenizer.save_pretrained(args.model_dir)
    print(f"Saved fine-tuned model to {args.model_dir}")


if __name__ == "__main__":
    main()
