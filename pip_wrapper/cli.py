import subprocess
import sys
import os
import toml
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sysconfig
import time
from threading import Lock

PYPROJECT_FILE = "pyproject.toml"
LOG_FILE = "installed_packages.json"
file_lock = Lock()  # For thread-safe file operations


def create_pyproject():
    """Create a basic pyproject.toml file if it doesn't exist."""
    if os.path.exists(PYPROJECT_FILE):
        print(f"{PYPROJECT_FILE} already exists.")
        return

    debug("Creating basic pyproject.toml...")
    project_data = {
        "tool": {
            "custom": {
                "dependencies": {}
            }
        },
        "build-system": {
            "requires": ["setuptools", "wheel"],
            "build-backend": "setuptools.build_meta"
        }
    }

    with open(PYPROJECT_FILE, "w") as f:
        toml.dump(project_data, f)

    print(f"{PYPROJECT_FILE} created successfully.")


def debug(message):
    """Print debug messages for better traceability."""
    print(f"[DEBUG] {message}")


def debug_toml_state():
    """Log the current state of pyproject.toml."""
    if os.path.exists(PYPROJECT_FILE):
        with open(PYPROJECT_FILE, "r") as f:
            debug(f"Current pyproject.toml:\n{f.read()}")
    else:
        debug("pyproject.toml does not exist.")


def is_virtual_env():
    """Check if the script is running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def initialize_pyproject():
    """Ensure pyproject.toml exists, and initialize if not."""
    if not os.path.exists(PYPROJECT_FILE):
        debug("Creating pyproject.toml...")
        create_pyproject()


def get_installed_packages():
    """Retrieve installed packages using pip freeze."""
    result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    packages = {}
    for line in result.stdout.splitlines():
        if "==" in line:
            name, version = line.split("==")
            packages[name] = version
    return packages


def backup_pyproject():
    """Create a backup of pyproject.toml."""
    if os.path.exists(PYPROJECT_FILE):
        backup_file = f"{PYPROJECT_FILE}.backup"
        debug(f"Creating backup: {backup_file}")
        with open(PYPROJECT_FILE, "r") as original, open(backup_file, "w") as backup:
            backup.write(original.read())


global_dependencies_state = {}  # In-memory store for current dependencies


def reconcile_installed_packages(skip_empty=False):
    """Sync installed packages and pyproject.toml using in-memory state."""
    debug("Reconciling installed packages and pyproject.toml...")
    initialize_pyproject()

    # Get currently installed packages
    current_packages = get_installed_packages()

    # Safeguard: Skip reconciliation if installed packages list is unexpectedly empty
    if not current_packages:
        debug("No installed packages detected. Skipping reconciliation to prevent data loss.")
        return

    # Load existing dependencies from pyproject.toml
    with open(PYPROJECT_FILE, "r") as f:
        project_data = toml.load(f)

    dependencies = project_data.setdefault("tool", {}).setdefault("custom", {}).setdefault("dependencies", {})

    # Update the global state if it's empty (first-time setup)
    global global_dependencies_state
    if not global_dependencies_state:
        global_dependencies_state = dependencies.copy()

    # Sync in-memory state with current packages
    for package, version in current_packages.items():
        if global_dependencies_state.get(package) != version:
            debug(f"Updating {package} to version {version} in memory.")
            global_dependencies_state[package] = version

    # Remove stale dependencies from the in-memory state
    to_remove = [pkg for pkg in global_dependencies_state if pkg not in current_packages]
    for package in to_remove:
        debug(f"Removing {package} from in-memory state.")
        del global_dependencies_state[package]

    # Write the in-memory state back to pyproject.toml
    dependencies.clear()
    dependencies.update(global_dependencies_state)

    with file_lock:
        with open(PYPROJECT_FILE, "w") as f:
            toml.dump(project_data, f)

    debug("Reconciliation complete.")
    debug_toml_state()


class InstallEventHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.shutdown_flag = False

    def on_any_event(self, event):
        if self.shutdown_flag:
            debug("Skipping event handling due to shutdown.")
            return

        if event.event_type in {"created", "modified", "deleted"}:
            debug(f"Event detected: {event.event_type} on {event.src_path}")
            reconcile_installed_packages()


def monitor_virtualenv():
    """Monitor site-packages directory and pyproject.toml for changes."""
    if not is_virtual_env():
        print("Error: This script must be run inside a virtual environment.")
        sys.exit(1)

    site_packages_dir = sysconfig.get_paths()["purelib"]
    debug(f"Monitoring {site_packages_dir} and {PYPROJECT_FILE} for changes...")

    event_handler = InstallEventHandler()
    observer = Observer()

    # Monitor site-packages and pyproject.toml
    observer.schedule(event_handler, site_packages_dir, recursive=True)
    observer.schedule(event_handler, ".", recursive=False)

    observer.start()
    try:
        print("Monitoring started. Press Ctrl+C to stop.")
        while observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitoring...")
        event_handler.shutdown_flag = True
        observer.stop()
    finally:
        observer.join()
        print("Monitoring stopped. No changes made during shutdown.")


def monitor():
    """Command for monitoring the virtual environment."""
    debug("Starting the monitoring process...")
    monitor_virtualenv()


def install_dependencies_from_pyproject():
    """Install all dependencies listed in pyproject.toml."""
    if not os.path.exists(PYPROJECT_FILE):
        print("Error: pyproject.toml does not exist. Cannot install dependencies.")
        return

    with open(PYPROJECT_FILE, "r") as f:
        project_data = toml.load(f)

    dependencies = project_data.get("tool", {}).get("custom", {}).get("dependencies", {})
    if not dependencies:
        print("No dependencies listed in pyproject.toml.")
        return

    print("Installing dependencies from pyproject.toml...")
    for package, version in dependencies.items():
        pkg_str = f"{package}=={version}" if version else package
        print(f"Installing {pkg_str}...")
        subprocess.run([sys.executable, "-m", "pip", "install", pkg_str])
    print("Dependencies installation complete.")


def install():
    """Command for installing dependencies."""
    install_dependencies_from_pyproject()

def clear_dependencies():
    """Clear all dependencies listed in pyproject.toml."""
    if not os.path.exists(PYPROJECT_FILE):
        print(f"Error: {PYPROJECT_FILE} does not exist. Nothing to clear.")
        return

    with open(PYPROJECT_FILE, "r") as f:
        project_data = toml.load(f)

    # Navigate to the dependencies section
    dependencies = project_data.get("tool", {}).get("custom", {}).get("dependencies", None)

    if dependencies is None or not dependencies:
        print("No dependencies to clear.")
        return

    # Clear the dependencies dictionary
    project_data["tool"]["custom"]["dependencies"] = {}

    # Save changes to pyproject.toml
    with file_lock:
        with open(PYPROJECT_FILE, "w") as f:
            toml.dump(project_data, f)

    print("All dependencies cleared from pyproject.toml.")
    debug_toml_state()


def clear():
    """Command for clearing dependencies."""
    clear_dependencies()


def main():
    if len(sys.argv) < 2:
        print("Usage: pip-wrapper [create|monitor|install|clear]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "create":
        create_pyproject()
    elif command == "monitor":
        monitor()
    elif command == "install":
        install()
    elif command == "clear":
        clear()
    else:
        print(f"Unknown command: {command}")
        print("Usage: pip-wrapper [create|monitor|install|clear]")
        sys.exit(1)


if __name__ == "__main__":
    main()
