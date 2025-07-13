"""
embedding_generation.py

Migration and embedding generation script for semantic/vector search enablement in Data_Insights.

Instructions:
- Run this script after deduplication and transformation, before final load into production tables.
- This script will:
    1. Add an 'embedding' column to each target table (see TABLES below) if it does not exist.
    2. For each record, concatenate the following fields (as available):
        - prime_award_base_transaction_description
        - transaction_description
        - naics_code
        - naics_description
        - product_or_service_code
        - product_or_service_code_description
        - subaward_description
    3. Generate embeddings for each record using your local embedding model (Ollama or similar).
    4. Store the embeddings in the new column.
- Index creation is handled in embedding_indexing.py for separation of concerns.
- Requires: pgvector extension installed in PostgreSQL.

TODO (future enhancements):
- Webscrape NAICS and PSC definitions and append to the text for embedding.
- Webscrape KBR social media and public websites for richer context (MCP tool).
- Fetch and parse inactive solicitation documents (RFP, PWS, SOWs) from sam.gov and include relevant text in embeddings.
- Document download and parsing for richer contract context.

To enable pgvector:
    CREATE EXTENSION IF NOT EXISTS vector;

To add embedding column (example for 768-dim vectors):
    ALTER TABLE s3_processed.usaspending_prime_awards ADD COLUMN IF NOT EXISTS embedding vector(768);

Update ETL:
- After deduplication and transformation, run this script to generate and store embeddings.
- Use your local LLM/embedding model to generate a vector for each record's relevant text fields.
- Store the vector in the 'embedding' column.

"""

import os
import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm
# from your_embedding_module import get_embedding  # Implement this using Ollama or your local model

DB_CONN = os.getenv("PG_CONN_STRING", "host=localhost dbname=capture_insights user=postgres password=postgres")
EMBEDDING_DIM = 768  # Change to match your model
BATCH_SIZE = 100

# List of tables and their relevant columns for embedding
TABLES = [
    {
        "name": "s3_processed.usaspending_prime_awards",
        "id_col": "contract_transaction_unique_key",
        "text_cols": [
            "prime_award_base_transaction_description",
            "transaction_description",
            "naics_code",
            "naics_description",
            "product_or_service_code",
            "product_or_service_code_description"
        ]
    },
    {
        "name": "s3_processed.usaspending_prime_awards_kbr",
        "id_col": "contract_transaction_unique_key",
        "text_cols": [
            "prime_award_base_transaction_description",
            "transaction_description",
            "naics_code",
            "naics_description",
            "product_or_service_code",
            "product_or_service_code_description"
        ]
    },
    {
        "name": "s3_processed.usaspending_subawards",
        "id_col": "id",
        "text_cols": [
            "subaward_description",
            "naics_code",
            "naics_description",
            "product_or_service_code",
            "product_or_service_code_description"
        ]
    },
    {
        "name": "s3_processed.usaspending_subawards_kbr",
        "id_col": "id",
        "text_cols": [
            "subaward_description",
            "naics_code",
            "naics_description",
            "product_or_service_code",
            "product_or_service_code_description"
        ]
    },
    {
        "name": "s3_processed.usaspending_subawards_kbr_issued",
        "id_col": "id",
        "text_cols": [
            "subaward_description",
            "naics_code",
            "naics_description",
            "product_or_service_code",
            "product_or_service_code_description"
        ]
    }
]

# --- STEP 1: Ensure embedding column exists ---
def ensure_embedding_column(conn, table):
    schema, tbl = table["name"].split(".")
    with conn.cursor() as cur:
        cur.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = '{schema}' AND table_name = '{tbl}' AND column_name = 'embedding'
                ) THEN
                    ALTER TABLE {table['name']} ADD COLUMN embedding vector({EMBEDDING_DIM});
                END IF;
            END$$;
        """)
        conn.commit()

# --- STEP 2: Generate and store embeddings ---
def generate_and_store_embeddings(conn, table):
    id_col = table["id_col"]
    text_cols = table["text_cols"]
    with conn.cursor() as cur:
        cur.execute(f"SELECT {id_col}, {', '.join(text_cols)} FROM {table['name']} WHERE embedding IS NULL LIMIT 100000")
        rows = cur.fetchall()
    print(f"Generating embeddings for {len(rows)} records in {table['name']}...")
    updates = []
    for row in tqdm(rows):
        key = row[0]
        text = " ".join([str(val) for val in row[1:] if val])
        # TODO: In the future, append webscraped NAICS/PSC definitions and document text here
        # embedding = get_embedding(text)  # Implement this function using your local model
        embedding = [0.0] * EMBEDDING_DIM  # Placeholder: replace with real embedding
        updates.append((embedding, key))
    with conn.cursor() as cur:
        execute_batch(cur, f"UPDATE {table['name']} SET embedding = %s WHERE {id_col} = %s", updates)
        conn.commit()
    print(f"Embeddings updated for {table['name'].split('.')[-1]}.")

if __name__ == "__main__":
    conn = psycopg2.connect(DB_CONN)
    for table in TABLES:
        ensure_embedding_column(conn, table)
        generate_and_store_embeddings(conn, table)
    conn.close()
    print("Embedding generation complete for all tables.")
