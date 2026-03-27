---
name: pc-control
description: Control local PC - file operations, system commands, window management, screenshots
category: system
tags: [system, automation, desktop]
---

# PC Control Skill

Control your local computer through Hermes Agent.

## Capabilities

- File/Folder operations (create, delete, move, search)
- System commands execution
- Window management (list, focus, minimize, close)
- Screenshots and screen recording
- Process management
- System info monitoring
- Clipboard operations
- Application launching

## Usage

```python
from skills.pc_control import PCController

pc = PCController()

# Files
pc.create_file("~/test.txt", "Hello World")
pc.search_files("*.py", "~/projects")

# System
pc.run_command("ls -la")
pc.get_system_info()

# Windows
pc.list_windows()
pc.focus_window("Chrome")

# Screenshot
pc.screenshot("~/screenshot.png")
```
