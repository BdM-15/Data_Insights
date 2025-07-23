"""
Step 4: Vectorization of Semantic Descriptions (ETL Pipeline)

- Reads the 'semantic_description' column from each enriched table.
- Generates vector embeddings using a local embedding model (default: SentenceTransformers, can be swapped for Ollama or other local LLMs).
- Stores the resulting vector in a new column 'semantic_vector' (type: BYTEA or ARRAY depending on DB setup).

Requirements:
- sentence-transformers (pip install sentence-transformers)
- numpy
- SQLAlchemy
- For Ollama: see comments below for API usage.

This script is modular and ready for orchestration in the ETL pipeline.
"""

import os
import sys
import time
import logging
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

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


def vectorize_table(table_name: str, text_col: str = 'semantic_description', vector_col: str = 'semantic_vector'):
    """
    Vectorize the semantic_description column and store as semantic_vector.
    Args:
        table_name: Table to process
        text_col: Name of the text column to embed
        vector_col: Name of the output vector column
    """
    start_time = time.time()
    logger.info(f"Starting vectorization for {table_name}...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    with engine.connect() as connection:
        # Add vector column if not exists (Postgres: BYTEA or FLOAT[])
        connection.execute(text(f"""
            ALTER TABLE {table_name}
            ADD COLUMN IF NOT EXISTS {vector_col} FLOAT[];
        """))
        # Fetch all ids and semantic_description
        rows = connection.execute(text(f"SELECT id, {text_col} FROM {table_name}")).fetchall()
        logger.info(f"Fetched {len(rows):,} rows from {table_name}.")
        for row in rows:
            rec_id, text_val = row
            if not text_val or not text_val.strip():
                continue
            embedding = model.encode(text_val, show_progress_bar=False, normalize_embeddings=True)
            # Store as float[] (Postgres array)
            embedding_list = embedding.tolist()
            connection.execute(text(f"""
                UPDATE {table_name}
                SET {vector_col} = :vec
                WHERE id = :rec_id
            """), {"vec": embedding_list, "rec_id": rec_id})
        connection.commit()
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
    vectorize_table('s2_interim.usaspending_prime_awards_enriched')
    vectorize_table('s2_interim.usaspending_subawards_enriched')
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
