## Purpose

This capability provides campaign file detection and grouping for Foothold mission files. It identifies campaign files by naming patterns, normalizes campaign names, handles version suffixes, and maps historical names to current campaign identifiers.

## ADDED Requirements

### Requirement: System SHALL detect campaign files by naming patterns

The system SHALL detect Foothold campaign files in a directory by matching file naming patterns (e.g., `foothold_afghanistan*.lua`, `FootHold_CA_v0.2*.csv`).

#### Scenario: Campaign files with consistent prefix
- **WHEN** a directory contains files like `foothold_afghanistan.lua`, `foothold_afghanistan_CTLD_FARPS.csv`, `foothold_afghanistan_storage.csv`
- **THEN** the system groups them as belonging to the "afghanistan" campaign

#### Scenario: Campaign files with version suffix
- **WHEN** a directory contains files like `FootHold_CA_v0.2.lua`, `FootHold_CA_v0.2_storage.csv`
- **THEN** the system groups them as belonging to the "CA" campaign (version suffix ignored)

#### Scenario: Multiple campaigns in same directory
- **WHEN** a directory contains files from multiple campaigns (e.g., `foothold_afghanistan*` and `FootHold_CA*`)
- **THEN** the system detects and groups files by campaign correctly

#### Scenario: No campaign files present
- **WHEN** a directory contains no recognizable Foothold campaign files
- **THEN** the system reports no campaigns detected

### Requirement: System SHALL normalize campaign names by removing version suffixes

The system SHALL remove version suffixes (`_v0.2`, `_V0.1`, `_0.1`) from file names to determine the campaign identifier.

#### Scenario: Lowercase version suffix
- **WHEN** a file is named `FootHold_CA_v0.2.lua`
- **THEN** the system normalizes the campaign name to "CA"

#### Scenario: Uppercase version suffix
- **WHEN** a file is named `FootHold_Germany_Modern_V0.1.lua`
- **THEN** the system normalizes the campaign name to "Germany_Modern"

#### Scenario: Numeric version suffix
- **WHEN** a file is named `footholdSyria_Extended_0.1.lua`
- **THEN** the system normalizes the campaign name to "Syria_Extended"

#### Scenario: No version suffix
- **WHEN** a file is named `foothold_afghanistan.lua`
- **THEN** the campaign name remains "afghanistan"

### Requirement: System SHALL group related campaign files together

The system SHALL group all files belonging to the same campaign (*.lua, *_CTLD_FARPS.csv, *_CTLD_Save.csv, *_storage.csv) based on normalized prefix.

#### Scenario: Complete campaign file set
- **WHEN** a campaign has all expected files (*.lua, *_CTLD_FARPS.csv, *_CTLD_Save.csv, *_storage.csv)
- **THEN** the system groups all four files together

#### Scenario: Incomplete campaign file set
- **WHEN** a campaign is missing some expected files (e.g., only .lua and _storage.csv present)
- **THEN** the system still groups available files together under the campaign

#### Scenario: Case-insensitive prefix matching
- **WHEN** files have mixed case prefixes (e.g., `foothold_afghanistan.lua` and `Foothold_Afghanistan_storage.csv`)
- **THEN** the system groups them together (case-insensitive matching)

### Requirement: System SHALL identify Foothold_Ranks.lua as a shared file

The system SHALL recognize `Foothold_Ranks.lua` as a shared file across all campaigns, not belonging to any specific campaign.

#### Scenario: Foothold_Ranks.lua present in directory
- **WHEN** the directory contains `Foothold_Ranks.lua`
- **THEN** the system identifies it as a shared file, separate from campaign-specific files

#### Scenario: Foothold_Ranks.lua absent from directory
- **WHEN** the directory does not contain `Foothold_Ranks.lua`
- **THEN** the system does not report an error (file is optional)

### Requirement: System SHALL ignore non-campaign files

The system SHALL ignore files that do not match Foothold campaign patterns (e.g., `foothold.status`, unrelated files).

#### Scenario: Status file present
- **WHEN** the directory contains `foothold.status`
- **THEN** the system ignores this file and does not include it in any campaign

#### Scenario: Unrelated files present
- **WHEN** the directory contains unrelated files like `README.txt`, `backup.zip`
- **THEN** the system ignores these files

#### Scenario: Hidden files present
- **WHEN** the directory contains hidden files (e.g., `.DS_Store`, `.gitignore`)
- **THEN** the system ignores these files

### Requirement: System SHALL map normalized names to configured campaign names

The system SHALL use configuration-defined campaign mappings to recognize historical campaign names and map them to current names.

#### Scenario: File uses historical campaign name
- **WHEN** a file is named `GCW_Modern_V0.1.lua` and config maps `Germany_Modern: [GCW_Modern, Germany_Modern]`
- **THEN** the system identifies the campaign as "Germany_Modern"

#### Scenario: File uses current campaign name
- **WHEN** a file is named `Germany_Modern_V0.2.lua` and config maps `Germany_Modern: [GCW_Modern, Germany_Modern]`
- **THEN** the system identifies the campaign as "Germany_Modern"

#### Scenario: Campaign name not in config
- **WHEN** a file is named `unknown_campaign.lua` and the campaign is not in config
- **THEN** the system uses the normalized prefix as the campaign name ("unknown_campaign")

### Requirement: System SHALL report detected campaigns with file counts

The system SHALL report detected campaigns along with the count of files found for each campaign.

#### Scenario: List campaigns with file counts
- **WHEN** the system scans a directory with multiple campaigns
- **THEN** the output includes campaign names and file counts (e.g., "afghanistan: 4 files", "CA: 3 files")

#### Scenario: Empty directory
- **WHEN** the system scans an empty directory
- **THEN** the output indicates "No campaigns detected"
