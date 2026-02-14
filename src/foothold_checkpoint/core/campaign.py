"""Campaign detection and file pattern matching."""

import re
from pathlib import Path
from typing import Union


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
