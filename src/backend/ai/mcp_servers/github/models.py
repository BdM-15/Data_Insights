"""Pydantic models for GitHub MCP server tool inputs/outputs.

These models provide validation and structured responses for the MCP tools
exposed by the GitHub server stub.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

# Input Models
class RepoRef(BaseModel):
    owner: str = Field(..., description="GitHub organization or user")
    repo: str = Field(..., description="Repository name")
    ref: Optional[str] = Field(None, description="Branch, tag, or commit SHA")

class ListRepoFilesInput(RepoRef):
    path: str = Field("", description="Directory path within repo (blank = root)")
    recursive: bool = Field(False, description="If true, list all descendants")
    max_items: int = Field(200, ge=1, le=5000, description="Limit results for safety")

class GetFileInput(RepoRef):
    path: str = Field(..., description="File path to retrieve")

class SearchCodeInput(RepoRef):
    query: str = Field(..., min_length=2, description="Search keywords / qualifiers")
    max_results: int = Field(50, ge=1, le=200, description="Limit results")

class ListPullsInput(RepoRef):
    state: str = Field("open", regex="^(open|closed|all)$", description="PR state filter")
    max_results: int = Field(30, ge=1, le=100, description="Max PRs to return")

# Output Models
class FileItem(BaseModel):
    path: str
    type: str
    size: Optional[int] = None
    sha: Optional[str] = None

class ListRepoFilesOutput(BaseModel):
    repository: str
    ref: str
    items: List[FileItem]
    truncated: bool = False

class GetFileOutput(BaseModel):
    repository: str
    ref: str
    path: str
    size: int
    sha: str
    content_preview: str = Field(..., description="First N chars (not full if large)")
    encoding: str

class SearchCodeMatch(BaseModel):
    path: str
    score: float
    fragment: str
    sha: Optional[str] = None

class SearchCodeOutput(BaseModel):
    repository: str
    ref: Optional[str]
    query: str
    matches: List[SearchCodeMatch]
    truncated: bool = False

class PullRequestItem(BaseModel):
    number: int
    title: str
    state: str
    user: str
    created_at: str
    updated_at: Optional[str] = None
    merged: Optional[bool] = None

class ListPullsOutput(BaseModel):
    repository: str
    state: str
    count: int
    pulls: List[PullRequestItem]

__all__ = [
    "ListRepoFilesInput","GetFileInput","SearchCodeInput","ListPullsInput",
    "ListRepoFilesOutput","GetFileOutput","SearchCodeOutput","ListPullsOutput"
]
