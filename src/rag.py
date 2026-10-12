import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

INDEXED_DOCS = [
    "ARCHITECTURE.md",
    "K8S_GUIDE.md",
    "LLD.md",
    "README.md",
    "RESUME_IMPACT.md",
]

INDEXED_CODE_FILES = [
    "src/models/registry.py",
    "src/models/baselines.py",
    "src/models/lightgbm_model.py",
    "src/drift/detector.py",
    "src/drift/simulator.py",
    "src/serving/app.py",
    "src/serving/middleware.py",
    "src/metrics/evaluator.py",
    "src/llm_gateway.py",
    "src/features/builder.py",
]

STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with", "is", "are",
    "was", "were", "of", "by", "from", "it", "this", "that", "how", "what", "why", "can",
    "you", "i", "we", "our", "do", "does", "explain", "about", "me", "show", "tell",
    "give", "please", "using", "used", "will", "would", "could", "should", "all"
}

def tokenize(text: str) -> List[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", " ", text.lower())
    return [w for w in cleaned.split() if len(w) > 1 and w not in STOPWORDS]

class Chunk:
    def __init__(
        self,
        file_path: str,
        section_name: str,
        content: str,
        chunk_type: str = "doc",  # "doc" or "code"
        language: str = "markdown",
    ):
        self.file_path = file_path
        self.section_name = section_name
        self.content = content.strip()
        self.chunk_type = chunk_type
        self.language = language
        self.tokens: Set[str] = set(tokenize(f"{section_name} {self.content}"))
        self.char_count = len(self.content)
        self.token_estimate = max(1, self.char_count // 4)

class ContextWindowManager:
    """
    Manages conversational context budget, token counting, and query reformulation.
    """

    def __init__(self, max_context_chars: int = 7000, max_history_turns: int = 4):
        self.max_context_chars = max_context_chars
        self.max_history_turns = max_history_turns

    def reformulate_conversational_query(
        self, prompt: str, history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Resolves coreferences (e.g. 'it', 'that', 'its code', 'explain it')
        using the previous 1-2 conversation turns.
        """
        query_text = (prompt or "").strip()
        if not history:
            return query_text

        # Check if query is short or coreference heavy
        coreference_words = {"it", "this", "that", "its", "them", "code", "architecture", "rollback", "drift", "why", "how"}
        tokens = set(tokenize(query_text))

        needs_context = len(tokens) <= 3 or bool(tokens & coreference_words) or ("code" in query_text.lower())

        if needs_context:
            context_keywords = []
            for msg in reversed(history[-self.max_history_turns:]):
                txt = msg.get("text") or msg.get("content") or ""
                # extract substantive terms from prior assistant/user turn
                prior_tokens = [t for t in tokenize(txt) if len(t) > 3][:6]
                context_keywords.extend(prior_tokens)
                if len(context_keywords) >= 8:
                    break

            if context_keywords:
                unique_keywords = list(dict.fromkeys(context_keywords[:5]))
                return f"{query_text} {' '.join(unique_keywords)}"

        return query_text

    def format_history_within_budget(
        self, history: Optional[List[Dict[str, Any]]], max_chars: int = 2500
    ) -> List[Dict[str, str]]:
        """
        Selects recent history turns without blowing up the context window budget.
        """
        if not history:
            return []

        formatted: List[Dict[str, str]] = []
        total_chars = 0

        for msg in reversed(history):
            role = "user" if msg.get("sender") == "user" or msg.get("role") == "user" else "assistant"
            content = msg.get("text") or msg.get("content") or ""
            # Clean up excessively long prior assistant outputs
            if len(content) > 800:
                content = content[:800] + "... [prior response truncated for context window]"

            msg_len = len(content)
            if total_chars + msg_len > max_chars:
                break

            formatted.insert(0, {"role": role, "content": content})
            total_chars += msg_len

        return formatted

class ConversationalRAG:
    """
    Conversational RAG Engine indexing repository documentation and Python code files.
    Manages semantic chunking, context window budgeting, and coding agent tool retrieval.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent
        self.chunks: List[Chunk] = []
        self.context_mgr = ContextWindowManager(max_context_chars=7500)
        self._load_and_index()

    def _load_and_index(self):
        self.chunks.clear()
        self._index_markdown_docs()
        self._index_python_code()

    def _index_markdown_docs(self):
        for doc_file in INDEXED_DOCS:
            fpath = self.base_dir / doc_file
            if not fpath.exists():
                continue

            try:
                raw = fpath.read_text(encoding="utf-8")
                lines = raw.splitlines()
                current_section = f"{doc_file} Overview"
                current_lines = []

                for line in lines:
                    if line.startswith("#"):
                        if current_lines:
                            body = "\n".join(current_lines).strip()
                            if len(body) > 30:
                                self.chunks.append(
                                    Chunk(
                                        file_path=doc_file,
                                        section_name=current_section,
                                        content=body,
                                        chunk_type="doc",
                                        language="markdown",
                                    )
                                )
                        current_section = line.lstrip("#").strip()
                        current_lines = [line]
                    else:
                        current_lines.append(line)

                if current_lines:
                    body = "\n".join(current_lines).strip()
                    if len(body) > 30:
                        self.chunks.append(
                            Chunk(
                                file_path=doc_file,
                                section_name=current_section,
                                content=body,
                                chunk_type="doc",
                                language="markdown",
                            )
                        )
            except Exception:
                pass

    def _index_python_code(self):
        for code_file in INDEXED_CODE_FILES:
            fpath = self.base_dir / code_file
            if not fpath.exists():
                continue

            try:
                raw = fpath.read_text(encoding="utf-8")
                lines = raw.splitlines()
                current_symbol = f"{code_file} Header"
                current_lines = []

                for line in lines:
                    # Detect class or function definitions
                    if re.match(r"^(class\s+[A-Za-z0-9_]+|def\s+[A-Za-z0-9_]+|async\s+def\s+[A-Za-z0-9_]+)", line):
                        if current_lines:
                            body = "\n".join(current_lines).strip()
                            if len(body) > 40:
                                self.chunks.append(
                                    Chunk(
                                        file_path=code_file,
                                        section_name=current_symbol,
                                        content=body,
                                        chunk_type="code",
                                        language="python",
                                    )
                                )
                        match = re.match(r"^(class|def|async\s+def)\s+([A-Za-z0-9_]+)", line)
                        current_symbol = f"{match.group(2)} ({code_file})" if match else line.strip()
                        current_lines = [line]
                    else:
                        current_lines.append(line)

                if current_lines:
                    body = "\n".join(current_lines).strip()
                    if len(body) > 40:
                        self.chunks.append(
                            Chunk(
                                file_path=code_file,
                                section_name=current_symbol,
                                content=body,
                                chunk_type="code",
                                language="python",
                            )
                        )
            except Exception:
                pass

    def search(
        self,
        query: str,
        history: Optional[List[Dict[str, Any]]] = None,
        top_k: int = 4,
        max_total_chars: int = 5000,
    ) -> Optional[Dict[str, Any]]:
        """
        Performs conversational semantic search with context window budgeting.
        """
        reformulated_query = self.context_mgr.reformulate_conversational_query(query, history)
        query_tokens = tokenize(reformulated_query)
        if not query_tokens:
            return None

        scored: List[Tuple[Chunk, float]] = []
        raw_query_lower = query.lower()
        ref_query_lower = reformulated_query.lower()

        for chunk in self.chunks:
            score = 0.0
            section_tokens = tokenize(chunk.section_name)
            file_tokens = tokenize(chunk.file_path)

            # 1. Section & file match boost
            for q_tok in query_tokens:
                if q_tok in section_tokens:
                    score += 4.5
                if q_tok in file_tokens:
                    score += 3.0
                if q_tok in chunk.tokens:
                    score += 1.2
                if q_tok in chunk.content.lower():
                    score += 0.4

            # 2. Exact phrase match bonus
            if len(query) > 4 and query.lower() in chunk.content.lower():
                score += 5.0

            # 3. Code match bonus if user specifically requested code/implementation
            if ("code" in raw_query_lower or "implementation" in raw_query_lower or "class" in raw_query_lower or "def" in raw_query_lower) and chunk.chunk_type == "code":
                score += 3.0

            if score > 2.0:
                scored.append((chunk, score))

        if not scored:
            return None

        scored.sort(key=lambda x: x[1], reverse=True)

        # Context Window Budget Management & File Diversity
        selected_chunks: List[Chunk] = []
        file_counts: Dict[str, int] = {}
        total_chars = 0

        for ch, sc in scored:
            if len(selected_chunks) >= top_k:
                break

            current_file_count = file_counts.get(ch.file_path, 0)
            if current_file_count >= 2:  # Prevent 1 file from dominating the context window
                continue

            if total_chars + ch.char_count > max_total_chars and selected_chunks:
                # If budget exceeded, stop adding to avoid context truncation
                continue

            selected_chunks.append(ch)
            file_counts[ch.file_path] = current_file_count + 1
            total_chars += ch.char_count

        if not selected_chunks:
            selected_chunks = [scored[0][0]]

        sources = []
        for ch in selected_chunks:
            preview = ch.content[:240].replace("\n", " ").strip() + "..."
            sources.append({
                "file": ch.file_path,
                "section": ch.section_name,
                "type": ch.chunk_type,
                "language": ch.language,
                "charCount": ch.char_count,
                "snippet": preview,
            })

        # Formulate cleanly formatted Markdown context without abrupt slicing
        formatted_sections = []
        code_snippets = []

        for ch in selected_chunks:
            file_link = f"[{ch.file_path}](file://{self.base_dir}/{ch.file_path})"
            if ch.chunk_type == "code":
                code_snippets.append({
                    "file": ch.file_path,
                    "symbol": ch.section_name,
                    "language": ch.language,
                    "code": ch.content,
                })
                formatted_sections.append(
                    f"#### 💻 Source Code: {file_link} § `{ch.section_name}`\n"
                    f"```{ch.language}\n{ch.content}\n```"
                )
            else:
                formatted_sections.append(
                    f"#### 📄 Documentation: {file_link} § {ch.section_name}\n\n{ch.content}"
                )

        assembled_context = "\n\n---\n\n".join(formatted_sections)

        return {
            "query": query,
            "reformulatedQuery": reformulated_query,
            "sources": sources,
            "contextText": assembled_context,
            "codeSnippets": code_snippets,
            "totalChars": total_chars,
            "estimatedTokens": total_chars // 4,
            "chunksCount": len(selected_chunks),
            "topTopic": selected_chunks[0].section_name,
        }

rag_engine = ConversationalRAG()

def query_documentation_rag(
    raw_query: str, history: Optional[List[Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    return rag_engine.search(raw_query, history=history)

def inspect_code_file(relative_path: str, max_lines: int = 120) -> Dict[str, Any]:
    """
    Direct tool for coding agent to inspect any code or doc file from the repository.
    """
    base_dir = Path(__file__).resolve().parent.parent
    target = base_dir / relative_path.lstrip("/")
    if not target.exists() or not target.is_file():
        return {
            "status": "error",
            "file": relative_path,
            "message": f"File '{relative_path}' not found in repository root.",
        }

    try:
        content = target.read_text(encoding="utf-8")
        lines = content.splitlines()
        truncated = len(lines) > max_lines
        code_view = "\n".join(lines[:max_lines])

        ext = target.suffix.lstrip(".")
        lang = "python" if ext == "py" else "markdown" if ext == "md" else "yaml" if ext in ["yaml", "yml"] else "text"

        return {
            "status": "success",
            "file": relative_path,
            "totalLines": len(lines),
            "displayedLines": min(len(lines), max_lines),
            "isTruncated": truncated,
            "language": lang,
            "content": code_view,
        }
    except Exception as e:
        return {
            "status": "error",
            "file": relative_path,
            "message": f"Error reading file: {str(e)}",
        }
