"""
Application version information.
"""
from get_git_info import get_git_info

VERSION = "2.0.0"
VERSION_NAME = "Intelligent RAG"
RELEASE_DATE = "2025-01-13"

# Get git info for debugging
GIT_INFO = get_git_info()
GIT_COMMIT = GIT_INFO['commit_short']
GIT_BRANCH = GIT_INFO['branch']

# Version history:
# 2.0.0 "Intelligent RAG" - Advanced query analysis, metadata filtering, reranking
# 1.0.0 "Foundation" - Basic RAG implementation
