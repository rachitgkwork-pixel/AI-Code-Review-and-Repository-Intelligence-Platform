"""AI code-review service.

Retrieves code chunks for a file (or entire repository) and sends them to an
OpenAI-compatible LLM via LangChain.  Returns structured ReviewIssue objects.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.code_chunk import CodeChunk, RepoFile
from backend.models.review import ReviewHistory
from backend.schemas.review import ReviewIssue, Severity
from backend.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the provided code and return a
JSON array of issues. Each issue must follow this schema:
{
  "issue": "<short title>",
  "severity": "critical|high|medium|low|info",
  "description": "<what is wrong and why>",
  "suggested_fix": "<concrete suggestion>",
  "line_range": "<start-end or null>"
}
Return ONLY the JSON array, no markdown fences."""


class ReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )

    async def review_file(
        self,
        repository_id: uuid.UUID,
        file_path: str,
        user_id: uuid.UUID,
    ) -> ReviewHistory:
        review = ReviewHistory(
            repository_id=repository_id,
            user_id=user_id,
            file_path=file_path,
            review_type="file",
            status="pending",
            llm_model=settings.llm_model,
        )
        self.db.add(review)
        await self.db.flush()

        try:
            code = await self._get_file_content(repository_id, file_path)
            issues = await self._run_review(code, file_path)
            review.results = [i.model_dump() for i in issues]
            review.status = "completed"
        except Exception as exc:
            logger.exception("File review failed")
            review.status = "error"
            review.error_message = str(exc)

        review.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return review

    async def review_repository(
        self,
        repository_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ReviewHistory:
        review = ReviewHistory(
            repository_id=repository_id,
            user_id=user_id,
            review_type="repository",
            status="pending",
            llm_model=settings.llm_model,
        )
        self.db.add(review)
        await self.db.flush()

        try:
            # Sample up to 5 files to keep LLM cost reasonable
            files = await self._get_sample_files(repository_id, limit=5)
            all_issues: list[ReviewIssue] = []
            for fp in files:
                code = await self._get_file_content(repository_id, fp)
                issues = await self._run_review(code, fp)
                all_issues.extend(issues)

            review.results = [i.model_dump() for i in all_issues]
            review.status = "completed"
        except Exception as exc:
            logger.exception("Repository review failed")
            review.status = "error"
            review.error_message = str(exc)

        review.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return review

    async def _get_file_content(self, repository_id: uuid.UUID, file_path: str) -> str:
        result = await self.db.execute(
            select(RepoFile).where(
                RepoFile.repository_id == repository_id,
                RepoFile.file_path == file_path,
            )
        )
        repo_file = result.scalar_one_or_none()
        if not repo_file:
            raise ValueError(f"File not found in index: {file_path}")

        chunks_result = await self.db.execute(
            select(CodeChunk)
            .where(CodeChunk.file_id == repo_file.id)
            .order_by(CodeChunk.chunk_index)
        )
        chunks = chunks_result.scalars().all()
        return "\n".join(c.content for c in chunks)

    async def _get_sample_files(self, repository_id: uuid.UUID, limit: int) -> list[str]:
        result = await self.db.execute(
            select(RepoFile.file_path)
            .where(RepoFile.repository_id == repository_id)
            .limit(limit)
        )
        return [row[0] for row in result.all()]

    async def _run_review(self, code: str, file_path: str) -> list[ReviewIssue]:
        """Send code to the LLM and parse structured issues."""
        if not code.strip():
            return []

        user_prompt = f"File: {file_path}\n\n```\n{code[:8000]}\n```"

        # TODO: add retry logic and token budget guards for large files
        try:
            response = await self._llm.ainvoke(
                [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]
            )
            raw = response.content
        except Exception as exc:
            logger.warning("LLM call failed (%s) — returning placeholder issues", exc)
            return self._placeholder_issues(file_path)

        import json
        try:
            data = json.loads(raw)
            return [ReviewIssue(**item) for item in data]
        except Exception:
            logger.warning("Could not parse LLM response for %s — returning empty", file_path)
            return []

    @staticmethod
    def _placeholder_issues(file_path: str) -> list[ReviewIssue]:
        """Return placeholder issues when the LLM is unavailable."""
        return [
            ReviewIssue(
                issue="Placeholder review",
                severity=Severity.info,
                description=f"LLM unavailable; manual review recommended for {file_path}.",
                suggested_fix="Configure a valid OPENAI_API_KEY and LLM_MODEL.",
            )
        ]
