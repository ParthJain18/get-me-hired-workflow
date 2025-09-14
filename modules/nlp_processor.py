from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from config import COSINE_FILTER_TOP_N


def filter_jobs_by_similarity(jobs_list, resume_text):
    if not jobs_list:
        print("No jobs to process. Skipping filtering.")
        return []

    print(
        f"Performing cosine similarity filtering on {len(jobs_list)} jobs...")
    df = pd.DataFrame(jobs_list)
    df['description'].fillna('', inplace=True)

    documents = [resume_text] + df['description'].tolist()

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(documents).toarray()  # type: ignore

    resume_vector = tfidf_matrix[0:1]
    cosine_sim = cosine_similarity(resume_vector, tfidf_matrix[1:])

    df['similarity_score'] = cosine_sim[0]

    top_jobs_df = df.sort_values(
        by='similarity_score', ascending=False).head(COSINE_FILTER_TOP_N)

    print(f"? Filtered down to the top {len(top_jobs_df)} most relevant jobs.")
    return top_jobs_df.to_dict('records')
