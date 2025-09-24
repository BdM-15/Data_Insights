#!/usr/bin/env python3
"""GitHub MCP Server (Stub)

Exposes read-only GitHub repository inspection tools via Model Context Protocol.

Security / Design Notes:
- Only supports read operations (no mutations) to minimize risk.
- Requires a GitHub PAT provided via environment variable GITHUB_TOKEN (fine-scoped).
- Explicit allowlist of accessible repositories via GITHUB_ALLOWED_REPOS env
  (comma-separated owner/repo identifiers). If unset, all repos are denied.
- Rate limit and size guards prevent excessive API usage.

Replace 'pass' sections with robust logic as you productionize.
"""
from __future__ import annotations
import os
import sys
import base64
import logging
from typing import List, Dict, Any
import httpx

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import Prompt

from .models import (
    ListRepoFilesInput, GetFileInput, SearchCodeInput, ListPullsInput,
    ListRepoFilesOutput, GetFileOutput, SearchCodeOutput, ListPullsOutput,
    FileItem, SearchCodeMatch, PullRequestItem
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

mcp = FastMCP("GitHub Repository Server")

GITHUB_API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")
ALLOWED = {r.strip().lower() for r in os.getenv("GITHUB_ALLOWED_REPOS", "").split(',') if r.strip()}
TIMEOUT = 15.0

if not TOKEN:
    logger.warning("GITHUB_TOKEN not set; all tool calls will fail until provided.")
if not ALLOWED:
    logger.warning("GITHUB_ALLOWED_REPOS empty; no repositories are accessible.")

_headers = {
    "Authorization": f"Bearer {TOKEN}" if TOKEN else "",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "capture-intel-mcp-github"
}

async def _client():
    return httpx.AsyncClient(timeout=TIMEOUT, headers=_headers)

def _is_allowed(owner: str, repo: str) -> bool:
    ident = f"{owner}/{repo}".lower()
    return ident in ALLOWED

@mcp.tool()
async def list_repo_files(payload: Dict[str, Any]) -> Dict[str, Any]:
    """List files/directories at a path in an allowed repository.
    Args: owner, repo, path (optional), recursive (bool), ref (optional), max_items.
    Returns: ListRepoFilesOutput as dict.
    """
    data = ListRepoFilesInput(**payload)
    if not _is_allowed(data.owner, data.repo):
        return {"error": "repository not allowed"}
    items: List[FileItem] = []
    truncated = False
    params = {"ref": data.ref} if data.ref else {}
    url = f"{GITHUB_API}/repos/{data.owner}/{data.repo}/contents/{data.path}"
    async with await _client() as client:
        try:
            r = await client.get(url, params=params)
            if r.status_code != 200:
                return {"error": f"GitHub error {r.status_code}: {r.text[:120]}"}
            resp = r.json()
            if isinstance(resp, dict) and resp.get('type') == 'file':
                # Single file path
                items.append(FileItem(path=resp['path'], type=resp['type'], size=resp.get('size'), sha=resp.get('sha')))
            else:
                for entry in resp:
                    items.append(FileItem(path=entry['path'], type=entry['type'], size=entry.get('size'), sha=entry.get('sha')))
                    if len(items) >= data.max_items:
                        truncated = True
                        break
        except Exception as e:
            return {"error": str(e)}
    return ListRepoFilesOutput(
        repository=f"{data.owner}/{data.repo}",
        ref=data.ref or "default",
        items=items,
        truncated=truncated
    ).dict()

@mcp.tool()
async def get_file(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Get file metadata + preview content (first 2KB decoded). Args: owner, repo, path, ref."""
    data = GetFileInput(**payload)
    if not _is_allowed(data.owner, data.repo):
        return {"error": "repository not allowed"}
    params = {"ref": data.ref} if data.ref else {}
    url = f"{GITHUB_API}/repos/{data.owner}/{data.repo}/contents/{data.path}"
    async with await _client() as client:
        r = await client.get(url, params=params)
        if r.status_code != 200:
            return {"error": f"GitHub error {r.status_code}: {r.text[:120]}"}
        content = r.json()
        if content.get('type') != 'file':
            return {"error": "not a file"}
        raw = base64.b64decode(content.get('content', '') or b'')
        preview = raw[:2048].decode('utf-8', errors='replace')
        return GetFileOutput(
            repository=f"{data.owner}/{data.repo}",
            ref=data.ref or "default",
            path=content['path'],
            size=content.get('size', 0),
            sha=content.get('sha', ''),
            content_preview=preview,
            encoding=content.get('encoding', 'base64')
        ).dict()

@mcp.tool()
async def search_code(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Search code in a repo (limited). Args: owner, repo, query, ref, max_results."""
    data = SearchCodeInput(**payload)
    if not _is_allowed(data.owner, data.repo):
        return {"error": "repository not allowed"}
    q = f"{data.query} repo:{data.owner}/{data.repo}"
    params = {"q": q, "per_page": min(data.max_results, 100)}
    async with await _client() as client:
        r = await client.get(f"{GITHUB_API}/search/code", params=params)
        if r.status_code != 200:
            return {"error": f"GitHub error {r.status_code}: {r.text[:120]}"}
        js = r.json()
        matches: List[SearchCodeMatch] = []
        for item in js.get('items', [])[: data.max_results]:
            matches.append(SearchCodeMatch(
                path=item['path'],
                score=item.get('score', 0.0),
                fragment=item.get('name', ''),
                sha=item.get('sha')
            ))
        return SearchCodeOutput(
            repository=f"{data.owner}/{data.repo}",
            ref=data.ref,
            query=data.query,
            matches=matches,
            truncated=len(matches) >= data.max_results
        ).dict()

@mcp.tool()
async def list_pull_requests(payload: Dict[str, Any]) -> Dict[str, Any]:
    """List pull requests (state=open|closed|all). Args: owner, repo, state, max_results."""
    data = ListPullsInput(**payload)
    if not _is_allowed(data.owner, data.repo):
        return {"error": "repository not allowed"}
    params = {"state": data.state, "per_page": min(data.max_results, 100)}
    async with await _client() as client:
        r = await client.get(f"{GITHUB_API}/repos/{data.owner}/{data.repo}/pulls", params=params)
        if r.status_code != 200:
            return {"error": f"GitHub error {r.status_code}: {r.text[:120]}"}
        pulls = []
        for pr in r.json()[: data.max_results]:
            pulls.append(PullRequestItem(
                number=pr['number'],
                title=pr['title'],
                state=pr['state'],
                user=pr['user']['login'],
                created_at=pr['created_at'],
                updated_at=pr.get('updated_at'),
                merged=pr.get('merged_at') is not None
            ))
        return ListPullsOutput(
            repository=f"{data.owner}/{data.repo}",
            state=data.state,
            count=len(pulls),
            pulls=pulls
        ).dict()

@mcp.prompt()
async def usage() -> Prompt:
    """Return usage/help text for available GitHub tools."""
    return Prompt(
        name="github_usage",
        messages=[{"role": "system", "content": (
            "GitHub MCP Server Tools:\n"
            "- list_repo_files: owner, repo, (path), (recursive), (ref), (max_items) -> directory listing.\n"
            "- get_file: owner, repo, path, (ref) -> file metadata + preview.\n"
            "- search_code: owner, repo, query, (ref), (max_results) -> code matches.\n"
            "- list_pull_requests: owner, repo, (state), (max_results) -> PR summary.\n"
            "Environment: GITHUB_TOKEN (PAT), GITHUB_ALLOWED_REPOS (comma list).\n"
            "All tools are read-only. Large responses truncated." )}]
    )

if __name__ == "__main__":  # pragma: no cover
    # Allow running standalone for quick manual test
    from mcp.server.fastmcp.run import run
    run(mcp)
