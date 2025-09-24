# GitHub MCP Server (Stub)

Read-only Model Context Protocol server exposing limited GitHub repository inspection tools.

## Tools

- `list_repo_files` — List files/directories at a path (optionally recursive in future enhancement)
- `get_file` — Get file metadata + base64-decoded preview (first 2KB)
- `search_code` — Code search within an allow‑listed repo
- `list_pull_requests` — List pull requests by state
- `usage` (prompt) — Help/summary of available tools

## Environment Variables

| Variable               | Required | Description                                                    |
| ---------------------- | -------- | -------------------------------------------------------------- |
| `GITHUB_TOKEN`         | Yes      | Fine-scoped PAT (repo:read for private, or public access only) |
| `GITHUB_ALLOWED_REPOS` | Yes      | Comma-separated `owner/repo` allowlist (no access if empty)    |
| `GITHUB_API_URL`       | No       | Override GitHub API base (default `https://api.github.com`)    |

## Security Controls

- Explicit allowlist prevents lateral exploration outside intended repos.
- Read-only tools only (no mutations / write endpoints implemented).
- Response truncation & max_items / max_results guard against large payloads.
- Early return with error when token missing or repo not allowed.
- Headers include API version pin for predictable responses.

## Future Hardening Ideas

- Add per-tool request timeouts + circuit breaker wrapper.
- Implement rate limit tracking (X-RateLimit headers) and backoff.
- Add `recursive` directory traversal with depth + total node guards.
- Cache file metadata ETag/sha for short-lived sessions.
- Redact or hash sensitive file fragments (config, secrets) via pattern rules.

## Integration Steps

1. Populate `.env` with `GITHUB_TOKEN` and `GITHUB_ALLOWED_REPOS="org/project"`.
2. Add discovery entry in `mcp_client_manager.py` (if not using dynamic folder scan).
3. Expose in agent tool registry / selection UI.
4. Write integration test hitting `list_repo_files` on a small test repo.

## Testing Locally

```
set GITHUB_TOKEN=ghp_your_pat_here
set GITHUB_ALLOWED_REPOS=youruser/yourrepo
python -m src.backend.ai.mcp_servers.github.server
```

(Then connect via MCP client if using stdio transport.)

## Limitations

- No pagination handling yet (first page only for search & pulls).
- No GraphQL API usage (REST only to keep surface minimal initially).
- Does not attempt recursive listing; implement carefully with size guards.

## Removal / Deactivation

Unset `GITHUB_ALLOWED_REPOS` or remove server from discovery for immediate disablement without code deletion.
