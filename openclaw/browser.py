"""
Browser and path opening utilities.
Opens files, folders, or URLs using the system's default handler.
"""

import os
import subprocess
import sys
from typing import Optional


def _validate_url(url: str) -> None:
    """Validate URL format and protocol."""
    try:
        from urllib.parse import urlparse
    except ImportError:
        from urlparse import urlparse

    parsed = urlparse(url)

    # Validate protocol
    if parsed.scheme not in ('http', 'https'):
        raise ValueError(
            f"Invalid URL protocol: must use http:// or https://, got {parsed.scheme}"
        )


def open_path(path: str) -> bool:
    """
    Open a file or folder path using the system's default handler.

    Uses:
    - macOS: open
    - Windows: explorer
    - Linux: xdg-open

    Args:
        path: File or folder path to open

    Returns:
        True if successful, False otherwise
    """
    try:
        platform = sys.platform

        if platform == 'win32':
            cmd = ['explorer', path]
        elif platform == 'darwin':
            cmd = ['open', path]
        else:
            cmd = ['xdg-open', path]

        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def open_browser(url: str, browser_env: Optional[str] = None) -> bool:
    """
    Open a URL in the system's default browser or a specified browser.

    Args:
        url: URL to open (must be http or https)
        browser_env: Optional browser command from environment (BROWSER env var)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Parse and validate the URL
        _validate_url(url)

        platform = sys.platform

        if platform == 'win32':
            if browser_env:
                # Browsers require shell=True on Windows
                cmd = [browser_env, f'"{url}"']
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    timeout=10
                )
                return result.returncode == 0
            else:
                cmd = ['rundll32', 'url,OpenURL', url]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=10
                )
                return result.returncode == 0
        else:
            # macOS / Linux
            if browser_env:
                cmd = [browser_env, url]
            elif platform == 'darwin':
                cmd = ['open', url]
            else:
                cmd = ['xdg-open', url]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
    except Exception:
        return False
