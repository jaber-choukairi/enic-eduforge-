"""
EduForge — Generation Service
Generates exams and individual questions via RAG:
  1. Retrieve relevant chunks from vector store
  2. Build prompt from template
  3. Call Anthropic API (claude-sonnet-4-20250514) for high-quality generation
  4. Parse and validate structured output
"""
from __future__ import annotations

import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.config import settings, PROMPT_TEMPLATES
from core.utils import get_logger
from services.ingestion.pipeline import IngestionPipeline

logger = get_logger("eduforge.generation")


# ── Groq API Client ──────────────────────────────────────────────────────────

class AnthropicGenerator:
    """
    Uses the Groq API (llama-3.3-70b) for high-quality question generation.
    Groq is free at https://console.groq.com
    Falls back to a simple rule-based generator if the API key is not set.
    """

    _instance: Optional["AnthropicGenerator"] = None

    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        if self.api_key:
            logger.info("GroqGenerator: using llama-3.3-70b-versatile")
        else:
            logger.warning("GroqGenerator: no GROQ_API_KEY — using fallback generator")

    @classmethod
    def get_instance(cls) -> "AnthropicGenerator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate_one(self, prompt: str) -> str:
        if not self.api_key:
            return self._fallback_generate(prompt)
        try:
            import urllib.request
            import json as _json
            payload = _json.dumps({
                "model": "llama-3.3-70b-versatile",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            }).encode()
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = _json.loads(resp.read())
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error("Groq API call failed", extra={"error": str(e)})
            return self._fallback_generate(prompt)

    @staticmethod
    def _fallback_generate(prompt: str) -> str:
        """Minimal rule-based fallback when no API key is available."""
        # Extract a snippet of context from the prompt to make a basic question
        lines = [l.strip() for l in prompt.splitlines() if l.strip()]
        context_lines = [l for l in lines if len(l) > 40]
        snippet = context_lines[0] if context_lines else "the educational material"
        snippet = snippet[:200]

        if "multiple_choice" in prompt:
            return (
                f"Question: Based on the material, which statement about the following is correct: {snippet[:100]}?\n"
                f"A) First option related to the concept\n"
                f"B) Second option with a variation\n"
                f"C) Third option that is incorrect\n"
                f"D) Fourth option that is incorrect\n"
                f"Correct: A\n"
                f"Explanation: This is based on the material provided."
            )
        elif "true_false" in prompt:
            return (
                f"Statement: {snippet[:150]}\n"
                f"Answer: True\n"
                f"Explanation: This statement is supported by the material."
            )
        elif "fill_blank" in prompt:
            words = snippet.split()
            if len(words) > 4:
                blank_idx = len(words) // 2
                answer = words[blank_idx]
                words[blank_idx] = "______"
                return (
                    f"Sentence: {' '.join(words[:blank_idx+1])} {' '.join(words[blank_idx+1:])}\n"
                    f"Answer: {answer}\n"
                    f"Explanation: This term appears in the material."
                )
        elif "essay" in prompt:
            return (
                f"Essay Prompt: Discuss and analyze the following concept from the material: {snippet[:120]}\n"
                f"Guidance: Your answer should cover the main points, provide examples, and demonstrate understanding.\n"
                f"Rubric: Introduction (20%), Analysis (40%), Examples (20%), Conclusion (20%)"
            )
        # short_answer default
        return (
            f"Question: Explain the following concept from the material: {snippet[:120]}\n"
            f"Model Answer: Based on the material, this concept refers to the key ideas presented.\n"
            f"Key Points: Understanding, application, and context."
        )


# ── Question Parser ───────────────────────────────────────────────────────────

class QuestionParser:
    """Parse raw LLM output into structured question dicts."""

    def parse(self, raw: str, question_type: str) -> Dict[str, Any]:
        parsers = {
            "multiple_choice": self._parse_mcq,
            "true_false":      self._parse_true_false,
            "short_answer":    self._parse_short_answer,
            "essay":           self._parse_essay,
            "fill_blank":      self._parse_fill_blank,
        }
        fn = parsers.get(question_type, self._parse_short_answer)
        try:
            return fn(raw)
        except Exception as e:
            logger.warning("Parse failed — falling back to raw", extra={"error": str(e)})
            return self._fallback(raw, question_type)

    def _parse_mcq(self, raw: str) -> Dict[str, Any]:
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
        content = ""
        options: List[str] = []
        correct = ""
        explanation = ""

        for line in lines:
            if line.lower().startswith("question:"):
                content = line.split(":", 1)[1].strip()
            elif re.match(r"^[A-Da-d][)\.][\s]+", line):
                options.append(re.sub(r"^[A-Da-d][)\.][\s]+", "", line).strip())
            elif line.lower().startswith("correct:"):
                correct = line.split(":", 1)[1].strip()
            elif line.lower().startswith("explanation:"):
                explanation = line.split(":", 1)[1].strip()

        if not content:
            content = lines[0] if lines else "Generated question"
        if len(options) < 2:
            options = ["Option A", "Option B", "Option C", "Option D"]
        if not correct:
            correct = "A"

        correct_idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(correct.upper()[0] if correct else "A", 0)
        correct_text = options[correct_idx] if correct_idx < len(options) else correct

        return {"content": content, "options": options, "correct_answer": correct_text, "explanation": explanation}

    def _parse_true_false(self, raw: str) -> Dict[str, Any]:
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
        content = ""
        correct = "True"
        explanation = ""

        for line in lines:
            llow = line.lower()
            if llow.startswith("statement:"):
                content = line.split(":", 1)[1].strip()
            elif llow.startswith("answer:"):
                ans = line.split(":", 1)[1].strip().lower()
                correct = "True" if "true" in ans else "False"
            elif llow.startswith("explanation:"):
                explanation = line.split(":", 1)[1].strip()

        if not content:
            content = lines[0] if lines else "Generated statement"

        return {"content": content, "options": ["True", "False"], "correct_answer": correct, "explanation": explanation}

    def _parse_short_answer(self, raw: str) -> Dict[str, Any]:
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
        content = ""
        answer = ""
        explanation = ""

        for line in lines:
            llow = line.lower()
            if llow.startswith("question:"):
                content = line.split(":", 1)[1].strip()
            elif llow.startswith(("model answer:", "answer:")):
                answer = line.split(":", 1)[1].strip()
            elif llow.startswith(("key points:", "explanation:")):
                explanation = line.split(":", 1)[1].strip()

        if not content:
            content = lines[0] if lines else "Generated question"
        if not answer and len(lines) > 1:
            answer = lines[1]

        return {"content": content, "options": None, "correct_answer": answer, "explanation": explanation}

    def _parse_essay(self, raw: str) -> Dict[str, Any]:
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
        content = ""
        explanation = ""
        rubric = ""

        for line in lines:
            llow = line.lower()
            if llow.startswith("essay prompt:"):
                content = line.split(":", 1)[1].strip()
            elif llow.startswith("guidance:"):
                explanation = line.split(":", 1)[1].strip()
            elif llow.startswith("rubric:"):
                rubric = line.split(":", 1)[1].strip()

        if not content:
            content = lines[0] if lines else "Write an essay about the topic"

        return {"content": content, "options": None, "correct_answer": None, "explanation": explanation, "rubric": rubric}

    def _parse_fill_blank(self, raw: str) -> Dict[str, Any]:
        lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]
        content = ""
        answer = ""
        explanation = ""

        for line in lines:
            llow = line.lower()
            if llow.startswith("sentence:"):
                content = line.split(":", 1)[1].strip()
            elif llow.startswith("answer:"):
                answer = line.split(":", 1)[1].strip()
            elif llow.startswith("explanation:"):
                explanation = line.split(":", 1)[1].strip()

        if not content:
            content = lines[0] if lines else "Fill in the blank: ______"

        return {"content": content, "options": None, "correct_answer": answer, "explanation": explanation}

    def _fallback(self, raw: str, question_type: str) -> Dict[str, Any]:
        first_line = raw.strip().splitlines()[0] if raw.strip() else "Generated question"
        return {
            "content":        first_line[:500],
            "options":        ["A", "B", "C", "D"] if question_type == "multiple_choice" else None,
            "correct_answer": "See explanation",
            "explanation":    raw.strip()[:1000],
        }


# ── Prompt Builder ────────────────────────────────────────────────────────────

class PromptBuilder:
    """Construct generation prompts from retrieved context and templates."""

    def build(self, context_chunks: List[str], question_type: str, topic: str, difficulty: str) -> str:
        # Use generous context window — Anthropic handles long prompts well
        context = "\n\n".join(context_chunks)
        context = context[:6000]  # ~1500 tokens of context

        template = PROMPT_TEMPLATES.get(question_type, PROMPT_TEMPLATES["short_answer"])
        return template.format(
            context=context,
            topic=topic or "the material",
            difficulty=difficulty,
        )


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class GeneratedQuestion:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question_type: str = "short_answer"
    difficulty: str = "medium"
    content: str = ""
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    rubric: Optional[str] = None
    points: float = 1.0
    order_index: int = 0
    raw_generation: str = ""
    source_context: str = ""


# ── Exam Generator ────────────────────────────────────────────────────────────

class ExamGenerator:
    """Orchestrates retrieval-augmented question generation."""

    def __init__(
        self,
        ingestion_pipeline: Optional[IngestionPipeline] = None,
        generator: Optional[AnthropicGenerator] = None,
        parser: Optional[QuestionParser] = None,
        prompt_builder: Optional[PromptBuilder] = None,
    ):
        self.pipeline = ingestion_pipeline or IngestionPipeline()
        self.model    = generator          or AnthropicGenerator.get_instance()
        self.parser   = parser             or QuestionParser()
        self.builder  = prompt_builder     or PromptBuilder()

    def generate_exam(
        self,
        material_ids: List[str],
        question_configs: List[Dict[str, Any]],
        topic: Optional[str] = None,
        global_difficulty: str = "medium",
    ) -> List[GeneratedQuestion]:
        all_questions: List[GeneratedQuestion] = []
        order = 0

        for cfg in question_configs:
            q_type = cfg.get("question_type", "multiple_choice")
            count  = cfg.get("count", 5)
            diff   = cfg.get("difficulty", global_difficulty)

            logger.info("Generating questions", extra={"type": q_type, "count": count, "difficulty": diff})

            questions = self.generate_questions(
                material_ids=material_ids,
                question_type=q_type,
                count=count,
                difficulty=diff,
                topic=topic,
            )
            for q in questions:
                q.order_index = order
                order += 1
            all_questions.extend(questions)

        logger.info("Exam generation complete", extra={"total_questions": len(all_questions)})
        return all_questions

    def generate_questions(
        self,
        material_ids: List[str],
        question_type: str,
        count: int,
        difficulty: str = "medium",
        topic: Optional[str] = None,
    ) -> List[GeneratedQuestion]:
        questions: List[GeneratedQuestion] = []

        for i in range(count):
            try:
                q = self._generate_single(
                    material_ids=material_ids,
                    question_type=question_type,
                    difficulty=difficulty,
                    topic=topic or "the educational material",
                    attempt=i,
                )
                questions.append(q)
            except Exception as e:
                logger.error("Question generation failed", extra={"index": i+1, "error": str(e)})
                questions.append(self._placeholder(question_type, difficulty, i))

        return questions

    def _generate_single(
        self,
        material_ids: List[str],
        question_type: str,
        difficulty: str,
        topic: str,
        attempt: int = 0,
    ) -> GeneratedQuestion:
        search_q = f"{topic} {difficulty} {question_type} {attempt}"
        chunks = self.pipeline.retrieve_context(
            query=search_q,
            n_results=5,
            material_ids=material_ids,
        )

        if not chunks:
            raise ValueError("No context retrieved from vector store")

        prompt = self.builder.build(
            context_chunks=chunks,
            question_type=question_type,
            topic=topic,
            difficulty=difficulty,
        )

        raw = self.model.generate_one(prompt)
        parsed = self.parser.parse(raw, question_type)
        points = {"easy": 1.0, "medium": 2.0, "hard": 3.0}.get(difficulty, 1.0)

        return GeneratedQuestion(
            question_type=question_type,
            difficulty=difficulty,
            content=parsed.get("content", ""),
            options=parsed.get("options"),
            correct_answer=parsed.get("correct_answer"),
            explanation=parsed.get("explanation"),
            rubric=parsed.get("rubric"),
            points=points,
            raw_generation=raw,
            source_context=chunks[0][:500] if chunks else "",
        )

    @staticmethod
    def _placeholder(q_type: str, difficulty: str, index: int) -> GeneratedQuestion:
        return GeneratedQuestion(
            question_type=q_type,
            difficulty=difficulty,
            content=f"[Question {index+1} — generation failed, please review]",
            options=["A", "B", "C", "D"] if q_type == "multiple_choice" else None,
            correct_answer="Review required",
            explanation="Could not generate this question automatically.",
            points=1.0,
        )


# ── Exam Exporter ─────────────────────────────────────────────────────────────

class ExamExporter:
    """Format generated exams for export."""

    def to_markdown(self, title: str, questions: List[GeneratedQuestion]) -> str:
        lines = [f"# {title}\n", f"**Total questions:** {len(questions)}\n\n---\n"]
        for i, q in enumerate(questions, 1):
            lines.append(f"## Question {i} ({q.question_type.replace('_', ' ').title()} — {q.difficulty.title()})\n")
            lines.append(f"{q.content}\n")
            if q.options:
                for j, opt in enumerate(q.options):
                    letter = chr(65 + j)
                    lines.append(f"- **{letter})** {opt}")
                lines.append("")
            if q.correct_answer:
                lines.append(f"\n**Answer:** {q.correct_answer}")
            if q.explanation:
                lines.append(f"\n**Explanation:** {q.explanation}")
            if q.rubric:
                lines.append(f"\n**Rubric:** {q.rubric}")
            lines.append(f"\n*Points: {q.points}*\n\n---\n")
        return "\n".join(lines)

    def to_student_view(self, title: str, questions: List[GeneratedQuestion]) -> str:
        lines = [f"# {title}\n", f"**Total questions:** {len(questions)}\n\n---\n"]
        for i, q in enumerate(questions, 1):
            lines.append(f"## Question {i}\n")
            lines.append(f"{q.content}\n")
            if q.options:
                for j, opt in enumerate(q.options):
                    letter = chr(65 + j)
                    lines.append(f"- **{letter})** {opt}")
                lines.append("")
            lines.append(f"\n*Points: {q.points}*\n\n---\n")
        return "\n".join(lines)

    def to_json(self, title: str, questions: List[GeneratedQuestion]) -> List[Dict[str, Any]]:
        return [
            {
                "index": i + 1,
                "type": q.question_type,
                "difficulty": q.difficulty,
                "content": q.content,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "rubric": q.rubric,
                "points": q.points,
            }
            for i, q in enumerate(questions)
        ]