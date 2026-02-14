"""Campaign detection and file pattern matching."""

import re
from pathlib import Path
from typing import Union
from collections import defaultdict


# Regex pattern for campaign files
# Matches: foothold_<campaign>[_version].<extension> (case-insensitive)
# Examples:
#   - foothold_afghanistan.lua
#   - FootHold_CA_v0.2.lua
#   - foothold_syria_extended_V0.1_storage.csv
#   - FOOTHOLD_Germany_0.3_CTLD_FARPS.csv
CAMPAIGN_FILE_PATTERN = re.compile(
    r'^foothold_'  # Must start with 'foothold_' (case-insensitive)
    r'[a-z0-9_]+'  # Campaign name (letters, numbers, underscores)
    r'(?:_[vV]?[0-9]+\.[0-9]+)?'  # Optional version suffix (_v0.2, _V0.1, _0.1)
    r'(?:_(?:CTLD_FARPS|CTLD_Save|storage))?'  # Optional file type suffix
    r'\.(lua|csv)$',  # File extension (.lua or .csv)
    re.IGNORECASE
)


def is_campaign_file(filename: Union[str, Path]) -> bool:
    """Check if a filename matches the Foothold campaign file pattern.

    This function identifies files that belong to a Foothold campaign by matching
    naming patterns. It recognizes various file types (.lua, _storage.csv,
    _CTLD_FARPS.csv, _CTLD_Save.csv) with optional version suffixes.

    Special cases:
    - foothold.status is NOT a campaign file (no underscore after prefix)
    - Foothold_Ranks.lua is handled separately as a shared file
    - Hidden files (starting with .) are ignored
    - Files without 'foothold' prefix are ignored

    Args:
        filename: The filename to check (string or Path object).
                 Can be just a filename or a full path.

    Returns:
        bool: True if the file matches a campaign file pattern, False otherwise.

    Examples:
        >>> is_campaign_file("foothold_afghanistan.lua")
        True
        >>> is_campaign_file("FootHold_CA_v0.2_storage.csv")
        True
        >>> is_campaign_file("foothold.status")
        False
        >>> is_campaign_file("README.txt")
        False
    """
    # Extract filename if a Path object or full path string is provided
    if isinstance(filename, Path):
        filename = filename.name
    else:
        filename = Path(filename).name

    # Ignore hidden files
    if filename.startswith('.'):
        return False

    # Special case: foothold.status is not a campaign file
    if filename.lower() == 'foothold.status':
        return False

    # Match against campaign file pattern
    return bool(CAMPAIGN_FILE_PATTERN.match(filename))


def normalize_campaign_name(filename: Union[str, Path]) -> str:
    """Extract and normalize the campaign name from a filename.

    Removes the 'foothold_' prefix, version suffixes, and file type suffixes
    to extract the core campaign name. Returns an empty string if the file
    is not a valid campaign file.

    Version suffix patterns removed:
    - _v0.2, _v1.0 (lowercase 'v')
    - _V0.1, _V2.3 (uppercase 'V')
    - _0.1, _1.5 (numeric only)

    File type suffixes removed:
    - _storage
    - _CTLD_FARPS
    - _CTLD_Save

    Args:
        filename: The filename to normalize (string or Path object).
                 Can be just a filename or a full path.

    Returns:
        str: The normalized campaign name, or empty string if not a campaign file.

    Examples:
        >>> normalize_campaign_name("FootHold_CA_v0.2.lua")
        'CA'
        >>> normalize_campaign_name("foothold_afghanistan.lua")
        'afghanistan'
        >>> normalize_campaign_name("FootHold_Germany_Modern_V0.1_storage.csv")
        'Germany_Modern'
        >>> normalize_campaign_name("README.txt")
        ''
    """
    # First check if it's a valid campaign file
    if not is_campaign_file(filename):
        return ""

    # Extract filename if a Path object or full path string is provided
    if isinstance(filename, Path):
        filename = filename.name
    else:
        filename = Path(filename).name

    # Remove file extension
    name_without_ext = filename.rsplit('.', 1)[0]

    # Remove 'foothold_' prefix (case-insensitive)
    # Use regex to handle case-insensitive matching
    name_without_prefix = re.sub(r'^foothold_', '', name_without_ext, flags=re.IGNORECASE)

    # Remove version suffix patterns: _v0.2, _V0.1, _0.1
    # Pattern: underscore followed by optional v/V, then digits.digits
    name_without_version = re.sub(r'_[vV]?[0-9]+(?:\.[0-9]+)?', '', name_without_prefix)

    # Remove file type suffixes: _storage, _CTLD_FARPS, _CTLD_Save
    name_normalized = re.sub(r'_(storage|CTLD_FARPS|CTLD_Save)$', '', name_without_version, flags=re.IGNORECASE)

    # Normalize to lowercase for consistent grouping (case-insensitive)
    # This ensures "Afghanistan", "afghanistan", "AFGHANISTAN" all map to same group
    name_normalized = name_normalized.lower()

    return name_normalized


def group_campaign_files(filenames: list[Union[str, Path]]) -> dict[str, list[str]]:
    """Group campaign files by their normalized campaign name.

    Takes a list of filenames and groups them by campaign, using the normalized
    campaign name as the key. Files with different version suffixes or mixed
    case are grouped together. Non-campaign files are ignored.

    The original filenames are preserved in the groups (not normalized), but
    they are grouped by their normalized campaign name.

    Args:
        filenames: List of filenames (strings or Path objects) to group.
                  Can include non-campaign files which will be filtered out.

    Returns:
        dict: Dictionary mapping normalized campaign names to lists of original filenames.
              Returns empty dict if no campaign files are found.

    Examples:
        >>> group_campaign_files([
        ...     "foothold_afghanistan.lua",
        ...     "foothold_afghanistan_storage.csv",
        ...     "FootHold_CA.lua"
        ... ])
        {
            'afghanistan': ['foothold_afghanistan.lua', 'foothold_afghanistan_storage.csv'],
            'CA': ['FootHold_CA.lua']
        }

        >>> group_campaign_files([
        ...     "FootHold_CA_v0.2.lua",
        ...     "foothold_ca_V0.1_storage.csv"
        ... ])
        {'CA': ['FootHold_CA_v0.2.lua', 'foothold_ca_V0.1_storage.csv']}
    """
    # Use defaultdict to automatically create empty lists
    groups: dict[str, list[str]] = defaultdict(list)

    for filename in filenames:
        # Get normalized campaign name
        campaign_name = normalize_campaign_name(filename)

        # Skip non-campaign files (normalize returns empty string)
        if not campaign_name:
            continue

        # Convert Path to string if needed, preserving original filename
        filename_str = str(filename) if isinstance(filename, Path) else filename
        # Extract just the filename (not the full path)
        if isinstance(filename, Path):
            filename_str = filename.name
        else:
            filename_str = Path(filename).name

        # Add to the group
        groups[campaign_name].append(filename_str)

    # Convert defaultdict back to regular dict
    return dict(groups)
