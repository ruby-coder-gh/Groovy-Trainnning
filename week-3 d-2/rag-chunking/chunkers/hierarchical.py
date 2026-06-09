"""
Hierarchical Chunking — splits document into two levels: sections and paragraphs.

Structure:
  Document
   ├─ Section (heading + its content)
       ├─ Paragraph 1
       ├─ Paragraph 2
       ...

Retrieval flow:
  1. Find relevant sections (coarse search)
  2. Find relevant paragraphs within those sections (fine search)
  3. Send best paragraphs to LLM

Pros: Scales to huge documents, better precision.
Cons: More complex, requires document structure awareness.
"""

import re


class HierarchicalChunker:
    """
    Splits text into a two-level hierarchy: sections and paragraphs.

    Sections are defined by markdown-style headings (## or ###).
    Paragraphs are split by double newlines within each section.
    """

    def __init__(self, max_paragraph_chars: int = 500):
        """
        Args:
            max_paragraph_chars: Maximum characters per paragraph chunk (default: 500).
                               Longer paragraphs are further split.
        """
        self.max_paragraph_chars = max_paragraph_chars

    def chunk(self, text: str) -> list[dict]:
        """
        Split text into hierarchical chunks (paragraph level).

        Each chunk includes metadata: section_heading, section_index, level,
        parent_section_id for tracing back to the parent section.

        Args:
            text: The full document text.

        Returns:
            List of paragraph-level chunks with metadata.
        """
        # Step 1: Parse sections (by markdown headings)
        sections = self._parse_sections(text)

        # Step 2: Split each section into paragraphs
        chunks = []
        for section in sections:
            paragraphs = self._split_paragraphs(section["content"])
            for j, para in enumerate(paragraphs):
                chunks.append({
                    "text": para,
                    "index": len(chunks),
                    "section_heading": section["heading"],
                    "section_index": section["index"],
                    "level": section["level"],
                    "paragraph_index": j,
                    "char_start": section["char_start"],
                    "char_end": section["char_end"],
                })

        return chunks

    def get_sections(self, text: str) -> list[dict]:
        """
        Get only the section-level chunks (coarse level).

        Returns:
            List of section-level chunks with headings.
        """
        return self._parse_sections(text)

    def _parse_sections(self, text: str) -> list[dict]:
        """
        Parse text into sections based on markdown headings (## or ###).
        If no headings found, treat entire text as one section.
        """
        # Pattern matches ## or ### headings
        heading_pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)

        sections = []
        last_pos = 0
        last_heading = "(Introduction)"
        last_level = 2
        section_index = -1

        for match in heading_pattern.finditer(text):
            # Save previous section
            if match.start() > last_pos:
                section_index += 1
                content = text[last_pos:match.start()].strip()
                sections.append({
                    "heading": last_heading,
                    "content": content,
                    "index": section_index,
                    "level": last_level,
                    "char_start": last_pos,
                    "char_end": match.start(),
                })

            last_heading = match.group(2).strip()
            last_level = len(match.group(1))
            last_pos = match.start()

        # Last section
        if last_pos < len(text):
            section_index += 1
            content = text[last_pos:].strip()
            sections.append({
                "heading": last_heading,
                "content": content,
                "index": section_index,
                "level": last_level,
                "char_start": last_pos,
                "char_end": len(text),
            })

        # Fallback: if no sections found, treat as one section
        if not sections:
            sections.append({
                "heading": "Document",
                "content": text.strip(),
                "index": 0,
                "level": 1,
                "char_start": 0,
                "char_end": len(text),
            })

        return sections

    def _split_paragraphs(self, text: str) -> list[str]:
        """
        Split section content into paragraphs.
        Paragraphs longer than max_paragraph_chars are further split.
        """
        # Split by double newlines (paragraph breaks)
        raw_paragraphs = re.split(r"\n\s*\n", text)

        paragraphs = []
        for para in raw_paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(para) <= self.max_paragraph_chars:
                paragraphs.append(para)
            else:
                # Split long paragraphs further
                sub_paras = self._split_long_paragraph(para)
                paragraphs.extend(sub_paras)

        return paragraphs

    def _split_long_paragraph(self, text: str) -> list[str]:
        """Split a long paragraph into smaller chunks at sentence boundaries."""
        chunks = []
        start = 0

        while start < len(text):
            if len(text) - start <= self.max_paragraph_chars:
                chunks.append(text[start:].strip())
                break

            # Try to break at sentence end within max_paragraph_chars
            end = start + self.max_paragraph_chars
            # Look for sentence boundary going backward
            sentence_end = max(
                text.rfind(". ", start, end),
                text.rfind("!\n", start, end),
                text.rfind("?\n", start, end),
                text.rfind("\n", start, end),
            )
            if sentence_end > start:
                end = sentence_end + 1
            else:
                # No sentence boundary found, break at space
                space_end = text.rfind(" ", start, end)
                if space_end > start:
                    end = space_end

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end

        return chunks

    def __repr__(self) -> str:
        return f"HierarchicalChunker(max_paragraph_chars={self.max_paragraph_chars})"
