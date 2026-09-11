"""
Milestone 1: Data Preparation & Thread Reconstruction for AmazonHelp.
Chunks twcs.csv, reconstructs customer-brand threads, cleans text, subsamples,
saves Parquet datasets, and computes EDA metrics.
"""

import os
import re
import sys
import argparse
import logging
from collections import Counter
from datetime import datetime
import pandas as pd
import numpy as np

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HF_TWCS_URL = "https://huggingface.co/datasets/SunidhiSriram/twcs/resolve/main/twcs.csv"

def clean_tweet_text(text: str) -> tuple[str, list[str]]:
    """
    Cleans tweet text:
    - Extracts and removes @mentions
    - Removes URLs
    - Preserves emojis and sentiment-bearing punctuation
    - Normalizes extra whitespace
    """
    if not isinstance(text, str):
        return "", []

    mentions = re.findall(r"@([A-Za-z0-9_]+)", text)
    cleaned = re.sub(r"@[A-Za-z0-9_]+", "", text)
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned, mentions

def download_dataset(destination_path: str):
    """Downloads twcs.csv from public mirror if not present."""
    import requests
    logger.info(f"Downloading twcs.csv from {HF_TWCS_URL} to {destination_path}...")
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    with requests.get(HF_TWCS_URL, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(destination_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192 * 16):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and downloaded % (1024 * 1024 * 20) < (8192 * 16):
                        mb = downloaded / (1024 * 1024)
                        logger.info(f"Downloaded {mb:.1f} MB / {total_size / (1024*1024):.1f} MB")
    logger.info("Download complete.")

def compute_bigrams(texts: list[str], top_n: int = 20) -> list[tuple[str, int]]:
    stop_words = {
        "the", "to", "and", "a", "in", "it", "is", "i", "that", "for", "you", "my", "with",
        "on", "this", "have", "be", "at", "of", "me", "so", "but", "was", "not", "your", "from"
    }
    bigram_counter = Counter()
    for text in texts:
        tokens = re.findall(r"\b[a-z]{2,}\b", text.lower())
        meaningful = [t for t in tokens if t not in stop_words]
        for i in range(len(meaningful) - 1):
            bigram_counter[(meaningful[i], meaningful[i+1])] += 1
    return [(f"{k[0]} {k[1]}", v) for k, v in bigram_counter.most_common(top_n)]

def process_data(csv_path: str, output_dir: str, sample_size: int = 5000, seed: int = 42):
    np.random.seed(seed)
    processed_dir = os.path.join(output_dir, "processed")
    results_dir = os.path.join(PROJECT_ROOT, "results")
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    if not os.path.exists(csv_path):
        alt = os.path.join(PROJECT_ROOT, csv_path)
        if os.path.exists(alt):
            csv_path = alt
        else:
            logger.warning(f"File {csv_path} not found. Attempting automatic download from public mirror...")
            download_dataset(csv_path)

    logger.info(f"Pass 1: Scanning {csv_path} for AmazonHelp replies...")
    chunk_size = 100000

    amazon_replies = {}
    target_customer_tweet_ids = set()

    for chunk_idx, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False)):
        ah_rows = chunk[chunk["author_id"] == "AmazonHelp"]
        for _, row in ah_rows.iterrows():
            in_resp = row.get("in_response_to_tweet_id")
            if pd.notna(in_resp):
                try:
                    in_resp_id = int(float(in_resp))
                    target_customer_tweet_ids.add(in_resp_id)
                    if in_resp_id not in amazon_replies:
                        clean_rep, _ = clean_tweet_text(str(row.get("text", "")))
                        amazon_replies[in_resp_id] = {
                            "brand_reply": clean_rep,
                            "brand_tweet_id": str(row.get("tweet_id")),
                            "created_at": str(row.get("created_at")),
                        }
                except (ValueError, TypeError):
                    continue

    threads = []
    customer_msgs_list = []

    for chunk_idx, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False)):
        relevant_rows = chunk[chunk["tweet_id"].isin(target_customer_tweet_ids)]
        for _, row in relevant_rows.iterrows():
            tweet_id = int(row["tweet_id"])
            in_resp = row.get("in_response_to_tweet_id")
            if pd.isna(in_resp):
                raw_text = str(row.get("text", ""))
                clean_text, mentions = clean_tweet_text(raw_text)
                if len(clean_text) < 5:
                    continue

                reply_info = amazon_replies[tweet_id]
                thread_record = {
                    "thread_id": f"thread_{tweet_id}",
                    "customer_tweet_id": str(tweet_id),
                    "customer_msg": clean_text,
                    "brand_reply": reply_info["brand_reply"],
                    "brand_tweet_id": reply_info["brand_tweet_id"],
                    "created_at": reply_info["created_at"],
                    "removed_mentions": ",".join(mentions),
                }
                threads.append(thread_record)
                customer_msgs_list.append({
                    "tweet_id": str(tweet_id),
                    "text": clean_text,
                    "created_at": str(row.get("created_at")),
                })

    df_threads = pd.DataFrame(threads)
    df_customer = pd.DataFrame(customer_msgs_list).drop_duplicates(subset=["tweet_id"])

    if len(df_threads) > sample_size:
        df_threads = df_threads.sample(n=sample_size, random_state=seed).reset_index(drop=True)
        matching_ids = set(df_threads["customer_tweet_id"])
        df_customer = df_customer[df_customer["tweet_id"].isin(matching_ids)].reset_index(drop=True)

    threads_out = os.path.join(processed_dir, "amazonhelp_threads.parquet")
    customer_out = os.path.join(processed_dir, "amazonhelp_customer_msgs.parquet")

    df_threads.to_parquet(threads_out, index=False)
    df_customer.to_parquet(customer_out, index=False)
    logger.info(f"Saved threads to {threads_out} and customer msgs to {customer_out}")

def main():
    parser = argparse.ArgumentParser(description="Data preparation for AmazonHelp Twitter dataset")
    parser.add_argument("--csv-path", type=str, default="data/raw/twcs.csv")
    parser.add_argument("--output-dir", type=str, default="data")
    parser.add_argument("--sample-size", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    process_data(args.csv_path, args.output_dir, args.sample_size, args.seed)

if __name__ == "__main__":
    main()
