"""Streamlit UI for Section Finder."""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st

from atheria.config import INDEX_DIR
from atheria.index.build_index import load_index
from atheria.retrieval.hybrid import hybrid_retrieve
from atheria.retrieval.formatter import format_results

st.set_page_config(page_title="Atheria Section Finder", layout="wide")


def load_index_safe():
    try:
        return load_index(INDEX_DIR)
    except FileNotFoundError:
        return None


@st.cache_resource
def get_index():
    return load_index_safe()


def main():
    st.title("Atheria — Biochem Paper Section Finder")
    st.caption("Find relevant sections for metric baseline queries (BM25 + MedCPT)")

    index_data = get_index()
    if index_data is None:
        st.error(
            "Index not found. Run from project root:\n"
            "```\npython -m atheria.api.app build -i data/raw/sample_pmc.xml\n```"
        )
        st.stop()

    paper_by_id, chunk_by_id, bm25, dense = index_data

    # Screen 1: Query box
    with st.form("query_form"):
        query = st.text_input(
            "Query",
            placeholder="e.g., electrophysiology assessment metrics",
            help="Free-text query for metric baselines",
        )
        paper_options = ["All"] + [f"{p.title[:50]}..." if len(p.title) > 50 else p.title for p in paper_by_id.values()]
        paper_ids = [None] + list(paper_by_id.keys())
        paper_filter_idx = st.selectbox(
            "Filter by paper (optional)",
            options=range(len(paper_options)),
            format_func=lambda i: paper_options[i],
            index=0,
        )
        paper_id_filter = paper_ids[paper_filter_idx] if paper_filter_idx > 0 else None
        top_n = st.slider("Number of results", 3, 15, 8)
        submitted = st.form_submit_button("Search")

    if submitted and query:
        paper_id = str(paper_id_filter) if paper_id_filter else None

        with st.spinner("Searching..."):
            results = hybrid_retrieve(
                query,
                bm25,
                dense,
                chunk_by_id,
                paper_by_id,
                top_n=top_n,
                paper_id=paper_id,
            )
            formatted = format_results(results, paper_by_id)

        st.session_state["results"] = formatted
        st.session_state["chunk_by_id"] = chunk_by_id
        st.session_state["selected_chunk_id"] = None

    # Screen 2: Results list
    if "results" in st.session_state and st.session_state["results"]:
        st.divider()
        st.subheader("Results")

        for i, sp in enumerate(st.session_state["results"]):
            # Short preview so 8 results from same paper/section still look distinct
            preview = (sp.snippets[0][:50] + "…") if sp.snippets else ""
            header = f"**{i+1}. {sp.section_path or '(no section)'}** — {sp.confidence}"
            if preview:
                header += f" — _{preview}_"
            with st.expander(header, expanded=(i == 0)):
                st.markdown(f"**Paper:** {sp.paper_title}")
                if sp.pmid:
                    st.caption(f"PMID: {sp.pmid}")
                st.markdown(f"**Pages:** {sp.page_start}-{sp.page_end}")
                for snip in sp.snippets:
                    st.write(f"> {snip}")
                if st.button("Open in context", key=f"open_{sp.chunk_id}"):
                    st.session_state["selected_chunk_id"] = sp.chunk_id
                    st.rerun()

        # Screen 3: Context viewer
        if "selected_chunk_id" in st.session_state and st.session_state["selected_chunk_id"]:
            st.divider()
            st.subheader("Context viewer")
            cid = st.session_state["selected_chunk_id"]
            chunk = st.session_state.get("chunk_by_id", {}).get(cid)
            if chunk:
                # Get prev/next chunks (by paper_id, page, section)
                all_chunks = sorted(
                    st.session_state["chunk_by_id"].values(),
                    key=lambda c: (c.paper_id, c.page_start, " ".join(c.section_path)),
                )
                idx = next((i for i, c in enumerate(all_chunks) if c.chunk_id == cid), -1)
                prev_chunk = all_chunks[idx - 1] if idx > 0 else None
                next_chunk = all_chunks[idx + 1] if idx >= 0 and idx < len(all_chunks) - 1 else None

                st.markdown("**Section path:** " + chunk.get_section_path_str())

                if prev_chunk:
                    with st.expander("Previous chunk", expanded=False):
                        st.write(prev_chunk.text[:500] + "..." if len(prev_chunk.text) > 500 else prev_chunk.text)

                st.info(chunk.text)

                if next_chunk:
                    with st.expander("Next chunk", expanded=False):
                        st.write(next_chunk.text[:500] + "..." if len(next_chunk.text) > 500 else next_chunk.text)

                if st.button("Close context"):
                    st.session_state["selected_chunk_id"] = None
                    st.rerun()


if __name__ == "__main__":
    main()
