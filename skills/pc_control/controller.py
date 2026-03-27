import os
import subprocess
import shutil
import json
import platform
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

class PCController:
    def __init__(self):
        self.system = platform.system()
        self.history = []
    
    def _log(self, action: str, details: Dict):
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        })
    
    # ==================== FILE OPERATIONS ====================
    
    def create_file(self, path: str, content: str = "") -> Dict:
        try:
            full_path = Path(path).expanduser()
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            self._log("create_file", {"path": str(full_path), "size": len(content)})
            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_file(self, path: str, offset: int = 0, limit: int = 1000) -> Dict:
        try:
            full_path = Path(path).expanduser()
            content = full_path.read_text()
            lines = content.split('\n')
            selected = lines[offset:offset+limit]
            
            return {
                "success": True,
                "path": str(full_path),
                "content": '\n'.join(selected),
                "total_lines": len(lines),
                "offset": offset,
                "limit": limit
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_file(self, path: str) -> Dict:
        try:
            full_path = Path(path).expanduser()
            if full_path.is_file():
                full_path.unlink()
            elif full_path.is_dir():
                shutil.rmtree(full_path)
            
            self._log("delete_file", {"path": str(full_path)})
            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def move_file(self, src: str, dst: str) -> Dict:
        try:
            src_path = Path(src).expanduser()
            dst_path = Path(dst).expanduser()
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(src_path), str(dst_path))
            self._log("move_file", {"src": str(src_path), "dst": str(dst_path)})
            return {"success": True, "src": str(src_path), "dst": str(dst_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def copy_file(self, src: str, dst: str) -> Dict:
        try:
            src_path = Path(src).expanduser()
            dst_path = Path(dst).expanduser()
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if src_path.is_file():
                shutil.copy2(str(src_path), str(dst_path))
            else:
                shutil.copytree(str(src_path), str(dst_path))
            
            self._log("copy_file", {"src": str(src_path), "dst": str(dst_path)})
            return {"success": True, "src": str(src_path), "dst": str(dst_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_files(self, pattern: str, path: str = "~", recursive: bool = True) -> Dict:
        try:
            search_path = Path(path).expanduser()
            matches = []
            
            if recursive:
                for p in search_path.rglob(pattern):
                    matches.append({
                        "path": str(p),
                        "size": p.stat().st_size if p.is_file() else 0,
                        "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                    })
            else:
                for p in search_path.glob(pattern):
                    matches.append({
                        "path": str(p),
                        "size": p.stat().st_size if p.is_file() else 0,
                        "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                    })
            
            return {"success": True, "matches": matches, "count": len(matches)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_directory(self, path: str = "~") -> Dict:
        try:
            dir_path = Path(path).expanduser()
            entries = []
            
            for entry in dir_path.iterdir():
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "path": str(entry),
                    "type": "file" if entry.is_file() else "directory",
                    "size": stat.st_size if entry.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            return {"success": True, "path": str(dir_path), "entries": entries}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== SYSTEM COMMANDS ====================
    
    def run_command(self, command: str, timeout: int = 60, cwd: str = None) -> Dict:
        try:
            work_dir = Path(cwd).expanduser() if cwd else None
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir
            )
            
            self._log("run_command", {"command": command, "exit_code": result.returncode})
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_background(self, command: str, cwd: str = None) -> Dict:
        try:
            work_dir = Path(cwd).expanduser() if cwd else None
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=work_dir
            )
            
            self._log("run_background", {"command": command, "pid": process.pid})
            
            return {
                "success": True,
                "pid": process.pid,
                "command": command
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== SYSTEM INFO ====================
    
    def get_system_info(self) -> Dict:
        try:
            info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
            }
            
            # Memory info
            if self.system == "Linux":
                mem = subprocess.run(["free", "-m"], capture_output=True, text=True)
                info["memory"] = mem.stdout
            elif self.system == "Darwin":
                mem = subprocess.run(["vm_stat"], capture_output=True, text=True)
                info["memory"] = mem.stdout
            
            # Disk usage
            disk = shutil.disk_usage("/")
            info["disk"] = {
                "total_gb": disk.total // (2**30),
                "used_gb": disk.used // (2**30),
                "free_gb": disk.free // (2**30)
            }
            
            return {"success": True, "info": info}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_processes(self, limit: int = 20) -> Dict:
        try:
            if self.system == "Linux":
                result = subprocess.run(
                    ["ps", "aux", "--sort=-%cpu"],
                    capture_output=True,
                    text=True
                )
                lines = result.stdout.strip().split('\n')[1:limit+1]
                processes = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "command": ' '.join(parts[10:])
                        })
                return {"success": True, "processes": processes}
            
            elif self.system == "Darwin":
                result = subprocess.run(
                    ["ps", "aux", "-r"],
                    capture_output=True,
                    text=True
                )
                lines = result.stdout.strip().split('\n')[1:limit+1]
                processes = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "command": ' '.join(parts[10:])
                        })
                return {"success": True, "processes": processes}
            
            return {"success": False, "error": "Unsupported platform"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def kill_process(self, pid: int) -> Dict:
        try:
            os.kill(pid, 9)
            self._log("kill_process", {"pid": pid})
            return {"success": True, "pid": pid}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== WINDOW MANAGEMENT ====================
    
    def list_windows(self) -> Dict:
        try:
            if self.system == "Linux":
                result = subprocess.run(
                    ["wmctrl", "-l"],
                    capture_output=True,
                    text=True
                )
                windows = []
                for line in result.stdout.strip().split('\n'):
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        windows.append({
                            "id": parts[0],
                            "desktop": parts[1],
                            "host": parts[2],
                            "title": parts[3]
                        })
                return {"success": True, "windows": windows}
            
            elif self.system == "Darwin":
                script = '''
                tell application "System Events"
                    set windowList to {}
                    repeat with proc in (get processes whose background only is false)
                        set procName to name of proc
                        set windowList to windowList & procName
                    end repeat
                    return windowList
                end tell
                '''
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True
                )
                apps = result.stdout.strip().split(', ')
                windows = [{"title": app, "id": i} for i, app in enumerate(apps)]
                return {"success": True, "windows": windows}
            
            return {"success": False, "error": "Unsupported platform"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def focus_window(self, title: str) -> Dict:
        try:
            if self.system == "Linux":
                subprocess.run(["wmctrl", "-a", title], check=True)
                self._log("focus_window", {"title": title})
                return {"success": True, "title": title}
            
            elif self.system == "Darwin":
                script = f'''
                tell application "{title}"
                    activate
                end tell
                '''
                subprocess.run(["osascript", "-e", script], check=True)
                self._log("focus_window", {"title": title})
                return {"success": True, "title": title}
            
            return {"success": False, "error": "Unsupported platform"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def minimize_window(self, title: str) -> Dict:
        try:
            if self.system == "Linux":
                result = subprocess.run(
                    ["xdotool", "search", "--name", title, "windowminimize"],
                    capture_output=True,
                    text=True
                )
                return {"success": result.returncode == 0, "title": title}
            
            elif self.system == "Darwin":
                script = f'''
                tell application "System Events"
                    tell process "{title}"
                        set value of attribute "AXMinimized" of window 1 to true
                    end tell
                end tell
                '''
                subprocess.run(["osascript", "-e", script], check=True)
                return {"success": True, "title": title}
            
            return {"success": False, "error": "Unsupported platform"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== SCREENSHOTS ====================
    
    def screenshot(self, output_path: str = None, window_title: str = None) -> Dict:
        try:
            if output_path is None:
                output_path = f"~/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            full_path = Path(output_path).expanduser()
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.system == "Linux":
                if window_title:
                    subprocess.run(
                        ["import", "-window", window_title, str(full_path)],
                        check=True
                    )
                else:
                    subprocess.run(
                        ["gnome-screenshot", "-f", str(full_path)],
                        check=True
                    )
            
            elif self.system == "Darwin":
                if window_title:
                    script = f'''
                    tell application "{window_title}"
                        set winPos to position of window 1
                        set winSize to size of window 1
                    end tell
                    do shell script "screencapture -R" & (item 1 of winPos) & "," & (item 2 of winPos) & "," & (item 1 of winSize) & "," & (item 2 of winSize) & " {full_path}"
                    '''
                    subprocess.run(["osascript", "-e", script], check=True)
                else:
                    subprocess.run(
                        ["screencapture", "-x", str(full_path)],
                        check=True
                    )
            
            self._log("screenshot", {"path": str(full_path)})
            return {"success": True, "path": str(full_path)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== CLIPBOARD ====================
    
    def clipboard_get(self) -> Dict:
        try:
            if self.system == "Linux":
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-o"],
                    capture_output=True,
                    text=True
                )
                return {"success": True, "content": result.stdout}
            
            elif self.system == "Darwin":
                result = subprocess.run(
                    ["pbpaste"],
                    capture_output=True,
                    text=True
                )
                return {"success": True, "content": result.stdout}
            
            return {"success": False, "error": "Unsupported platform"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def clipboard_set(self, content: str) -> Dict:
        try:
            if self.system == "Linux":
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=content,
                    text=True
                )
            
            elif self.system == "Darwin":
                subprocess.run(
                    ["pbcopy"],
                    input=content,
                    text=True
                )
            
            self._log("clipboard_set", {"content_length": len(content)})
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== APPLICATIONS ====================
    
    def launch_app(self, app_name: str, args: List[str] = None) -> Dict:
        try:
            args = args or []
            
            if self.system == "Linux":
                subprocess.Popen([app_name] + args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            elif self.system == "Darwin":
                if not app_name.endswith('.app'):
                    app_name = f"/Applications/{app_name}.app"
                subprocess.run(["open", "-a", app_name] + args, check=True)
            
            self._log("launch_app", {"app": app_name, "args": args})
            return {"success": True, "app": app_name}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_history(self) -> List[Dict]:
        return self.history
