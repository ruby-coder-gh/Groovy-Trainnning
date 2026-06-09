"""
Fixed-Size Chunking — splits text into equal-sized chunks by character count.

Strategy: Hard cut at `chunk_size` characters with no overlap.
Pros: Fast, simple, easy implementation.
Cons: Can cut sentences in half, loses context, retrieval quality lower.
"""


class FixedChunker:
    """Splits text into fixed-size character chunks with no overlap."""

    def __init__(self, chunk_size: int = 500):
        """
        Args:
            chunk_size: Number of characters per chunk (default: 500).
        """
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[dict]:
        """
        Split text into fixed-size chunks.

        Args:
            text: The full document text.

        Returns:
            List of dicts with keys: text, index, char_start, char_end.
        """
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "index": len(chunks),
                    "char_start": start,
                    "char_end": end,
                })

            start = end

        return chunks

    def __repr__(self) -> str:
        return f"FixedChunker(chunk_size={self.chunk_size})"
