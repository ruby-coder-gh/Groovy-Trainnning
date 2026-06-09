"""
Sliding Window Chunking — splits text into overlapping chunks.

Strategy: Chunks of `chunk_size` characters with `overlap` characters
shared between consecutive chunks.
Pros: Preserves context across boundaries, better retrieval recall.
Cons: More embeddings, higher storage cost.
"""


class SlidingWindowChunker:
    """Splits text into overlapping fixed-size chunks."""

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        """
        Args:
            chunk_size: Number of characters per chunk (default: 500).
            overlap: Number of overlapping characters between chunks (default: 100).
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

        if overlap >= chunk_size:
            raise ValueError(f"Overlap ({overlap}) must be less than chunk_size ({chunk_size}).")

    def chunk(self, text: str) -> list[dict]:
        """
        Split text into overlapping fixed-size chunks.

        Args:
            text: The full document text.

        Returns:
            List of dicts with keys: text, index, char_start, char_end.
        """
        chunks = []
        start = 0
        step = self.chunk_size - self.overlap

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

            if end >= len(text):
                break

            start += step

        return chunks

    def __repr__(self) -> str:
        return f"SlidingWindowChunker(chunk_size={self.chunk_size}, overlap={self.overlap})"
