# VEAF Foothold Checkpoint Tool

A CLI tool for managing DCS Foothold campaign checkpoints with integrity verification and cross-server restoration.

## Status

🚧 **In Development** - OpenSpec design phase complete, implementation in progress.

## Features (Planned)

- **Save checkpoints**: Create timestamped backups of Foothold campaign saves
- **Restore checkpoints**: Restore campaigns with integrity verification (SHA-256)
- **Cross-server support**: Restore checkpoints from one server to another
- **Campaign evolution**: Handle campaign name changes transparently
- **Import**: Convert existing manual backups to checkpoint format
- **CLI modes**: Command-line flags or interactive prompts
- **Rich UI**: Progress bars, tables, colored output

## Project Structure

```
VEAF-Foothold-Campaign-Manager/
├── openspec/               # OpenSpec design artifacts
│   └── changes/
│       └── foothold-checkpoint-tool/
│           ├── proposal.md      # Project vision
│           ├── design.md        # Technical architecture
│           ├── specs/           # 8 capability specifications
│           └── tasks.md         # 211 implementation tasks
├── tests/
│   └── data/foothold/      # Test data
└── .claude/                # Development memory and guidelines
```

## Requirements

- Python 3.10+
- Windows environment (PowerShell)
- DCS servers with Foothold campaigns

## Development Status

**Current Phase**: OpenSpec Design Complete

- ✅ Proposal (vision and capabilities)
- ✅ Design (architecture and technical decisions)
- ✅ Specifications (8 detailed capability specs)
- ✅ Tasks (211 implementation tasks)
- 🚧 Implementation (next phase)

## Documentation

- [OpenSpec Proposal](openspec/changes/foothold-checkpoint-tool/proposal.md) - Why and what
- [OpenSpec Design](openspec/changes/foothold-checkpoint-tool/design.md) - How and architecture
- [OpenSpec Specs](openspec/changes/foothold-checkpoint-tool/specs/) - Detailed requirements
- [OpenSpec Tasks](openspec/changes/foothold-checkpoint-tool/tasks.md) - Implementation checklist
- [Conversation History](openspec/changes/foothold-checkpoint-tool/conversation.md) - Design rationale

## Contributing

This project follows Test-Driven Development (TDD) practices:
- All code in English
- Communication in French
- Tests must be written before implementation
- Keep a Changelog format
- Quality checks: ruff, black, mypy

See [Development Guidelines](.claude/projects/d--dev--VEAF-VEAF-Foothold-Campaign-Manager/memory/development-guidelines.md) for details.

## License

TBD

## Credits

Developed for [VEAF](https://www.veaf.org/) - Virtual European Air Force
