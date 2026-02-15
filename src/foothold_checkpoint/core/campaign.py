"""Campaign detection using explicit file lists from configuration."""

import re
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foothold_checkpoint.core.config import Config


# Pattern to detect foothold-like files (used for unknown file detection)
# More permissive than old pattern - catches anything that looks like a foothold file
_FOOTHOLD_LIKE_PATTERN = re.compile(
    r"^[Ff][Oo][Oo][Tt][Hh][Oo][Ll][Dd]",  # Starts with 'foothold' (any case)
    re.IGNORECASE,
)


def is_shared_file(filename: str | Path) -> bool:
    """Check if a filename is the shared Foothold_Ranks.lua file.

    Foothold_Ranks.lua is a special file that is shared across all campaigns
    and should not be grouped with any specific campaign.

    Args:
        filename: The filename to check (string or Path object).
                 Can be just a filename or a full path.

    Returns:
        bool: True if the file is Foothold_Ranks.lua (case-insensitive), False otherwise.

    Examples:
        >>> is_shared_file("Foothold_Ranks.lua")
        True
        >>> is_shared_file("foothold_ranks.lua")
        True
        >>> is_shared_file("foothold_afghanistan.lua")
        False
    """
    # Extract filename if a Path object or full path string is provided
    filename_str = filename.name if isinstance(filename, Path) else Path(filename).name

    # Check if it matches Foothold_Ranks.lua (case-insensitive)
    return filename_str.lower() == "foothold_ranks.lua"


def build_file_to_campaign_map(config: "Config") -> dict[str, str]:
    """Build a reverse lookup map from file names to campaign IDs.

    Creates a dictionary mapping each configured file name to its campaign ID.
    This allows quick lookup of which campaign a file belongs to.

    Args:
        config: Configuration object containing campaign definitions.

    Returns:
        dict: Dictionary mapping file names to campaign IDs.
              Example: {"FootHold_CA_v0.2.lua": "ca", "foothold_afghanistan.lua": "afghanistan"}

    Examples:
        >>> # With config containing afghanistan and ca campaigns
        >>> file_map = build_file_to_campaign_map(config)
        >>> file_map["foothold_afghanistan.lua"]
        'afghanistan'
        >>> file_map["FootHold_CA_v0.2.lua"]
        'ca'
    """
    file_to_campaign: dict[str, str] = {}

    for campaign_id, campaign_config in config.campaigns.items():
        # Iterate through all file types in the campaign
        for file_type_name in ["persistence", "ctld_save", "ctld_farps", "storage"]:
            file_type = getattr(campaign_config.files, file_type_name)
            # Add all files from this type to the map
            for filename in file_type.files:
                file_to_campaign[filename] = campaign_id

    return file_to_campaign


def group_campaign_files(filenames: Sequence[str | Path], config: "Config") -> dict[str, list[str]]:
    """Group campaign files by campaign ID using configuration.

    Takes a list of filenames and groups them by campaign based on explicit
    file lists in the configuration. Files not in configuration are ignored.

    Args:
        filenames: List of filenames (strings or Path objects) to group.
                  Can include non-campaign files which will be filtered out.
        config: Configuration object containing campaign definitions.

    Returns:
        dict: Dictionary mapping campaign IDs to lists of original filenames.
              Returns empty dict if no configured campaign files are found.

    Examples:
        >>> # With config defining afghanistan and ca campaigns
        >>> group_campaign_files([
        ...     "foothold_afghanistan.lua",
        ...     "foothold_afghanistan_storage.csv",
        ...     "FootHold_CA_v0.2.lua"
        ... ], config)
        {
            'afghanistan': ['foothold_afghanistan.lua', 'foothold_afghanistan_storage.csv'],
            'ca': ['FootHold_CA_v0.2.lua']
        }
    """
    # Build reverse lookup map
    file_to_campaign = build_file_to_campaign_map(config)

    # Group files by campaign
    groups: dict[str, list[str]] = defaultdict(list)

    for filename in filenames:
        # Skip shared files (Foothold_Ranks.lua)
        if is_shared_file(filename):
            continue

        # Extract just the filename (not full path)
        filename_str = filename.name if isinstance(filename, Path) else Path(filename).name

        # Look up which campaign this file belongs to
        if filename_str in file_to_campaign:
            campaign_id = file_to_campaign[filename_str]
            groups[campaign_id].append(filename_str)

    # Convert defaultdict back to regular dict
    return dict(groups)


def detect_unknown_files(filenames: Sequence[str | Path], config: "Config") -> list[str]:
    """Detect files that look like foothold campaign files but aren't configured.

    Identifies files that start with "foothold" but are not listed in any
    campaign configuration. These might be new campaign files that need to be
    added to the configuration.

    Args:
        filenames: List of filenames to analyze (strings or Path objects).
        config: Configuration object containing campaign definitions.

    Returns:
        list: List of file names that appear to be foothold files but aren't configured.
              Returns empty list if all foothold-like files are configured.

    Examples:
        >>> # With config not containing "newmap" campaign
        >>> detect_unknown_files([
        ...     "foothold_newmap.lua",
        ...     "foothold_afghanistan.lua",  # This one IS configured
        ...     "README.txt"  # Not a foothold file
        ... ], config)
        ['foothold_newmap.lua']
    """
    # Build set of all known file names
    file_to_campaign = build_file_to_campaign_map(config)
    known_files = set(file_to_campaign.keys())

    # Also include shared files as known
    known_files.add("Foothold_Ranks.lua")
    known_files.add("foothold_ranks.lua")  # case variation
    # Add foothold.status as known non-campaign file
    known_files.add("foothold.status")

    unknown: list[str] = []

    for filename in filenames:
        # Extract just the filename (not full path)
        filename_str = filename.name if isinstance(filename, Path) else Path(filename).name

        # Skip hidden files
        if filename_str.startswith("."):
            continue

        # Check if it looks like a foothold file but isn't configured
        if _FOOTHOLD_LIKE_PATTERN.match(filename_str) and filename_str not in known_files:
            unknown.append(filename_str)

    return unknown


def detect_campaigns(filenames: Sequence[str | Path], config: "Config") -> dict[str, list[str]]:
    """Detect and group campaign files using configuration.

    Groups files by campaign based on explicit file lists in configuration.
    This is the main entry point for campaign detection.

    Args:
        filenames: List of filenames to detect and group.
        config: Configuration object containing campaign definitions.

    Returns:
        dict: Dictionary mapping campaign IDs to lists of filenames.

    Examples:
        >>> files = ["FootHold_CA_v0.2.lua", "foothold_afghanistan.lua"]
        >>> detect_campaigns(files, config)
        {
            'ca': ['FootHold_CA_v0.2.lua'],
            'afghanistan': ['foothold_afghanistan.lua']
        }
    """
    return group_campaign_files(filenames, config)


def create_campaign_report(filenames: Sequence[str | Path], config: "Config") -> dict[str, int]:
    """Create a campaign detection report with file counts.

    Analyzes a list of filenames and generates a summary report showing
    how many files belong to each detected campaign.

    Args:
        filenames: List of filenames to analyze (strings or Path objects).
                  Can include campaign files, shared files, and other files.
        config: Configuration object containing campaign definitions.

    Returns:
        dict: Dictionary mapping campaign IDs to file counts.
              Only includes campaigns with at least one file.
              Empty dict if no campaign files are found.

    Examples:
        >>> files = ["FootHold_CA_v0.2.lua", "foothold_afghanistan.lua"]
        >>> create_campaign_report(files, config)
        {
            'ca': 1,
            'afghanistan': 1
        }

        >>> # With multiple files per campaign
        >>> files = [
        ...     "foothold_afghanistan.lua",
        ...     "foothold_afghanistan_storage.csv",
        ...     "Foothold_Ranks.lua"  # Excluded (shared file)
        ... ]
        >>> create_campaign_report(files, config)
        {'afghanistan': 2}
    """
    # Detect and group campaigns
    campaigns = detect_campaigns(filenames, config)

    # Convert to file count report
    return {name: len(files) for name, files in campaigns.items()}


def generate_config_suggestion(unknown_files: list[str]) -> str:
    """Generate a YAML config snippet suggestion for unknown files.

    Creates an example configuration snippet showing how to add the unknown
    files to config.yaml. Attempts to guess the campaign name from the
    first unknown file.

    Args:
        unknown_files: List of unknown file names to create config for.

    Returns:
        str: YAML configuration snippet as a string.

    Examples:
        >>> generate_config_suggestion(["foothold_newmap_v1.0.lua"])
        '''
          newmap:
            display_name: "New Map"
            files:
              persistence:
                - "foothold_newmap_v1.0.lua"
              ctld_save:
                - "foothold_newmap_CTLD_Save.csv"
              ctld_farps:
                - "foothold_newmap_CTLD_FARPS.csv"
              storage:
                optional: true
        '''
    """
    if not unknown_files:
        return ""

    # Try to extract a campaign name from the first file
    # Remove foothold prefix, version, and file type suffixes
    first_file = unknown_files[0]
    name_without_ext = first_file.rsplit(".", 1)[0]

    # Remove foothold prefix (case-insensitive)
    campaign_guess = re.sub(r"^foothold_?", "", name_without_ext, flags=re.IGNORECASE)

    # Remove version and file type suffixes
    campaign_guess = re.sub(r"_[vV]?[0-9]+(?:\.[0-9]+)?", "", campaign_guess)
    campaign_guess = re.sub(
        r"_(storage|CTLD_FARPS|CTLD_Save)", "", campaign_guess, flags=re.IGNORECASE
    )

    # Convert to lowercase for campaign ID
    campaign_id = campaign_guess.lower().replace(" ", "_")

    # Create display name (capitalize first letter of each word)
    display_name = " ".join(word.capitalize() for word in campaign_id.split("_"))

    # Build the YAML snippet
    snippet = f"""  {campaign_id}:
    display_name: "{display_name}"
    files:
      persistence:"""

    # Add the persistence files (usually .lua)
    persistence_files = [f for f in unknown_files if f.endswith(".lua")]
    if persistence_files:
        for f in persistence_files:
            snippet += f'\n        - "{f}"'
    else:
        # Guess the persistence file name
        snippet += f'\n        - "foothold_{campaign_id}.lua"'

    # Add other file types
    snippet += "\n      ctld_save:"
    ctld_save_files = [f for f in unknown_files if "CTLD_Save" in f or "ctld_save" in f.lower()]
    if ctld_save_files:
        for f in ctld_save_files:
            snippet += f'\n        - "{f}"'
    else:
        snippet += f'\n        - "foothold_{campaign_id}_CTLD_Save.csv"'

    snippet += "\n      ctld_farps:"
    ctld_farps_files = [f for f in unknown_files if "CTLD_FARPS" in f or "ctld_farps" in f.lower()]
    if ctld_farps_files:
        for f in ctld_farps_files:
            snippet += f'\n        - "{f}"'
    else:
        snippet += f'\n        - "foothold_{campaign_id}_CTLD_FARPS.csv"'

    snippet += "\n      storage:\n        optional: true"

    return snippet


def format_unknown_files_error(unknown_files: list[str], _config: "Config") -> str:
    """Format a helpful error message for unknown campaign files.

    Creates a detailed error message that lists the unknown files and
    provides guidance on how to add them to the configuration.

    Args:
        unknown_files: List of unknown file names detected.
        _config: Configuration object (reserved for future context-aware messages).

    Returns:
        str: Formatted error message with instructions.

    Examples:
        >>> error = format_unknown_files_error(["foothold_newmap.lua"], config)
        >>> print(error)
        Unknown campaign files detected in source directory:
          - foothold_newmap.lua

        These files appear to be Foothold campaign files but are not configured.

        To import this campaign, add it to your config.yaml under 'campaigns':

          newmap:
            display_name: "New Map"
            files:
              persistence:
                - "foothold_newmap.lua"
              ...
    """
    # Build the error message
    msg = "Unknown campaign files detected in source directory:\n"

    for filename in unknown_files:
        msg += f"  - {filename}\n"

    msg += "\n"
    msg += "These files appear to be Foothold campaign files but are not configured.\n"
    msg += "\n"

    if len(unknown_files) == 1:
        msg += "To import this campaign, add it to your config.yaml under 'campaigns':\n"
    else:
        msg += "To import these campaigns, add them to your config.yaml under 'campaigns':\n"

    msg += "\n"

    # Add the config suggestion
    suggestion = generate_config_suggestion(unknown_files)
    msg += suggestion

    msg += "\n"
    msg += "\nFor more details, see the configuration documentation."

    return msg
