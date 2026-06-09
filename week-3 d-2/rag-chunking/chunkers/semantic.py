"""
Semantic Chunking — splits text by meaning using natural boundaries.

Strategy: Uses LangChain's RecursiveCharacterTextSplitter to split at
natural text boundaries in order of priority:
  1. Paragraph breaks (\n\n)
  2. Newlines (\n)
  3. Sentence endings (. )
  4. Word boundaries (space)

Pros: Most natural retrieval, better context preservation.
Cons: Harder implementation, requires NLP processing library.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


class SemanticChunker:
    """Splits text into semantically meaningful chunks using recursive character splitting."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Args:
            chunk_size: Target chunk size in characters (default: 500).
            overlap: Overlap characters between chunks (default: 50).
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

        # Use LangChain's RecursiveCharacterTextSplitter
        # Separators tried in order: double newline → newline → period-space → space
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
            keep_separator=False,
        )

    def chunk(self, text: str) -> list[dict]:
        """
        Split text into semantically meaningful chunks.

        Args:
            text: The full document text.

        Returns:
            List of dicts with keys: text, index, char_start, char_end.
        """
        # RecursiveCharacterTextSplitter doesn't give char offsets natively,
        # so we compute them by searching for each chunk in the source text.
        raw_chunks = self.splitter.split_text(text)

        chunks = []
        search_start = 0

        for i, chunk_text in enumerate(raw_chunks):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue

            # Find position of this chunk in the original text
            char_start = text.find(chunk_text, search_start)
            if char_start == -1:
                # Fallback: approximate position
                char_start = search_start

            char_end = char_start + len(chunk_text)
            search_start = char_end

            chunks.append({
                "text": chunk_text,
                "index": i,
                "char_start": char_start,
                "char_end": char_end,
            })

        return chunks

    def __repr__(self) -> str:
        return f"SemanticChunker(chunk_size={self.chunk_size}, overlap={self.overlap})"
