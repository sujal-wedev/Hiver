"""
Milestone 2: Intent Taxonomy Discovery via Sentence Embeddings and K-Means.
Embeds customer messages, sweeps k=6..14 with silhouette scoring,
generates cluster summary and plots results/silhouette_sweep.png.
"""

import os
import argparse
import logging
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def discover_clusters(
    data_path: str = "data/processed/amazonhelp_customer_msgs.parquet",
    output_dir: str = "results",
    sample_size: int = 1500,
    seed: int = 42,
    k_min: int = 6,
    k_max: int = 14,
    chosen_k: int = 8
):
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Loading customer messages from {data_path}...")
    df = pd.read_parquet(data_path)

    if len(df) > sample_size:
        df_sample = df.sample(n=sample_size, random_state=seed).reset_index(drop=True)
    else:
        df_sample = df.copy()

    texts = df_sample["text"].tolist()
    logger.info(f"Embedding {len(texts)} messages with all-MiniLM-L6-v2...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)

    logger.info(f"Sweeping k={k_min}..{k_max}...")
    k_range = list(range(k_min, k_max + 1))
    silhouette_scores = []
    models = {}

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=seed, n_init=10)
        labels = km.fit_predict(embeddings)
        score = silhouette_score(embeddings, labels)
        silhouette_scores.append(score)
        models[k] = (km, labels)
        logger.info(f"  k={k}: Silhouette Score = {score:.4f}")

    # Plot silhouette sweep
    plt.figure(figsize=(9, 5))
    plt.plot(k_range, silhouette_scores, marker="o", color="#2563EB", linewidth=2.5, markersize=8)
    plt.axvline(x=chosen_k, color="#DC2626", linestyle="--", label=f"Selected k={chosen_k}")
    plt.title("K-Means Silhouette Score vs. Number of Clusters (AmazonHelp)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Number of Clusters (k)", fontsize=11)
    plt.ylabel("Silhouette Score", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "silhouette_sweep.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()
    logger.info(f"Silhouette sweep plot saved to {plot_path}")

    # For chosen_k, sample 15 messages per cluster closest to centroid
    best_km, best_labels = models[chosen_k]
    df_sample["cluster"] = best_labels

    llm = LLMClient()
    cluster_proposals = []

    logger.info(f"Proposing labels for k={chosen_k} clusters...")
    for cluster_id in range(chosen_k):
        centroid = best_km.cluster_centers_[cluster_id]
        cluster_indices = np.where(best_labels == cluster_id)[0]
        cluster_embs = embeddings[cluster_indices]

        # Distances to centroid
        dists = np.linalg.norm(cluster_embs - centroid, axis=1)
        top_indices = cluster_indices[np.argsort(dists)[:15]]
        sample_msgs = [texts[idx] for idx in top_indices]

        # One-off exploratory prompt
        prompt = f"""Given the following 15 representative customer tweets sent to @AmazonHelp in a single cluster:

{chr(10).join([f"- {m}" for m in sample_msgs])}

Propose a concise intent name (snake_case) and a 1-sentence definition.
Return STRICT JSON: {{"intent_name": "...", "definition": "..."}}"""

        res = llm.generate_json(prompt)
        intent_name = res.get("intent_name", f"cluster_{cluster_id}")
        definition = res.get("definition", "Representative cluster of customer tweets.")

        cluster_proposals.append({
            "cluster_id": cluster_id,
            "size": int(np.sum(best_labels == cluster_id)),
            "proposed_name": intent_name,
            "definition": definition,
            "samples": sample_msgs[:3]
        })
        logger.info(f"Cluster {cluster_id} ({np.sum(best_labels == cluster_id)} msgs) -> {intent_name}")

    summary_path = os.path.join(output_dir, "cluster_discovery_summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Intent Clustering Discovery (k={chosen_k})\n\n")
        f.write(f"Sampled `{len(texts)}` messages. Optimal k evaluated across {k_min}..{k_max}.\n\n")
        for cp in cluster_proposals:
            f.write(f"### Cluster {cp['cluster_id']}: `{cp['proposed_name']}` ({cp['size']} messages)\n")
            f.write(f"- **Definition**: {cp['definition']}\n")
            f.write("- **Examples**:\n")
            for s in cp["samples"]:
                f.write(f"  - \"{s}\"\n")
            f.write("\n")

    logger.info(f"Cluster discovery summary saved to {summary_path}")

def main():
    parser = argparse.ArgumentParser(description="Discover intent taxonomy via clustering")
    parser.add_argument("--data-path", type=str, default="data/processed/amazonhelp_customer_msgs.parquet")
    parser.add_argument("--output-dir", type=str, default="results")
    parser.add_argument("--sample-size", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--chosen-k", type=int, default=8)
    args = parser.parse_args()

    discover_clusters(args.data_path, args.output_dir, args.sample_size, args.seed, chosen_k=args.chosen_k)

if __name__ == "__main__":
    main()
