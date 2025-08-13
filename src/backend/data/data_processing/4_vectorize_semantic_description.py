"""
Step 4: Vectorization of Semantic Descriptions (ETL Pipeline)

- Reads the 'semantic_description' column from each enriched table.
- Generates vector embeddings using a local embedding model (default: SentenceTransformers; can be swapped for Ollama/local LLMs).
- Stores the resulting vector in a new column 'semantic_vector' (DOUBLE PRECISION[] in Postgres).

Requirements:
- sentence-transformers
- numpy
- SQLAlchemy

Notes:
- Embeddings are computed in batches for speed.
- Vectors are bulk-updated via a temp table to avoid per-row UPDATEs.
"""

import os
import sys
import time
import logging
from typing import List

import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
try:
    import torch
except Exception:  # torch is optional; CPU fallback
    torch = None

# Load environment variables from .env file
load_dotenv()

pg_user = os.getenv('PG_USER')
pg_password = os.getenv('PG_PASSWORD')
pg_host = os.getenv('PG_HOST')
pg_port = os.getenv('PG_PORT')
pg_dbname = os.getenv('PG_DBNAME')

# Choose your embedding model (local, no external API)
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

# DB connection
engine = create_engine(f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}", echo=False)
logger = logging.getLogger(__name__)


def vectorize_table(
    table_name: str,
    id_col: str,
    text_col: str = 'semantic_description',
    vector_col: str = 'semantic_vector',
    batch_size: int = 2000,
    embed_batch_size: int = 64,
):
    """Vectorize a text column and store results in an array column.

    Args:
        table_name: Table to process.
        id_col: Primary key/unique identifier column.
        text_col: Name of the text column to embed.
        vector_col: Name of the output vector column (DOUBLE PRECISION[]).
        batch_size: Number of rows to process per DB batch.
        embed_batch_size: Number of texts per model.encode batch.
    """
    start_time = time.time()
    logger.info(f"Starting vectorization for {table_name}...")

    device = 'cuda' if (torch is not None and hasattr(torch, 'cuda') and torch.cuda.is_available()) else 'cpu'
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)

    # Ensure the output column exists
    with engine.begin() as connection:
        try:
            connection.execute(text("SET LOCAL statement_timeout = '30min'"))
        except Exception:
            pass
        connection.execute(text(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN IF NOT EXISTS {vector_col} DOUBLE PRECISION[]
            """
        ))

    total_updated = 0
    last_key = None
    while True:
        # Fetch a batch of rows missing vectors, ordered by id for stable pagination
        with engine.begin() as connection:
            try:
                connection.execute(text("SET LOCAL statement_timeout = '30min'"))
            except Exception:
                pass
            if last_key is None:
                query = text(
                    f"""
                    SELECT {id_col}, {text_col}
                    FROM {table_name}
                    WHERE {text_col} IS NOT NULL AND {text_col} <> '' AND {vector_col} IS NULL
                    ORDER BY {id_col}
                    LIMIT :limit
                    """
                )
                params = {"limit": batch_size}
            else:
                query = text(
                    f"""
                    SELECT {id_col}, {text_col}
                    FROM {table_name}
                    WHERE {id_col} > :last_key
                      AND {text_col} IS NOT NULL AND {text_col} <> '' AND {vector_col} IS NULL
                    ORDER BY {id_col}
                    LIMIT :limit
                    """
                )
                params = {"last_key": last_key, "limit": batch_size}
            rows = connection.execute(query, params).fetchall()

        if not rows:
            break

        ids: List[str] = [r[0] for r in rows]
        texts: List[str] = [r[1] for r in rows]

        # Compute embeddings in batches using SentenceTransformers
        vectors = model.encode(
            texts,
            batch_size=embed_batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        # Ensure Python lists for DB binding
        vec_list: List[List[float]] = vectors.astype(float).tolist()

        # Bulk update via temp table to avoid per-row UPDATE
        with engine.begin() as connection:
            try:
                connection.execute(text("SET LOCAL statement_timeout = '30min'"))
            except Exception:
                pass
            connection.execute(text("CREATE TEMP TABLE IF NOT EXISTS tmp_vecs(id_txt TEXT, vec DOUBLE PRECISION[]) ON COMMIT DROP"))
            # Truncate temp table in case it already exists in this session
            connection.execute(text("TRUNCATE tmp_vecs"))

            # Insert batch rows into temp table
            payload = [{"id": i, "vec": v} for i, v in zip(ids, vec_list)]
            connection.execute(text("INSERT INTO tmp_vecs(id_txt, vec) VALUES (:id, :vec)"), payload)

            # Update target table joining on id (cast to text to be generic)
            connection.execute(text(
                f"""
                UPDATE {table_name} AS t
                SET {vector_col} = v.vec
                FROM tmp_vecs AS v
                WHERE t.{id_col}::TEXT = v.id_txt
                """
            ))

        total_updated += len(ids)
        last_key = ids[-1]
        logger.info(f"Updated {len(ids)} vectors (total {total_updated}) for {table_name}; last key: {last_key}")

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Vectorization for {table_name} completed in {minutes}m {seconds}s ({elapsed:.2f} seconds).")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.info("Step 4: Vectorizing semantic_description columns...")
    start_all = time.time()
    # Prime vectors on dedup table updated in place (id = contract_transaction_unique_key)
    vectorize_table(
        table_name='s2_interim.usaspending_prime_awards_dedup',
        id_col='contract_transaction_unique_key',
        text_col='semantic_description',
        vector_col='semantic_vector',
        batch_size=500,
        embed_batch_size=32,
    )
    # Subawards vectors on enriched table (id = subaward_unique_key)
    vectorize_table(
        table_name='s2_interim.usaspending_subawards_enriched',
        id_col='subaward_unique_key',
        text_col='semantic_description',
        vector_col='semantic_vector',
        batch_size=2000,
        embed_batch_size=64,
    )
    elapsed_all = time.time() - start_all
    minutes_all = int(elapsed_all // 60)
    seconds_all = int(elapsed_all % 60)
    logger.info(f"Semantic vector columns created and populated for all tables in {minutes_all}m {seconds_all}s ({elapsed_all:.2f} seconds).")

if __name__ == "__main__":
    main()

"""
# To use Ollama for embeddings instead of SentenceTransformers:
# - Start Ollama with an embedding-capable model (e.g., llama2, mistral, etc.)
# - Replace the model.encode() call with an HTTP POST to your local Ollama server's /api/embeddings endpoint.
# - See Ollama docs for details.
"""
