## MODIFIED Requirements

### Requirement: System SHALL detect campaign files using explicit configuration

The system SHALL identify Foothold campaign files by matching filenames against explicit lists defined in config.yaml for each campaign, rather than using regex pattern matching.

#### Scenario: File matches configured name exactly
- **WHEN** a directory contains `FootHold_CA_v0.2.lua` and config lists this exact filename for the caucasus campaign
- **THEN** the system identifies the file as belonging to the caucasus campaign

#### Scenario: File with era suffix matches configuration
- **WHEN** a directory contains `Foothold_CA_CTLD_FARPS_Modern.csv` and config lists this exact filename for the caucasus campaign
- **THEN** the system identifies the file as belonging to the caucasus campaign (not a separate ca_modern campaign)

#### Scenario: Multiple file names for same file type
- **WHEN** config lists both `FootHold_CA_v0.2.lua` and `FootHold_Caucasus_v0.3.lua` as persistence files for the caucasus campaign
- **THEN** the system recognizes either filename as belonging to the caucasus campaign

#### Scenario: File not in configuration
- **WHEN** a directory contains `foothold_unknown.lua` which is not listed in any campaign configuration
- **THEN** the system fails with error message listing the unknown file and suggesting config update

#### Scenario: Multiple campaigns in same directory
- **WHEN** a directory contains files from multiple configured campaigns
- **THEN** the system correctly groups files by their configured campaign assignments

#### Scenario: No campaign files present
- **WHEN** a directory contains no files listed in any campaign configuration
- **THEN** the system reports no campaigns detected

### Requirement: System SHALL group files by campaign using configuration mapping

The system SHALL group all files belonging to the same campaign based on explicit campaign-to-file mappings in config.yaml.

#### Scenario: Complete campaign file set
- **WHEN** a directory contains all files configured for a campaign (persistence, ctld_save, ctld_farps, storage)
- **THEN** the system groups all files together under that campaign

#### Scenario: Incomplete campaign file set with optional files
- **WHEN** a directory is missing optional files (e.g., storage marked as optional in config)
- **THEN** the system groups available files without error

#### Scenario: Incomplete campaign file set with required files
- **WHEN** a directory is missing required files (e.g., persistence file not marked optional)
- **THEN** the system displays warning about missing required files but continues grouping available files

#### Scenario: Files from different naming generations
- **WHEN** a directory contains `FootHold_CA_v0.2.lua` and `Foothold_CA_CTLD_FARPS_Modern.csv` both configured for caucasus campaign
- **THEN** the system groups both files under caucasus campaign despite different naming conventions

### Requirement: System SHALL identify Foothold_Ranks.lua as a shared file

The system SHALL recognize `Foothold_Ranks.lua` as a shared file across all campaigns, not belonging to any specific campaign.

#### Scenario: Foothold_Ranks.lua present in directory
- **WHEN** the directory contains `Foothold_Ranks.lua`
- **THEN** the system identifies it as a shared file, separate from campaign-specific files

#### Scenario: Foothold_Ranks.lua absent from directory
- **WHEN** the directory does not contain `Foothold_Ranks.lua`
- **THEN** the system does not report an error (file is optional)

### Requirement: System SHALL fail on unrecognized campaign-like files

The system SHALL fail with a clear error message when encountering files that appear to be Foothold campaign files but are not configured.

#### Scenario: Unknown campaign file detected
- **WHEN** a directory contains `foothold_newmap_v1.0.lua` which matches foothold patterns but is not in configuration
- **THEN** the system displays error: "Unknown campaign files detected: foothold_newmap_v1.0.lua" with instructions to update config.yaml

#### Scenario: Multiple unknown files
- **WHEN** a directory contains multiple unconfigured files matching foothold patterns
- **THEN** the system lists all unknown files and suggests adding them to configuration

#### Scenario: Unknown file detection with guidance
- **WHEN** unknown files are detected
- **THEN** error message includes example config.yaml snippet showing how to add the campaign

### Requirement: System SHALL report detected campaigns with file counts

The system SHALL report detected campaigns along with the count of files found for each campaign.

#### Scenario: List campaigns with file counts
- **WHEN** the system scans a directory with multiple campaigns
- **THEN** the output includes campaign names and file counts (e.g., "caucasus: 4 files", "afghanistan: 3 files")

#### Scenario: Empty directory
- **WHEN** the system scans an empty directory
- **THEN** the output indicates "No campaigns detected"

## REMOVED Requirements

### Requirement: System SHALL detect campaign files by naming patterns

**Reason**: Replaced by explicit configuration-based detection which eliminates ambiguity with era suffixes and provides better control over file naming evolution.

**Migration**: Add all campaign file names explicitly to config.yaml under each campaign's `files` section. See design.md for configuration structure.

### Requirement: System SHALL normalize campaign names by removing version suffixes

**Reason**: No longer needed with explicit file-to-campaign mapping. Configuration directly specifies which files belong to which campaign.

**Migration**: No migration needed - normalization logic is completely replaced by configuration lookup.

### Requirement: System SHALL map normalized names to configured campaign names

**Reason**: Replaced by direct file-to-campaign mapping in configuration. No normalization step needed.

**Migration**: Instead of mapping campaign names, list all file name variations directly under each campaign in config.yaml.
