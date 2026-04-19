"""
EduForge — Training Service
Fine-tunes a T5 (or similar seq2seq) model on extracted Q&A pairs.
Tracks experiments with MLflow and registers the best model.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mlflow
import mlflow.pytorch
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    T5ForConditionalGeneration,
    T5Tokenizer,
    EarlyStoppingCallback,
)

from core.config import settings, PROMPT_TEMPLATES
from core.utils import get_logger

logger = get_logger("eduforge.training")


# ── Dataset ───────────────────────────────────────────────────────────────────

@dataclass
class QARecord:
    input_text: str
    target_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class EduDataset(Dataset):
    """Tokenised dataset of (input → output) pairs for seq2seq training."""

    def __init__(
        self,
        records: List[QARecord],
        tokenizer: AutoTokenizer,
        max_input_len: int = settings.MAX_INPUT_TOKENS,
        max_output_len: int = settings.MAX_OUTPUT_TOKENS,
    ):
        self.records = records
        self.tokenizer = tokenizer
        self.max_input_len = max_input_len
        self.max_output_len = max_output_len

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        rec = self.records[idx]
        model_inputs = self.tokenizer(
            rec.input_text,
            max_length=self.max_input_len,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        labels = self.tokenizer(
            rec.target_text,
            max_length=self.max_output_len,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        label_ids = labels["input_ids"].squeeze()
        # Mask padding tokens in labels
        label_ids[label_ids == self.tokenizer.pad_token_id] = -100

        return {
            "input_ids":      model_inputs["input_ids"].squeeze(),
            "attention_mask": model_inputs["attention_mask"].squeeze(),
            "labels":         label_ids,
        }


# ── Data Builder ─────────────────────────────────────────────────────────────

class TrainingDataBuilder:
    """
    Transforms raw chunk texts into (input, target) pairs suitable for
    fine-tuning a question-generation model.
    Format used: "generate question: {context}" → "{question}"
    and           "generate answer: {context} question: {question}" → "{answer}"
    """

    def build_from_chunks(
        self,
        chunks: List[Dict[str, Any]],
        question_type: str = "short_answer",
    ) -> List[QARecord]:
        records: List[QARecord] = []
        template = PROMPT_TEMPLATES.get(question_type, PROMPT_TEMPLATES["short_answer"])

        for chunk in chunks:
            content = chunk.get("content", "").strip()
            if len(content) < 50:  # Skip very short chunks
                continue

            # Question generation training record
            input_text = f"generate question from context: {content[:400]}"
            target_text = f"What is the main concept discussed in the following passage: {content[:100]}?"
            records.append(QARecord(
                input_text=input_text,
                target_text=target_text,
                metadata={"type": "question_gen", "chunk_id": chunk.get("chunk_index", 0)},
            ))

            # Context summarisation record
            input_text2 = f"summarize educational content: {content[:400]}"
            sentences = content.split(".")
            target_text2 = sentences[0].strip() + "." if sentences else content[:100]
            records.append(QARecord(
                input_text=input_text2,
                target_text=target_text2,
                metadata={"type": "summarise", "chunk_id": chunk.get("chunk_index", 0)},
            ))

        logger.info("Built training records", extra={"count": len(records)})
        return records

    def train_val_split(
        self,
        records: List[QARecord],
        val_ratio: float = 0.1,
    ) -> Tuple[List[QARecord], List[QARecord]]:
        import random
        shuffled = records.copy()
        random.shuffle(shuffled)
        split = max(1, int(len(shuffled) * (1 - val_ratio)))
        return shuffled[:split], shuffled[split:]


# ── Trainer ───────────────────────────────────────────────────────────────────

class EduModelTrainer:
    """
    Wraps HuggingFace Seq2SeqTrainer with MLflow integration.
    Works on CPU — batch sizes are kept small to avoid OOM.
    """

    def __init__(
        self,
        base_model: str = settings.GENERATION_MODEL,
        model_save_dir: Optional[Path] = None,
    ):
        self.base_model = base_model
        self.model_save_dir = model_save_dir or (settings.MODEL_CACHE_DIR / "fine_tuned")
        self.model_save_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Loading base model", extra={"model": base_model})
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model, cache_dir=str(settings.MODEL_CACHE_DIR)
        )
        self.model: Optional[AutoModelForSeq2SeqLM] = None

    def _load_model(self) -> AutoModelForSeq2SeqLM:
        logger.info("Loading model weights", extra={"model": self.base_model})
        model = AutoModelForSeq2SeqLM.from_pretrained(
            self.base_model, cache_dir=str(settings.MODEL_CACHE_DIR)
        )
        model.to("cpu")
        return model

    def train(
        self,
        records: List[QARecord],
        job_id: str,
        hyperparams: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Full fine-tune loop. Returns metrics dict.
        All MLflow logging is done here.
        """
        hp = {
            "num_train_epochs": settings.NUM_TRAIN_EPOCHS,
            "per_device_train_batch_size": settings.TRAIN_BATCH_SIZE,
            "per_device_eval_batch_size": settings.EVAL_BATCH_SIZE,
            "learning_rate": settings.LEARNING_RATE,
            "warmup_steps": settings.WARMUP_STEPS,
            "gradient_accumulation_steps": settings.GRADIENT_ACCUMULATION_STEPS,
            **(hyperparams or {}),
        }

        data_builder = TrainingDataBuilder()
        train_records, val_records = data_builder.train_val_split(records)

        if len(train_records) < 2:
            raise ValueError("Not enough training data — need at least 2 records")

        train_ds = EduDataset(train_records, self.tokenizer)
        val_ds   = EduDataset(val_records,   self.tokenizer)

        output_dir = self.model_save_dir / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        training_args = Seq2SeqTrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=hp["num_train_epochs"],
            per_device_train_batch_size=hp["per_device_train_batch_size"],
            per_device_eval_batch_size=hp["per_device_eval_batch_size"],
            learning_rate=hp["learning_rate"],
            warmup_steps=hp["warmup_steps"],
            gradient_accumulation_steps=hp["gradient_accumulation_steps"],
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            predict_with_generate=True,
            fp16=False,  # CPU — no FP16
            no_cuda=True,
            report_to=["none"],  # We handle MLflow manually
            logging_steps=10,
            save_total_limit=2,
            dataloader_num_workers=0,  # Windows compatibility
        )

        # ── MLflow run ────────────────────────────────────────────────────────
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)

        with mlflow.start_run(run_name=f"train-{job_id[:8]}") as run:
            mlflow.log_params({**hp, "base_model": self.base_model, "job_id": job_id})
            mlflow.log_param("train_samples", len(train_records))
            mlflow.log_param("val_samples", len(val_records))

            self.model = self._load_model()

            collator = DataCollatorForSeq2Seq(
                self.tokenizer, model=self.model, pad_to_multiple_of=8
            )

            trainer = Seq2SeqTrainer(
                model=self.model,
                args=training_args,
                train_dataset=train_ds,
                eval_dataset=val_ds,
                tokenizer=self.tokenizer,
                data_collator=collator,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
            )

            logger.info("Training started", extra={"job_id": job_id, "epochs": hp["num_train_epochs"]})
            t0 = time.time()
            train_result = trainer.train()
            elapsed = round(time.time() - t0, 2)

            eval_result = trainer.evaluate()

            # Log metrics
            metrics = {
                "train_loss":    round(train_result.training_loss, 4),
                "eval_loss":     round(eval_result.get("eval_loss", 0), 4),
                "train_runtime": round(elapsed, 2),
                "train_samples": len(train_records),
                "val_samples":   len(val_records),
            }
            mlflow.log_metrics(metrics)

            # Save model
            trainer.save_model(str(output_dir / "best"))
            self.tokenizer.save_pretrained(str(output_dir / "best"))

            # Log model artifact
            mlflow.pytorch.log_model(self.model, "model")

            run_id = run.info.run_id
            run_url = f"{settings.MLFLOW_TRACKING_URI}/#/experiments/{run.info.experiment_id}/runs/{run_id}"

            logger.info(
                "Training complete",
                extra={"job_id": job_id, "metrics": metrics, "run_id": run_id},
            )

            return {
                "metrics":        metrics,
                "mlflow_run_id":  run_id,
                "mlflow_run_url": run_url,
                "model_path":     str(output_dir / "best"),
            }

    def register_model(self, run_id: str, model_name: str) -> str:
        """Register the trained model in MLflow Model Registry."""
        client = mlflow.tracking.MlflowClient(tracking_uri=settings.MLFLOW_TRACKING_URI)
        result = mlflow.register_model(
            model_uri=f"runs:/{run_id}/model",
            name=model_name,
        )
        client.transition_model_version_stage(
            name=model_name,
            version=result.version,
            stage="Staging",
        )
        logger.info(
            "Model registered",
            extra={"name": model_name, "version": result.version},
        )
        return result.version


# ── Inference Wrapper ─────────────────────────────────────────────────────────

class GenerativeModel:
    """
    Loads a fine-tuned (or base) model for exam generation inference.
    Singleton to avoid reloading on every request.
    """

    _instance: Optional["GenerativeModel"] = None

    def __init__(self, model_path: Optional[str] = None):
        path = model_path or settings.GENERATION_MODEL
        logger.info("Loading generative model", extra={"path": path})
        t0 = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(
            path, cache_dir=str(settings.MODEL_CACHE_DIR)
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            path, cache_dir=str(settings.MODEL_CACHE_DIR)
        )
        self.model.eval()
        self.model.to("cpu")
        logger.info(
            "Generative model loaded",
            extra={"path": path, "elapsed_s": round(time.time() - t0, 2)},
        )

    @classmethod
    def get_instance(cls, model_path: Optional[str] = None) -> "GenerativeModel":
        if cls._instance is None:
            cls._instance = cls(model_path)
        return cls._instance

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = settings.MAX_OUTPUT_TOKENS,
        temperature: float = settings.GENERATION_TEMPERATURE,
        top_p: float = settings.GENERATION_TOP_P,
        num_return_sequences: int = 1,
    ) -> List[str]:
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=settings.MAX_INPUT_TOKENS,
            truncation=True,
        )
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=temperature if temperature > 0 else 1.0,
            top_p=top_p,
            num_return_sequences=num_return_sequences,
            early_stopping=True,
        )
        decoded = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return [d.strip() for d in decoded]

    def generate_one(self, prompt: str, **kwargs) -> str:
        results = self.generate(prompt, num_return_sequences=1, **kwargs)
        return results[0] if results else ""
