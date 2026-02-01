# =========================================================
# PATH FIX (DO NOT REMOVE)
# =========================================================
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# =========================================================
# IMPORTS
# =========================================================
import streamlit as st
import json

from crawler.selenium_crawler import ImprovedSeleniumCrawler
from indexing.inverted_index import AdvancedInvertedIndex
from evaluation.ir_metrics import (
    precision,
    recall,
    f1_score,
    average_precision,
    mean_average_precision
)

# =========================================================
# CONFIG
# =========================================================
DATA_FILE = "data/publications.json"
INDEX_FILE = "data/search_index.pkl"

BASE_URL = (
    "https://pureportal.coventry.ac.uk/en/organisations/"
    "ics-research-centre-for-computational-science-and-mathematical-mo"
)

os.makedirs("data", exist_ok=True)

# =========================================================
# GROUND TRUTH (DEMO PURPOSE)
# =========================================================
GROUND_TRUTH = {
    "model": [0, 1, 2, 3],
    "modelling": [0, 2, 4],
    "computational": [1, 3, 5],
    "analysis": [0, 1, 3],
}

# =========================================================
# LOAD INDEX
# =========================================================
index = AdvancedInvertedIndex()
loaded = index.load(INDEX_FILE)

# =========================================================
# HELPER: STATISTICS
# =========================================================
def compute_statistics(index):
    years = {}
    authors = set()

    for doc in index.documents.values():
        year = doc.get("year")
        if year is None or not str(year).isdigit():
            year = "N/A"
        else:
            year = int(year)

        years[year] = years.get(year, 0) + 1

        for a in doc.get("authors", []):
            authors.add(a)

    sorted_years = dict(
        sorted(
            years.items(),
            key=lambda x: (x[0] == "N/A", -x[0] if isinstance(x[0], int) else 0)
        )
    )

    return {
        "total_docs": len(index.documents),
        "unique_terms": len(index.index),
        "total_authors": len(authors),
        "years": sorted_years
    }

# =========================================================
# STREAMLIT PAGE
# =========================================================
st.set_page_config(
    page_title="Coventry University Research Search Engine",
    layout="wide"
)

st.title("🎓 Coventry University – Research Search Engine")
st.caption("Vertical Search Engine | PurePortal Publications Only")

if not loaded:
    st.warning("Index not found or invalid. Please run the crawler.")

# =========================================================
# SIDEBAR – CONTROLS
# =========================================================
st.sidebar.header("⚙️ Controls")

# -------- MAX AUTHORS --------
max_authors = st.sidebar.slider(
    "Max Authors to Crawl",
    min_value=5,
    max_value=100,
    value=20,
    step=5
)

# -------- RUN CRAWLER --------
if st.sidebar.button("🕷️ Run Selenium Crawler"):
    st.sidebar.info("Crawling in progress… please wait")

    crawler = ImprovedSeleniumCrawler()
    publications = crawler.crawl_department(
        BASE_URL,
        max_authors=max_authors
    )

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(publications, f, indent=2)

    index = AdvancedInvertedIndex()
    for i, pub in enumerate(publications):
        index.add_document(i, pub)

    index.finalize()
    index.save(INDEX_FILE)

    st.sidebar.success(f"Indexed {len(publications)} publications")

# -------- MAP --------
if st.sidebar.button("📊 Evaluate MAP"):
    ap_scores = []
    for q, rel_docs in GROUND_TRUTH.items():
        results = index.search(q)
        retrieved_ids = [doc_id for doc_id, _, _ in results]
        ap_scores.append(average_precision(retrieved_ids, set(rel_docs)))

    st.sidebar.success(
        f"MAP Score: {mean_average_precision(ap_scores):.3f}"
    )

# -------- STATISTICS --------
st.sidebar.markdown("## 📊 Statistics")

if index.documents:
    stats = compute_statistics(index)
    st.sidebar.metric("Publications", stats["total_docs"])
    st.sidebar.metric("Unique Terms", stats["unique_terms"])
    st.sidebar.metric("Authors", stats["total_authors"])

    st.sidebar.markdown("### 📅 Publications by Year")
    for y, c in list(stats["years"].items())[:6]:
        st.sidebar.write(f"{y}: {c}")
else:
    st.sidebar.info("No statistics available.")

# =========================================================
# SEARCH
# =========================================================
st.markdown("## 🔍 Search Publications")

query = st.text_input(
    "Enter keywords",
    placeholder="Try: modelling, computational, analysis"
)

if query:
    results = index.search(query)

    if not results:
        st.warning("No results found.")
    else:
        st.success(f"Found {len(results)} results")

        for rank, (doc_id, doc, score) in enumerate(results[:20], start=1):

            col_main, col_side = st.columns([4, 1])

            # -------- MAIN COLUMN --------
            with col_main:
                if doc.get("publication_link"):
                    st.markdown(
                        f"### {rank}. "
                        f"[{doc.get('title','No Title')}]({doc['publication_link']})"
                    )
                else:
                    st.markdown(
                        f"### {rank}. {doc.get('title','No Title')}"
                    )

                st.write(
                    f"**Year:** {doc.get('year','N/A')} | "
                    f"**Score:** {round(score,3)}"
                )

                abstract = doc.get("abstract", "")
                title = doc.get("title", "")

                snippet = (
                    abstract[:300]
                    if abstract and len(abstract) > 40
                    else f"This publication titled '{title}' "
                         f"contributes to research in computational science "
                         f"and mathematical modelling."
                )

                st.markdown(
                    f"<p style='color:#555;font-size:0.9em'>{snippet}...</p>",
                    unsafe_allow_html=True
                )

            # -------- SIDE COLUMN --------
            with col_side:
                st.markdown("**Authors**")
                st.write(", ".join(doc.get("authors", [])))
                if doc.get("profile_link"):
                    st.markdown(
                        f"[👤 Author Profile]({doc['profile_link']})"
                    )

            st.markdown("---")

        # -------- QUERY EVALUATION --------
        matched = next(
            (k for k in GROUND_TRUTH if k in query.lower()),
            None
        )

        if matched:
            rel = set(GROUND_TRUTH[matched])
            ret = [doc_id for doc_id, _, _ in results]

            tp = len(set(ret) & rel)
            fp = len(set(ret) - rel)
            fn = len(rel - set(ret))

            st.sidebar.markdown("## 📊 Evaluation")
            st.sidebar.metric("Precision", round(precision(tp, fp), 3))
            st.sidebar.metric("Recall", round(recall(tp, fn), 3))
            st.sidebar.metric(
                "F1-Score",
                round(
                    f1_score(
                        precision(tp, fp),
                        recall(tp, fn)
                    ),
                    3
                )
            )
            st.sidebar.metric(
                "Average Precision",
                round(average_precision(ret, rel), 3)
            )
        else:
            st.sidebar.info("No ground truth for this query.")

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.caption(
    "Information Retrieval Assignment | "
    "TF-IDF + Cosine Similarity | Selenium + Streamlit"
)
