"""
stages/research.py — Topic research stage.

Collects a small bundle of live search evidence, then uses Claude Code CLI
to synthesize:
  - research/<slug>.md
  - research/<slug>-outline.md
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from config import PipelineConfig
from stages.claude_client import run_claude_json
from stages.topic_utils import (
    TopicInput,
    topic_context_json,
    topic_signature,
    topic_slug,
    topic_title,
)


class ResearchStage:
    def __init__(self, cfg: PipelineConfig, log: logging.Logger):
        self.cfg = cfg
        self.log = log.getChild("research")

    def run(self, topic: TopicInput) -> tuple[Path, Path]:
        slug = topic_slug(topic)
        signature = topic_signature(topic)
        title = topic_title(topic)
        research_dir = self.cfg.research_dir
        research_dir.mkdir(parents=True, exist_ok=True)

        research_path = research_dir / f"{slug}.md"
        outline_path = research_dir / f"{slug}-outline.md"
        meta_path = research_dir / f"{slug}.meta.json"

        if research_path.exists() and outline_path.exists() and meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except json.JSONDecodeError:
                meta = {}
            if isinstance(meta, dict) and meta.get("topic_signature") == signature:
                self.log.info(f"  Reusing existing research docs for '{title}'")
                return research_path, outline_path

        queries = self._build_queries(topic)
        evidence = self._collect_evidence(title, queries)
        self.log.info(f"  Collected {len(evidence)} evidence snippets from {len(queries)} queries")

        research_markdown = ""
        outline_markdown = ""

        try:
            prompt = self._build_prompt(topic, slug, queries, evidence)
            schema = {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "research_brief": {"type": "string"},
                    "research_markdown": {"type": "string"},
                    "outline_markdown": {"type": "string"},
                },
                "required": [
                    "title",
                    "research_brief",
                    "research_markdown",
                    "outline_markdown",
                ],
                "additionalProperties": False,
            }
            result = run_claude_json(
                prompt=prompt,
                model=self.cfg.llm_model_name(),
                system_prompt=self._system_prompt(),
                schema=schema,
                provider=self.cfg.llm_provider,
                base_url=self.cfg.lmstudio_base_url,
                api_key=self.cfg.lmstudio_api_key,
                timeout=180,
            )

            research_markdown = self._normalize_markdown(
                result.get("research_markdown")
                or result.get("research_brief")
                or ""
            )
            outline_markdown = self._normalize_markdown(
                result.get("outline_markdown")
                or result.get("research_markdown")
                or result.get("research_brief")
                or ""
            )
        except Exception as exc:
            self.log.warning(f"  Research LLM failed ({exc}); using structured fallback")

        if not research_markdown.strip():
            research_markdown = self._fallback_research_markdown(topic, title, queries, evidence)
        if not outline_markdown.strip():
            outline_markdown = self._fallback_outline_markdown(topic, title, queries, evidence)

        research_path.write_text(research_markdown.rstrip() + "\n")
        outline_path.write_text(outline_markdown.rstrip() + "\n")
        meta_path.write_text(
            json.dumps(
                {
                    "topic_signature": signature,
                    "topic_title": title,
                    "topic_slug": slug,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )

        self.log.info(f"  Research saved -> {research_path}")
        self.log.info(f"  Outline saved  -> {outline_path}")
        return research_path, outline_path

    def _system_prompt(self) -> str:
        return (
            "You are a senior research analyst and instructional designer for an educational video pipeline. "
            "Your job is to convert search evidence into a concise but high-signal research brief and an act-based outline. "
            "Use only the supplied evidence for factual claims. If a detail is not supported, label it clearly as an inference or omit it. "
            "Prefer specific names, numbers, examples, and causal relationships over generalities. "
            "Write for a future script writer who needs topic accuracy, teaching sequence, and visual hooks. "
            "Return only the JSON object required by the schema and make sure it contains no extra commentary."
        )

    def _build_queries(self, topic: TopicInput) -> list[str]:
        if isinstance(topic, dict):
            title = topic_title(topic)
            queries = [
                *(query.strip() for query in topic.get("search_queries", []) if isinstance(query, str)),
                f"{title} definition and intuition",
                f"{title} worked example",
                f"{title} visual intuition",
                f"{title} common misconceptions",
                f"{title} real world application",
            ]
            for angle in topic.get("research_angles", []):
                if isinstance(angle, str) and angle.strip():
                    queries.append(f"{title} {angle}")
            for term in topic.get("key_terms", [])[:4]:
                if isinstance(term, str) and term.strip():
                    queries.append(f"{title} {term}")
            return self._dedupe_queries(queries)

        topic_clean = topic.strip()
        lower = topic_clean.lower()

        if any(word in lower for word in ["option", "trading", "finance", "market", "stock"]):
            return [
                f"{topic_clean} definition and core formula",
                f"{topic_clean} worked example with numbers",
                f"{topic_clean} historical context",
                f"{topic_clean} visual intuition",
                f"{topic_clean} common misconceptions",
                f"{topic_clean} real world example",
            ]

        if any(word in lower for word in ["physics", "chemistry", "biology", "math", "probability", "statistics", "algorithm", "machine learning"]):
            return [
                f"{topic_clean} definition and mechanism",
                f"{topic_clean} worked example or experiment",
                f"{topic_clean} historical context",
                f"{topic_clean} visual intuition",
                f"{topic_clean} common misconceptions",
                f"{topic_clean} real world application",
            ]

        if any(word in lower for word in ["history", "war", "novel", "movie", "story", "biography", "detective"]):
            return [
                f"{topic_clean} historical context",
                f"{topic_clean} key events and timeline",
                f"{topic_clean} important characters or figures",
                f"{topic_clean} visual references",
                f"{topic_clean} common misconceptions",
                f"{topic_clean} real world significance",
            ]

        return [
            f"{topic_clean} definition and overview",
            f"{topic_clean} key concepts",
            f"{topic_clean} real world example",
            f"{topic_clean} historical context",
            f"{topic_clean} visual intuition",
            f"{topic_clean} common misconceptions",
        ]

    def _dedupe_queries(self, queries: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for query in queries:
            normalized = " ".join(query.split()).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped[:10]

    def _collect_evidence(self, topic: str, queries: list[str]) -> list[dict[str, str]]:
        evidence: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        if self.cfg.brave_api_key:
            for query in queries:
                snippets = self._brave_search(query)
                for item in snippets:
                    url = item.get("url", "").strip()
                    if url and url in seen_urls:
                        continue
                    if url:
                        seen_urls.add(url)
                    item["query"] = query
                    evidence.append(item)
        else:
            for query in queries:
                snippets = self._duckduckgo_instant_answer(query)
                for item in snippets:
                    url = item.get("url", "").strip()
                    if url and url in seen_urls:
                        continue
                    if url:
                        seen_urls.add(url)
                    item["query"] = query
                    evidence.append(item)

        wiki = self._wikipedia_summary(topic)
        if wiki:
            url = wiki.get("url", "")
            if not url or url not in seen_urls:
                if url:
                    seen_urls.add(url)
                evidence.append({"query": topic, **wiki})

        return evidence[:24]

    def _brave_search(self, query: str, count: int = 5) -> list[dict[str, str]]:
        url = (
            "https://api.search.brave.com/res/v1/web/search"
            f"?q={urllib.parse.quote_plus(query)}&count={count}&text_decorations=0&search_lang=en"
        )
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.cfg.brave_api_key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read()
                # Brave may return gzip-encoded data
                import gzip as _gzip
                try:
                    raw = _gzip.decompress(raw)
                except Exception:
                    pass
                data = json.loads(raw.decode("utf-8"))
        except Exception as e:
            self.log.warning(f"  Brave search failed for '{query}': {e}")
            return []

        results: list[dict[str, str]] = []
        for item in (data.get("web") or {}).get("results") or []:
            title = (item.get("title") or "").strip()
            page_url = (item.get("url") or "").strip()
            description = (item.get("description") or "").strip()
            extra = " ".join(item.get("extra_snippets") or []).strip()
            snippet = f"{description} {extra}".strip() if extra else description
            if snippet:
                results.append({
                    "source": "brave",
                    "title": title,
                    "url": page_url,
                    "snippet": snippet,
                })
        return results

    def _duckduckgo_instant_answer(self, query: str) -> list[dict[str, str]]:
        url = (
            "https://api.duckduckgo.com/"
            f"?q={urllib.parse.quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        )
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            self.log.warning(f"  DDG lookup failed for '{query}': {e}")
            return []

        results: list[dict[str, str]] = []
        abstract = (data.get("AbstractText") or "").strip()
        abstract_url = (data.get("AbstractURL") or "").strip()
        heading = (data.get("Heading") or query).strip()
        if abstract:
            results.append(
                {
                    "source": "duckduckgo",
                    "title": heading,
                    "url": abstract_url,
                    "snippet": abstract,
                }
            )

        def walk_related(items: Any):
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                if "Topics" in item:
                    yield from walk_related(item.get("Topics"))
                    continue
                text = (item.get("Text") or "").strip()
                first_url = (item.get("FirstURL") or "").strip()
                if text:
                    yield {
                        "source": "duckduckgo",
                        "title": text.split(" - ", 1)[0],
                        "url": first_url,
                        "snippet": text,
                    }

        results.extend(list(walk_related(data.get("RelatedTopics"))))
        return results

    def _wikipedia_summary(self, topic: str) -> dict[str, str]:
        title = urllib.parse.quote(topic.strip().replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            return {}

        extract = (data.get("extract") or "").strip()
        page_url = ""
        content_urls = data.get("content_urls") or {}
        if isinstance(content_urls, dict):
            desktop = content_urls.get("desktop") or {}
            if isinstance(desktop, dict):
                page_url = (desktop.get("page") or "").strip()

        if not extract:
            return {}

        return {
            "source": "wikipedia",
            "title": (data.get("title") or topic).strip(),
            "url": page_url,
            "snippet": extract,
        }

    def _build_prompt(
        self,
        topic: TopicInput,
        slug: str,
        queries: list[str],
        evidence: list[dict[str, str]],
    ) -> str:
        topic_block = topic_context_json(topic)
        topic_name = topic_title(topic)
        queries_block = "\n".join(f"- {q}" for q in queries)

        if evidence:
            evidence_block = json.dumps(evidence, indent=2, ensure_ascii=False)
            evidence_section = f"Search evidence:\n{evidence_block}"
        else:
            evidence_section = (
                "Search evidence: none available. "
                "Synthesize from the topic document and your knowledge of the subject."
            )

        return f"""
Topic title: {topic_name}
Slug: {slug}
Topic document:
{topic_block}

You are preparing research for a topic-driven educational video pipeline.
Produce three fields:
1. `research_markdown`: 400-600 words, markdown, with a clear teaching arc.
2. `outline_markdown`: markdown outline with Act 1, Act 2, Act 3, Act 4 sections.
3. `research_brief`: one concise paragraph summarising the topic and the teaching goal.

Research constraints:
- Use the topic document fields (learning_goals, key_terms, visual_hooks, misconceptions, teaching_notes) as the primary source.
- Include at least one concrete worked example with specific numbers or values.
- Add a short "common misconceptions" section drawn from the topic document.
- Explain what the video should teach in each act.
- Keep the outline suitable for later script generation.
- Prioritize useful teaching structure over prose polish.
- Keep the output compact, precise, and easy for a script writer to reuse.

Target search queries:
{queries_block}

{evidence_section}
""".strip()

    def _fallback_research_markdown(
        self,
        topic: TopicInput,
        title: str,
        queries: list[str],
        evidence: list[dict[str, str]],
    ) -> str:
        lines = [
            f"# {title}",
            "",
            "## Research Summary",
        ]
        if isinstance(topic, dict):
            brief = str(topic.get("brief") or topic.get("prompt_summary") or "").strip()
            description = str(topic.get("description") or "").strip()
            if brief:
                lines.append(brief)
            if description:
                lines.extend(["", description])
            goals = self._topic_list(topic.get("learning_goals"))
            if goals:
                lines.extend(["", "## Learning Goals", *[f"- {item}" for item in goals]])
            notes = topic.get("teaching_notes")
            if isinstance(notes, dict):
                opener = str(notes.get("opener") or "").strip()
                explanation = str(notes.get("explanation") or "").strip()
                practice = str(notes.get("practice") or "").strip()
                close = str(notes.get("close") or "").strip()
                teaching_bits = [bit for bit in [opener, explanation, practice, close] if bit]
                if teaching_bits:
                    lines.extend(["", "## Teaching Notes", *[f"- {bit}" for bit in teaching_bits]])
            key_terms = self._topic_list(topic.get("key_terms"))
            if key_terms:
                lines.extend(["", "## Key Terms", *[f"- {item}" for item in key_terms]])
            visual_hooks = self._topic_list(topic.get("visual_hooks"))
            if visual_hooks:
                lines.extend(["", "## Visual Hooks", *[f"- {item}" for item in visual_hooks]])
            misconceptions = self._topic_list(topic.get("misconceptions"))
            if misconceptions:
                lines.extend(["", "## Common Misconceptions", *[f"- {item}" for item in misconceptions]])
            research_angles = self._topic_list(topic.get("research_angles"))
            if research_angles:
                lines.extend(["", "## Research Angles", *[f"- {item}" for item in research_angles]])
        else:
            lines.append(
                "No live evidence was collected for this seed, so this draft preserves the broad lesson context for downstream script generation."
            )
            lines.append("")
            lines.append("## Research Notes")
            lines.append("- No evidence snippets were returned.")

        if queries:
            lines.extend([
                "",
                "## Search Queries",
                *[f"- {query}" for query in queries[:6]],
            ])
        if evidence:
            lines.extend([
                "",
                "## Evidence Notes",
                *[f"- {item.get('title', 'source')}: {item.get('snippet', '')}" for item in evidence[:6]],
            ])
        elif not isinstance(topic, dict):
            lines.append("- No evidence snippets were returned.")
        return "\n".join(lines)

    def _fallback_outline_markdown(
        self,
        topic: TopicInput,
        title: str,
        queries: list[str],
        evidence: list[dict[str, str]],
    ) -> str:
        lines = [
            f"# {title}",
            "",
            "## Act 1",
            f"- Introduce {title} at a high level.",
            "",
            "## Act 2",
            "- Expand the core mechanics, vocabulary, and visual intuition.",
            "",
            "## Act 3",
            "- Show a worked example or concrete use case grounded in the topic document.",
            "",
            "## Act 4",
            "- Connect the lesson back to practice, common misconceptions, and next steps.",
        ]
        if isinstance(topic, dict):
            goals = self._topic_list(topic.get("learning_goals"))
            if goals:
                lines.extend(["", "## Learning Goals", *[f"- {item}" for item in goals]])
            teaching_notes = topic.get("teaching_notes")
            if isinstance(teaching_notes, dict):
                notes_lines = []
                for key in ("opener", "explanation", "practice", "close"):
                    value = str(teaching_notes.get(key) or "").strip()
                    if value:
                        notes_lines.append(f"- {value}")
                if notes_lines:
                    lines.extend(["", "## Teaching Notes", *notes_lines])
        if queries:
            lines.extend([
                "",
                "## Search Queries",
                *[f"- {query}" for query in queries[:6]],
            ])
        if evidence:
            lines.extend([
                "",
                "## Evidence",
                *[f"- {item.get('title', 'source')}: {item.get('snippet', '')}" for item in evidence[:6]],
            ])
        return "\n".join(lines)

    @staticmethod
    def _topic_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _normalize_markdown(text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        return stripped
