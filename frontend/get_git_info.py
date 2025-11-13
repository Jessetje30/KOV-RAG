#!/usr/bin/env python3
"""
Extract git information for version tracking.
"""
import subprocess
import os


def get_git_info():
    """
    Get git commit hash and branch name.

    Returns:
        dict with 'commit_hash', 'commit_short', 'branch', 'commit_message'
    """
    try:
        # Get current directory (frontend) and go up to repo root
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Get commit hash (full)
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_dir,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # Get short commit hash
        commit_short = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=repo_dir,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # Get branch name
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=repo_dir,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()

        # Get commit message (first line)
        commit_message = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=%B'],
            cwd=repo_dir,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip().split('\n')[0][:60]  # First 60 chars

        return {
            'commit_hash': commit_hash,
            'commit_short': commit_short,
            'branch': branch,
            'commit_message': commit_message
        }
    except Exception as e:
        # Fallback if git not available or not a git repo
        return {
            'commit_hash': 'unknown',
            'commit_short': 'unknown',
            'branch': 'unknown',
            'commit_message': 'Git info not available'
        }
