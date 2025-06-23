
import requests
import json
from typing import Optional, Dict, Any
from packaging.version import parse as parse_version

# Assuming constants.py will have this. If not, define it here.
try:
    from core.constants import UPDATE_URL
except ImportError:
    # Fallback or error. For this implementation, let's use a fallback.
    # This makes the module more self-contained if constants change.
    UPDATE_URL = "https://api.github.com/repos/Chickaboo/UpdaterTest/releases/latest"


class Updater:
    """Handles checking for application updates from GitHub Releases."""

    def __init__(self, current_version: str):
        """
        Initializes the updater.
        :param current_version: The current version of the application (e.g., "0.4.0").
        """
        self.current_version = current_version
        self.latest_version_info: Optional[Dict[str, Any]] = None

    def check_for_updates(self) -> bool:
        """
        Checks for updates by fetching the latest release from GitHub.
        Returns True if a newer version is available, False otherwise.
        """
        try:
            # Use a timeout to prevent the app from hanging indefinitely
            response = requests.get(UPDATE_URL, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            self.latest_version_info = response.json()

            # GitHub tags are often prefixed with 'v', e.g., 'v1.2.3'
            latest_version_str = self.latest_version_info.get("tag_name", "0.0.0").lstrip('v')

            # Use the packaging library for robust version comparison (handles cases like 1.0.0-beta vs 1.0.0)
            return parse_version(latest_version_str) > parse_version(self.current_version)

        except requests.RequestException as e:
            # Handle connection errors, timeouts, etc.
            print(f"Update check failed: Network error - {e}")
            self.latest_version_info = None
            return False
        except json.JSONDecodeError as e:
            # Handle cases where the response is not valid JSON
            print(f"Update check failed: Could not parse response - {e}")
            self.latest_version_info = None
            return False
        except Exception as e:
            # Catch any other unexpected errors
            print(f"An unexpected error occurred during update check: {e}")
            self.latest_version_info = None
            return False

    def get_latest_version(self) -> Optional[str]:
        """Returns the tag name of the latest version, e.g., '0.5.0'."""
        if self.latest_version_info:
            return self.latest_version_info.get("tag_name", "N/A").lstrip('v')
        return None

    def get_release_notes(self) -> Optional[str]:
        """Returns the body/description of the latest release."""
        if self.latest_version_info:
            return self.latest_version_info.get("body", "No description available.")
        return None

    def get_download_url(self) -> Optional[str]:
        """
        Returns the download URL for the first asset of the latest release.
        Assumes the primary release asset (e.g., .msi, .exe, .zip) is the first one listed.
        """
        if self.latest_version_info and "assets" in self.latest_version_info and self.latest_version_info["assets"]:
            return self.latest_version_info["assets"][0].get("browser_download_url")
        return None
