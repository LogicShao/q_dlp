# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Q_DLP is a modern video downloader application built with PyQt6 and yt-dlp, featuring Microsoft Fluent Design UI. It
supports downloading videos from Bilibili and YouTube with comprehensive download management, progress tracking, and
history persistence.

**Tech Stack:**

- PyQt6 6.9.0 + PyQt6-Fluent-Widgets 1.7.2 (UI Framework)
- yt-dlp 2025.5.22 (Download Engine)
- SQLite3 (Database)

## Common Commands

### Development

```bash
# Run application (Windows)
scripts\run.bat

# Run application (Linux/macOS)
bash scripts/run.sh

# Direct run
python src/main.py
```

### Building

```bash
# Build executable (Windows)
scripts\build.bat

# Build executable (Linux/macOS)
bash scripts/build.sh
```

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r config/requirements.txt
```

## Architecture

### Core Components

**src/MainWindow.py** - Main UI implementation

- `MainWindow`: FluentWindow-based main window with navigation
- `DownloadTaskListWidget`: Custom list widget for download queue with right-click context menu
- `SettingsDialog`: Configuration dialog for all app settings
- `AddTaskDialog`: Dialog for adding new download tasks
- `url_checker()`: URL validation for Bilibili/YouTube links

**src/dlp.py** - Download engine

- `DownloadThread`: QThread-based async downloader wrapping yt-dlp
- Uses progress_hooks and postprocessor_hooks to track download progress
- `finished_signal`: Emits (bool, str, str) for success, message, and file_path
- Critical: Must capture final file path after FFmpeg postprocessing, not intermediate files

**src/db.py** - Database layer

- SQLite-based download history management
- `DownloadRecord`: Dataclass for download records with file_path field
- `init_db()`: Auto-migration for schema updates
- Records are loaded on startup and saved on exit

**src/utils.py** - Configuration management

- `load_config()`/`save_config()`: JSON-based config in `config/config.json`
- `get_icon_path()`: Resource path resolution for icons

**src/m_path.py** - Path management

- Centralized path constants for cross-platform compatibility

### Key Design Patterns

**Signal-Slot Communication:**

- Download thread communicates with UI via Qt signals:
    - `log_signal(str)`: Real-time log updates
    - `progress_signal(int)`: Progress percentage (0-100)
    - `finished_signal(bool, str, str)`: Completion status with file path

**Progress Calculation:**

- Uses `downloaded_bytes/total_bytes` for accurate progress
- Falls back to `_percent_float` with 0-1 range detection
- Progress shown in both log text and StateToolTip (must match!)

**File Path Tracking:**

- yt-dlp's progress_hooks returns intermediate files
- postprocessor_hooks captures final processed file path
- Fallback: extract from info_dict if hooks fail
- File path stored in DownloadRecord for right-click menu features

**Right-Click Context Menu:**

- Only shows "Open in Explorer" / "Open with App" when file exists
- Cross-platform support (Windows/macOS/Linux)
- Delete task with optional file deletion (custom MessageBoxBase dialog)

### Configuration Structure

`config/config.json`:

```json
{
  "download": {
    "default_path": "path/to/downloads",
    "video_quality": "best|1080p|720p|480p|worst",
    "audio_quality": "best|192k|128k|96k|worst",
    "format": "mp4|webm|mkv",
    "audio_format": "mp3|m4a|wav|aac",
    "subtitle": bool,
    "thumbnail": bool
  },
  "network": {
    "proxy": "http://host:port",
    "timeout": 30,
    "retry_times": 3,
    "concurrent_downloads": 1
  },
  "ui": {
    "theme": "light|dark|auto",
    "language": "zh_CN|en_US",
    "show_log": bool,
    "auto_clear_log": bool
  },
  "advanced": {
    "use_cookies": bool,
    "cookies_file": "path/to/cookies.txt",
    "user_agent": "custom UA",
    "extract_audio": bool
  }
}
```

### Database Schema

```sql
CREATE TABLE downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT DEFAULT '',
    file_path TEXT DEFAULT '',
    platform TEXT DEFAULT '',
    download_time TEXT DEFAULT '',
    is_finished BOOLEAN DEFAULT 0,
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT ''
);
```

## Important Implementation Notes

### Progress Display Consistency

When modifying download progress, ensure both log text and StateToolTip show identical values. Progress must be
calculated from:

1. `downloaded_bytes / total_bytes * 100` (primary)
2. `_percent_float * 100` if < 1, else use as-is (fallback)

### File Path Capture

When working with yt-dlp downloads:

- Use `extract_info(url, download=True)` instead of `download([url])`
- Add postprocessor_hooks to capture final file path after FFmpeg processing
- Store file path in DownloadRecord.file_path for UI features
- Update list item text to "[已完成]" when download finishes

### Right-Click Menu Features

Context menu implementation requires:

- `customContextMenuRequested` signal connection
- File existence check before showing open options
- Cross-platform commands (explorer/open/xdg-open)
- Custom MessageBoxBase for delete confirmation with three buttons

### Theme Management

Theme changes apply immediately via `setTheme(Theme.LIGHT|DARK|AUTO)`. Config is saved separately and loaded on restart.

### PyInstaller Packaging

Critical hidden imports for successful build:

- PyQt6.QtCore, PyQt6.QtGui, PyQt6.QtWidgets
- qfluentwidgets + all submodules
- yt_dlp, sqlite3
- Use `--collect-all=qfluentwidgets` to include all Fluent resources

### Adding New Platform Support

1. Add URL pattern to `url_checker()` in MainWindow.py
2. Return platform identifier string (e.g., 'bilibili', 'youtube')
3. yt-dlp automatically handles most platforms without code changes

## Code Style

- Follow PEP 8
- Chinese comments for user-facing strings, English for technical implementation
- Use type hints for function parameters and returns
- Dataclasses for structured data (e.g., DownloadRecord)
- Context managers for database connections
- Qt signal naming: `<action>_signal` (e.g., `finished_signal`)
