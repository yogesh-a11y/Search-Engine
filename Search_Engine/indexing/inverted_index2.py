import math
import pickle
import os
from collections import defaultdict

from indexing.text_preprocessor import TextPreprocessor


class AdvancedInvertedIndex:
    def __init__(self):
        # token -> list of (doc_id, weighted_tf)
        self.index = defaultdict(list)

        # doc_id -> document data (dict)
        self.documents = {}

    # -------------------------------------------------
    # ADD DOCUMENT TO INDEX
    # -------------------------------------------------
    def add_document(self, doc_id, doc_data):
        """
        doc_data must be a dictionary containing:
        title, authors, year, abstract, keywords, etc.
        """

        self.documents[doc_id] = doc_data

        searchable_fields = {
            "title": doc_data.get("title", ""),
            "authors": " ".join(doc_data.get("authors", [])),
            "year": str(doc_data.get("year", "")),
            "abstract": doc_data.get("abstract", ""),
            "keywords": " ".join(doc_data.get("keywords", [])),
        }

        # Field importance (boosting)
        field_weights = {
            "title": 3.0,
            "authors": 2.5,
            "year": 1.5,
            "keywords": 2.0,
            "abstract": 1.0,
        }

        for field, text in searchable_fields.items():
            processed = TextPreprocessor.preprocess(text)
            tokens = TextPreprocessor.tokenize(processed)
            tokens = TextPreprocessor.remove_stopwords(tokens)

            for token in set(tokens):
                tf = tokens.count(token)
                weighted_tf = tf * field_weights[field]
                self.index[token].append((doc_id, weighted_tf))

    # -------------------------------------------------
    # SEARCH (TF-IDF RANKING)
    # -------------------------------------------------
    def search(self, query):
        processed = TextPreprocessor.preprocess(query)
        tokens = TextPreprocessor.tokenize(processed)
        tokens = TextPreprocessor.remove_stopwords(tokens)

        scores = defaultdict(float)

        for token in tokens:
            if token in self.index:
                df = len(set(doc_id for doc_id, _ in self.index[token]))
                idf = math.log((len(self.documents) + 1) / (df + 1)) + 1

                for doc_id, tf in self.index[token]:
                    scores[doc_id] += tf * idf

        ranked_results = sorted(
            scores.items(), key=lambda x: x[1], reverse=True
        )

        return [
            (doc_id, self.documents[doc_id], score)
            for doc_id, score in ranked_results
            if doc_id in self.documents
        ]

    # -------------------------------------------------
    # SAVE INDEX (PICKLE)
    # -------------------------------------------------
    def save(self, filepath):
        with open(filepath, "wb") as f:
            pickle.dump((dict(self.index), self.documents), f)

    # -------------------------------------------------
    # LOAD INDEX (SAFE – FIXES EOFError)
    # -------------------------------------------------
    def load(self, filepath):
        """
        Safe loader:
        - Handles missing file
        - Handles empty/corrupted pickle
        - NEVER crashes Streamlit
        """

        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "rb") as f:
                index_data, documents = pickle.load(f)

            self.index = defaultdict(list, index_data)
            self.documents = documents
            return True

        except (EOFError, pickle.UnpicklingError):
            # File exists but is empty or corrupted
            self.index = defaultdict(list)
            self.documents = {}
            return False
