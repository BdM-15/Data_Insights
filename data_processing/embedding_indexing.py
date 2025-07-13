"""
embedding_indexing.py

Script to create vector (pgvector) indexes for semantic search in Data_Insights.

Instructions:
- Run this script after running embedding_generation.py and after all embeddings have been generated and stored.
- This script will:
    1. Create a vector index on the 'embedding' column of each target table (see TABLES below).
- Requires: pgvector extension and embedding columns already present and populated.

Example index creation (for 768-dim vectors):
    CREATE INDEX IF NOT EXISTS idx_<table>_embedding
    ON <table> USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

You may adjust the index type and parameters for your workload.
"""

import os
import psycopg2

DB_CONN = os.getenv("PG_CONN_STRING", "host=localhost dbname=capture_insights user=postgres password=postgres")

TABLES = [
    "s3_processed.usaspending_prime_awards",
    "s3_processed.usaspending_prime_awards_kbr",
    "s3_processed.usaspending_subawards",
    "s3_processed.usaspending_subawards_kbr",
    "s3_processed.usaspending_subawards_kbr_issued"
]

# --- STEP 1: Create vector index for each table ---
def create_vector_index(conn, table):
    idx_name = f"idx_{table.replace('.', '_')}_embedding"
    with conn.cursor() as cur:
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS {idx_name}
            ON {table} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        """)
        conn.commit()
    print(f"Vector index created on {table} (embedding column).")

if __name__ == "__main__":
    conn = psycopg2.connect(DB_CONN)
    for table in TABLES:
        create_vector_index(conn, table)
    conn.close()
    print("Indexing complete for all tables.")
