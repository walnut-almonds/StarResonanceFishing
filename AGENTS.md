# AGENTS.md

A guide for coding agents working on the Star Resonance Fishing project.

## Project Overview

Star Resonance Fishing is an automated fishing bot for game automation. It uses computer vision for detection and keyboard/mouse input control to automate fishing mechanics through multiple game phases.

## Technology Stack

- Python 3.14+ (managed by uv)
- OpenCV for computer vision
- PyYAML for configuration
- WinAPI for input control

## Setup

### Prerequisites
- Install uv package manager: `pip install uv` or see [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

### Environment Setup
- Python 3.14+ is automatically managed by uv
- Verify environment: `uv run python --version`
- All development must occur within the virtual environment (never use system Python)
- See [uv documentation](https://docs.astral.sh/uv/) for complete usage instructions

### Initial Setup
```bash
# Clone the repository
git clone https://github.com/walnut-almonds/StarResonanceFishing.git
cd StarResonanceFishing

# Install dependencies (automatically creates virtual environment)
uv sync
```

## Build and Test Commands

### Development Workflow
- Run checks: `uv run scripts/check.py`
- Fix issues automatically: `uv run scripts/check.py --fix`
- Package executable: `uv run scripts/pack.py`
- Run application: `uv run main.py`

### Testing
- The agent should run `uv run scripts/check.py` before committing to ensure code quality
- Fix any issues reported by the check script
- Verify the application starts without errors

## Code Style and Standards

- Follow PEP 8 Python conventions
- Use type hints for function parameters and return types
- Write docstrings for classes and public functions
- Keep functions focused and single-responsibility
- Use snake_case for variables and functions, PascalCase for classes

## Project Structure

- `src/` - Main application source code
  - `phases/` - Game phase implementations (casting, tension, waiting, completion, preparation)
  - `fishing_bot.py` - Core bot orchestration
  - `image_detector.py` - Computer vision detection logic
  - `input_controller.py` - Input simulation abstraction
  - `window_manager.py` - Window detection and management
  - `config_manager.py` - Configuration handling
- `scripts/` - Development utilities (check.py, pack.py)
- `config.yaml` - Application configuration file
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies
- `pyproject.toml` - Project metadata and configuration

## Key Implementation Details

- All game interactions happen through phase classes in `src/phases/`
- Image detection uses template matching - detection areas are configurable
- Input control is abstracted to support different input methods (WinAPI, etc.)
- Configuration is YAML-based and loaded at startup

## Before Committing

### Pre-commit Checklist
- Run full check suite: `uv run scripts/check.py --fix`
- Verify application starts: `uv run main.py --help` (or integration test if available)
- Update `AGENTS.md` if adding new tools, commands, or conventions

### Commit Message Format
- Format: `type: description` (e.g., `fix: input timing issue`)
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
