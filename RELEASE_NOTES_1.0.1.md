# Release Notes - Version 1.0.1

**Release Date:** February 14, 2026

## Overview

This is a patch release that fixes cross-platform compatibility issues discovered when running tests under Linux/WSL. No functional changes to the core features.

## Bug Fixes

### Cross-Platform Compatibility

- **Fixed campaign name mapping behavior**: The `map_campaign_name()` function now correctly returns the last (current) name from the campaign name list as documented, instead of the dictionary key. This ensures files are restored with the correct naming convention.

- **Linux/WSL test compatibility**: 
  - Marked `test_path_expansion_with_windows_style_envvar` as Windows-only (Windows `%VAR%` environment variable syntax is not supported on Linux)
  - Marked `test_delete_checkpoint_handles_permission_error` as Windows-only (Linux allows deletion of read-only files when the parent directory is writable, unlike Windows)

### Code Quality

- Fixed ruff linting error regarding unused loop variable in `map_campaign_name()`

## Technical Details

### Campaign Name Restoration

Files are now restored using the exact name specified as the last entry in the campaign names list in `config.yaml`, preserving case sensitivity as intended. For example:

- `campaigns: {Afghanistan: [afghanistan]}` → files use `afghanistan` (lowercase)
- `campaigns: {Germany_Modern: [gcw_modern, Germany_Modern]}` → files are renamed to `Germany_Modern`

This behavior is now correctly implemented and matches the documentation in USERS.md.

## Testing

- ✅ All 350 tests pass (3 tests skipped on Windows as expected)
- ✅ 83% code coverage maintained
- ✅ All quality checks pass (ruff, black, mypy)

## Upgrade Notes

This is a drop-in replacement for version 1.0.0. No configuration changes required.

## Credits

VEAF Team
