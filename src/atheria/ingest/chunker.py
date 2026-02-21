"""Section-aware, table-aware chunker."""

from atheria.models.chunk import Chunk, ChunkType
from atheria.models.paper import Paper
from atheria.ingest.pmc_parser import ParsedDocument, ParsedBlock


def chunk_document(doc: ParsedDocument, paper: Paper) -> list[Chunk]:
    """
    Chunk a parsed document into Chunk objects.

    Rules:
    - Chunk by semantic structure: headings, paragraphs, tables, captions
    - Prepend heading context: "Section: X > Subsection: Y > " + text
    - Tables: caption as one chunk, table body as another
    """
    paper_id_str = str(paper.paper_id)
    chunks: list[Chunk] = []

    for block in doc.blocks:
        section_path = block.section_path.copy()
        page = block.page

        # Map block_type to ChunkType
        chunk_type_map = {
            "paragraph": ChunkType.PARAGRAPH,
            "table": ChunkType.TABLE,
            "table_caption": ChunkType.CAPTION,
            "figure_caption": ChunkType.FIGURE_CAPTION,
        }
        chunk_type = chunk_type_map.get(block.block_type, ChunkType.PARAGRAPH)

        # Build text with section context
        if section_path:
            prefix = "Section: " + " > ".join(section_path) + " "
            full_text = prefix + block.text
        else:
            full_text = block.text

        chunk = Chunk.create(
            paper_id=paper_id_str,
            chunk_type=chunk_type,
            section_path=section_path,
            page_start=page,
            page_end=page,
            text=full_text,
        )
        # Override bm25_fields with the full text for indexing (chunk.create builds from section_path + text)
        chunk.bm25_fields = chunk.bm25_fields  # Already set by create
        chunks.append(chunk)

    return chunks
