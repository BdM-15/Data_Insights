# Langfuse Local Setup Instructions

This guide will help you run Langfuse locally as part of the Data_Insights repository for LLM and agent observability.

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM (16GB+ recommended for full stack)

## Steps

1. **Configure environment variables:**

   - All environment variables for Langfuse and Data_Insights are managed in the root `.env` and `.env.example` files.
   - Ensure the following Langfuse variables are present in your root `.env` and `.env.example`:
     - `DATABASE_URL`, `CLICKHOUSE_URL`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_MIGRATION_URL`, `REDIS_HOST`, `REDIS_PORT`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL`, `LANGFUSE_HOST`, `SALT`, `S3_ENDPOINT`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_DEBUG`
   - See `.env.example` for sample values and documentation.

2. **Start Langfuse stack:**
   Open a terminal in the `langfuse` directory and run:

   ```cmd
   docker-compose up -d
   ```

   This will start all required services (Langfuse web, worker, Postgres, Clickhouse, Redis, Minio).

3. **Access the Langfuse UI:**
   Open your browser to [http://localhost:3000](http://localhost:3000)

4. **First-time setup:**

   - Register an admin user in the UI.
   - Create a project and API key for your Data_Insights integration.

5. **Persistence:**

   - All data is stored in Docker volumes under the `langfuse` directory.
   - All environment variables are managed in the root `.env` and `.env.example` files for consistency across the project.

6. **Stopping Langfuse:**
   ```cmd
   docker-compose down
   ```

## Troubleshooting

- If you have issues, check logs with:
  ```cmd
  docker-compose logs
  ```
- Make sure ports 3000, 5433, 9000, 9001, 6379, and 8123 are not in use by other services.

## Security Note

- This setup is for local development only. Do not expose these services to the public internet without proper security hardening.

## Integration Note

- All environment variables for Langfuse are consolidated in the root `.env` and `.env.example` files. Do not create or use separate `.env` files in the `langfuse` directory.

---

---

For more details, see the official Langfuse self-hosting documentation: https://langfuse.com/self-hosting
