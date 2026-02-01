import math
import pickle
import os
from collections import defaultdict

from indexing.text_preprocessor import TextPreprocessor


class AdvancedInvertedIndex:
    def __init__(self):
        # term -> list of (doc_id, weighted_tf)
        self.index = defaultdict(list)

        # doc_id -> document metadata
        self.documents = {}

        # doc_id -> document vector norm
        self.doc_norms = {}

    # -------------------------------------------------
    # ADD DOCUMENT TO INDEX
    # -------------------------------------------------
    def add_document(self, doc_id, doc_data):
        self.documents[doc_id] = doc_data

        searchable_fields = {
            "title": doc_data.get("title", ""),
            "authors": " ".join(doc_data.get("authors", [])),
            "year": str(doc_data.get("year", "")),
            "abstract": doc_data.get("abstract", ""),
            "keywords": " ".join(doc_data.get("keywords", [])),
        }

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

            for token in tokens:
                tf = tokens.count(token)
                weighted_tf = tf * field_weights[field]
                self.index[token].append((doc_id, weighted_tf))

    # -------------------------------------------------
    # FINALIZE INDEX (COMPUTE DOCUMENT NORMS)
    # -------------------------------------------------
    def finalize(self):
        """
        Precompute full document vector norms for cosine similarity
        """
        doc_vectors = defaultdict(lambda: defaultdict(float))

        for term, postings in self.index.items():
            df = len(set(doc_id for doc_id, _ in postings))
            idf = math.log((len(self.documents) + 1) / (df + 1)) + 1

            for doc_id, tf in postings:
                doc_vectors[doc_id][term] += tf * idf

        self.doc_norms = {}
        for doc_id, vector in doc_vectors.items():
            self.doc_norms[doc_id] = math.sqrt(
                sum(weight ** 2 for weight in vector.values())
            )

    # -------------------------------------------------
    # SEARCH (TF-IDF + TRUE COSINE SIMILARITY)
    # -------------------------------------------------
    def search(self, query):
        processed = TextPreprocessor.preprocess(query)
        tokens = TextPreprocessor.tokenize(processed)
        tokens = TextPreprocessor.remove_stopwords(tokens)

        if not tokens or not self.documents:
            return []

        # -------- QUERY VECTOR --------
        query_tf = defaultdict(int)
        for t in tokens:
            query_tf[t] += 1

        query_vector = {}
        for term, tf in query_tf.items():
            if term in self.index:
                df = len(set(doc_id for doc_id, _ in self.index[term]))
                idf = math.log((len(self.documents) + 1) / (df + 1)) + 1
                query_vector[term] = tf * idf

        if not query_vector:
            return []

        query_norm = math.sqrt(sum(w ** 2 for w in query_vector.values()))
        if query_norm == 0:
            return []

        # -------- DOT PRODUCT --------
        scores = defaultdict(float)

        for term, q_weight in query_vector.items():
            df = len(set(doc_id for doc_id, _ in self.index[term]))
            idf = math.log((len(self.documents) + 1) / (df + 1)) + 1

            for doc_id, tf in self.index.get(term, []):
                scores[doc_id] += q_weight * (tf * idf)

        # -------- COSINE SIMILARITY --------
        results = []
        for doc_id, dot_product in scores.items():
            doc_norm = self.doc_norms.get(doc_id)

            if not doc_norm or doc_norm == 0:
                continue

            cosine_score = dot_product / (query_norm * doc_norm)
            results.append((doc_id, self.documents[doc_id], cosine_score))

        results.sort(key=lambda x: x[2], reverse=True)
        return results

    # -------------------------------------------------
    # SAVE INDEX
    # -------------------------------------------------
    def save(self, filepath):
        with open(filepath, "wb") as f:
            pickle.dump(
                (dict(self.index), self.documents, self.doc_norms),
                f
            )

    # -------------------------------------------------
    # LOAD INDEX (SAFE + AUTO-FINALIZE)
    # -------------------------------------------------
    def load(self, filepath):
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, "rb") as f:
                index_data, documents, doc_norms = pickle.load(f)

            self.index = defaultdict(list, index_data)
            self.documents = documents

            # If norms missing or empty → recompute
            if not doc_norms:
                self.finalize()
            else:
                self.doc_norms = doc_norms

            return True

        except (EOFError, pickle.UnpicklingError):
            self.index = defaultdict(list)
            self.documents = {}
            self.doc_norms = {}
            return False
