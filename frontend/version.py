"""
Frontend application version information.
Synced with backend version.
"""
from get_git_info import get_git_info

VERSION = "2.0.0"
VERSION_NAME = "Intelligent RAG"
RELEASE_DATE = "2025-01-13"

# Get git info for debugging
GIT_INFO = get_git_info()
GIT_COMMIT = GIT_INFO['commit_short']
GIT_BRANCH = GIT_INFO['branch']
GIT_MESSAGE = GIT_INFO['commit_message']
