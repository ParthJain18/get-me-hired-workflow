import pandas as pd
from sentence_transformers import SentenceTransformer, util
from config import COSINE_FILTER_TOP_N

print("Loading semantic search model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Semantic search model loaded.")

def filter_jobs_by_similarity(jobs: list[dict], ideal_candidate_profile: str) -> list[dict]:
    if not jobs:
        print("⚠️ No jobs to perform similarity filtering on.")
        return []
    
    print(f"Performing semantic similarity filtering on {len(jobs)} jobs...")

    df = pd.DataFrame(jobs)
    df['description'] = df['description'].fillna('').astype(str)
    
    profile_embedding = model.encode(ideal_candidate_profile, convert_to_tensor=True)
    job_embeddings = model.encode(df['description'].tolist(), convert_to_tensor=True, show_progress_bar=True)
    
    cosine_scores = util.cos_sim(profile_embedding, job_embeddings)
    
    df['similarity_score'] = cosine_scores[0].cpu().tolist()
    df_sorted = df.sort_values(by='similarity_score', ascending=False)
    
    print(f"✅ Semantic search complete. Top 5 matches:")
    for _, row in df_sorted.head(5).iterrows():
        print(f"   - Score: {row['similarity_score']:.4f}, Title: {row['title']}")

    top_jobs = df_sorted.head(COSINE_FILTER_TOP_N).to_dict('records')
    
    print(f"Filtered down to the top {len(top_jobs)} most relevant jobs.")
    return top_jobs