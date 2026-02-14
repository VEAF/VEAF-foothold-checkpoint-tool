"""Campaign detection and file pattern matching."""

import re
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foothold_checkpoint.core.config import Config


# Regex pattern for campaign files
# Matches: foothold[_]<campaign>[_version].<extension>
# Requires either underscore after 'foothold' OR uppercase letter (footholdSyria)
# Examples:
#   - foothold_afghanistan.lua (with underscore)
#   - FootHold_CA_v0.2.lua (with underscore)
#   - footholdSyria_Extended_0.1.lua (no underscore but uppercase S)
#   - foothold_syria_extended_V0.1_storage.csv
#   - FOOTHOLD_Germany_0.3_CTLD_FARPS.csv
CAMPAIGN_FILE_PATTERN = re.compile(
    r"^[Ff][Oo][Oo][Tt][Hh][Oo][Ll][Dd]"  # 'foothold' in any case
    r"(?:_|(?=[A-Z]))"  # Followed by underscore OR uppercase letter
    r"[a-zA-Z0-9_]+"  # Campaign name (letters, numbers, underscores)
    r"(?:_[vV]?[0-9]+\.[0-9]+)?"  # Optional version suffix (_v0.2, _V0.1, _0.1)
    r"(?:_(?:[Cc][Tt][Ll][Dd]_[Ff][Aa][Rr][Pp][Ss]|[Cc][Tt][Ll][Dd]_[Ss][Aa][Vv][Ee]|[Ss][Tt][Oo][Rr][Aa][Gg][Ee]))?"  # Optional file type suffix (case-insensitive)
    r"\.(lua|csv)$",  # File extension (.lua or .csv)
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
    filename = filename.name if isinstance(filename, Path) else Path(filename).name

    # Check if it matches Foothold_Ranks.lua (case-insensitive)
    return filename.lower() == "foothold_ranks.lua"


def is_campaign_file(filename: str | Path) -> bool:
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
    filename = filename.name if isinstance(filename, Path) else Path(filename).name

    # Ignore hidden files
    if filename.startswith("."):
        return False

    # Special case: foothold.status is not a campaign file
    if filename.lower() == "foothold.status":
        return False

    # Match against campaign file pattern
    return bool(CAMPAIGN_FILE_PATTERN.match(filename))


def normalize_campaign_name(filename: str | Path) -> str:
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
    filename = filename.name if isinstance(filename, Path) else Path(filename).name

    # Remove file extension
    name_without_ext = filename.rsplit(".", 1)[0]

    # Remove 'foothold' or 'foothold_' prefix (case-insensitive)
    # Use regex to handle case-insensitive matching and optional underscore
    name_without_prefix = re.sub(r"^foothold_?", "", name_without_ext, flags=re.IGNORECASE)

    # Remove version suffix patterns: _v0.2, _V0.1, _0.1
    # Pattern: underscore followed by optional v/V, then digits.digits
    name_without_version = re.sub(r"_[vV]?[0-9]+(?:\.[0-9]+)?", "", name_without_prefix)

    # Remove file type suffixes: _storage, _CTLD_FARPS, _CTLD_Save
    # Era suffixes (_Coldwar, _Modern) are part of the campaign name and should NOT be removed
    # This ensures "Germany_CTLD_FARPS_Modern" and "Germany_Modern_CTLD_FARPS" both normalize to "germany_modern"
    name_normalized = re.sub(
        r"_(storage|CTLD_FARPS|CTLD_Save)", "", name_without_version, flags=re.IGNORECASE
    )

    # Normalize to lowercase for consistent grouping (case-insensitive)
    # This ensures "Afghanistan", "afghanistan", "AFGHANISTAN" all map to same group
    name_normalized = name_normalized.lower()

    return name_normalized


def group_campaign_files(filenames: Sequence[str | Path]) -> dict[str, list[str]]:
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
        # Skip shared files (Foothold_Ranks.lua)
        if is_shared_file(filename):
            continue

        # Get normalized campaign name
        campaign_name = normalize_campaign_name(filename)

        # Skip non-campaign files (normalize returns empty string)
        if not campaign_name:
            continue

        # Convert Path to string if needed, preserving original filename
        filename_str = str(filename) if isinstance(filename, Path) else filename
        # Extract just the filename (not the full path)
        filename_str = filename.name if isinstance(filename, Path) else Path(filename).name

        # Add to the group
        groups[campaign_name].append(filename_str)

    # Convert defaultdict back to regular dict
    return dict(groups)


def map_campaign_name(campaign_name: str, config: "Config") -> str:
    """Map a campaign name to its current name using config mappings.

    Uses the configuration's campaign mappings to translate historical campaign
    names to their current name (the last name in the list). This is used during
    checkpoint restoration to ensure files use the current campaign naming.

    Args:
        campaign_name: The normalized campaign name to map (lowercase).
        config: Configuration object containing campaign mappings.

    Returns:
        str: The current campaign name (last in list), or the original name if not found.

    Examples:
        >>> # Config: Germany_Modern: [GCW_Modern, germany_modern]
        >>> map_campaign_name("gcw_modern", config)
        'germany_modern'
        >>> # Config: Caucasus: [CA]
        >>> map_campaign_name("ca", config)
        'CA'
        >>> map_campaign_name("unknown", config)
        'unknown'
    """
    # Search through all campaign mappings (case-insensitive)
    for _, name_list in config.campaigns.items():
        # Normalize all names in the list to lowercase for comparison
        normalized_names = [name.lower() for name in name_list]

        # If the campaign name matches any name in the list
        if campaign_name in normalized_names:
            # Return the last (current) name in the list
            return name_list[-1]

    # If not found in config, return unchanged
    return campaign_name


def detect_campaigns(filenames: Sequence[str | Path], config: "Config") -> dict[str, list[str]]:
    """Detect and group campaign files, applying name mapping from config.

    Combines file grouping with campaign name mapping to produce groups
    keyed by current campaign names rather than historical names.

    Args:
        filenames: List of filenames to detect and group.
        config: Configuration object containing campaign mappings.

    Returns:
        dict: Dictionary mapping current campaign names to lists of filenames.

    Examples:
        >>> # Config: Germany_Modern: [GCW_Modern, Germany_Modern]
        >>> files = ["FootHold_GCW_Modern.lua", "foothold_afghanistan.lua"]
        >>> detect_campaigns(files, config)
        {
            'germany_modern': ['FootHold_GCW_Modern.lua'],
            'afghanistan': ['foothold_afghanistan.lua']
        }
    """
    # First, group files by normalized name
    groups = group_campaign_files(filenames)

    # Then, apply name mapping to group keys
    mapped_groups: dict[str, list[str]] = defaultdict(list)

    for campaign_name, files in groups.items():
        # Map the campaign name to its current name
        current_name = map_campaign_name(campaign_name, config)

        # Add files to the mapped group
        mapped_groups[current_name].extend(files)

    return dict(mapped_groups)


def create_campaign_report(filenames: Sequence[str | Path], config: "Config") -> dict[str, int]:
    """Create a campaign detection report with file counts.

    Analyzes a list of filenames and generates a summary report showing
    how many files belong to each detected campaign. Uses campaign name
    mapping from config to ensure current names are used.

    Args:
        filenames: List of filenames to analyze (strings or Path objects).
                  Can include campaign files, shared files, and other files.
        config: Configuration object containing campaign mappings.

    Returns:
        dict: Dictionary mapping current campaign names to file counts.
              Only includes campaigns with at least one file.
              Empty dict if no campaign files are found.

    Examples:
        >>> # Config: Germany_Modern: [gcw_modern, germany_modern]
        >>> files = ["FootHold_GCW_Modern.lua", "foothold_afghanistan.lua"]
        >>> create_campaign_report(files, config)
        {
            'germany_modern': 1,
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
    # Detect and group campaigns with name mapping
    campaigns = detect_campaigns(filenames, config)

    # Convert to file count report
    report = {name: len(files) for name, files in campaigns.items()}

    return report


def rename_campaign_file(filename: str | Path, config: "Config") -> str:
    """Rename a campaign file to use the current campaign name from config.

    This function is used during checkpoint restoration to rename files
    that use historical campaign names to their current names. For example,
    if a campaign evolved from "GCW_Modern" to "Germany_Modern", files like
    "FootHold_GCW_Modern.lua" are renamed to "FootHold_Germany_Modern.lua".

    The function preserves:
    - Original prefix case (foothold vs FootHold vs FOOTHOLD)
    - File extensions (.lua, .csv)
    - File type suffixes (_storage, _CTLD_FARPS, _CTLD_Save)

    Non-campaign files (shared files, unknown files) are returned unchanged.

    Args:
        filename: The filename to potentially rename (string or Path object).
                 Can be just a filename or a full path (only filename is used).
        config: Configuration object containing campaign mappings.

    Returns:
        str: The renamed filename, or original filename if:
             - Not a campaign file (e.g., Foothold_Ranks.lua)
             - Campaign not found in config
             - Campaign name hasn't changed

    Examples:
        >>> # Config: Germany_Modern: [gcw_modern, germany_modern]
        >>> rename_campaign_file("FootHold_GCW_Modern.lua", config)
        'FootHold_germany_modern.lua'

        >>> rename_campaign_file("FootHold_GCW_Modern_storage.csv", config)
        'FootHold_germany_modern_storage.csv'

        >>> # Unchanged campaign name
        >>> rename_campaign_file("foothold_afghanistan.lua", config)
        'foothold_afghanistan.lua'

        >>> # Non-campaign file
        >>> rename_campaign_file("Foothold_Ranks.lua", config)
        'Foothold_Ranks.lua'
    """
    # Extract filename if a Path object is provided
    filename = filename.name if isinstance(filename, Path) else Path(filename).name

    # Don't rename non-campaign files
    if not is_campaign_file(filename):
        return filename

    # Extract the normalized campaign name
    normalized_name = normalize_campaign_name(filename)

    if not normalized_name:
        # Shouldn't happen (is_campaign_file returned True), but safety check
        return filename

    # Map to current campaign name
    current_name = map_campaign_name(normalized_name, config)

    # If the name hasn't changed, return original
    if current_name == normalized_name:
        return filename

    # Now we need to reconstruct the filename with the new campaign name
    # while preserving the original structure

    # Remove file extension to work with the name part
    name_without_ext = filename.rsplit(".", 1)[0]
    extension = filename.rsplit(".", 1)[1]  # .lua or .csv

    # Extract the original prefix (preserving case)
    # Pattern: foothold[_]<campaign>_<rest>
    # We need to find where "foothold" or "foothold_" ends (case-insensitive)
    prefix_match = re.match(r"(foothold_?)", name_without_ext, re.IGNORECASE)
    if not prefix_match:
        # Shouldn't happen, but safety
        return filename

    original_prefix = prefix_match.group(1)  # "foothold_", "FootHold_", "footholdSyria" etc.

    # Remove the prefix to get the rest
    name_after_prefix = name_without_ext[len(original_prefix) :]

    # The name_after_prefix can have various patterns:
    # - "afghanistan"
    # - "GCW_Modern_v0.2_storage"
    # - "Germany_Modern_CTLD_FARPS"
    # - "Germany_CTLD_FARPS_Modern" (era after file type)
    #
    # Strategy: remove all known suffixes (version, file type) to extract campaign name,
    # then reconstruct with current_name preserving the suffixes

    # Extract and remove file type suffix if present (can be anywhere in the name)
    file_type_suffix = ""
    file_type_match = re.search(
        r"_(storage|CTLD_FARPS|CTLD_Save)", name_after_prefix, re.IGNORECASE
    )
    if file_type_match:
        file_type_suffix = file_type_match.group(0)
        # Remove from name (preserve order by keeping track of position)
        name_after_prefix = name_after_prefix.replace(file_type_suffix, "", 1)

    # Extract and remove version suffix if present
    version_suffix = ""
    version_match = re.search(r"_[vV]?[0-9]+(?:\.[0-9]+)?", name_after_prefix)
    if version_match:
        version_suffix = version_match.group(0)
        name_after_prefix = name_after_prefix.replace(version_suffix, "", 1)

    # Now name_after_prefix contains just the campaign name (possibly with era like _Modern)
    # This should match the normalized name after mapping

    # Reconstruct the filename with standardized order: prefix + campaign + filetype + extension
    # Note: version suffix is intentionally NOT preserved during renaming
    # This ensures clean, consistent naming without confusing version numbers from different campaigns
    new_filename = f"{original_prefix}{current_name}{file_type_suffix}.{extension}"

    return new_filename
