import subprocess
import sys
import os
import toml
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sysconfig
import threading
import time

PYPROJECT_FILE = "pyproject.toml"
LOG_FILE = "installed_packages.json"


def debug(message):
    """Print debug messages for better traceability."""
    print(f"[DEBUG] {message}")


# Check if we are in a virtual environment
def is_virtual_env():
    """Check if the script is running in a virtual environment."""
    debug(f"sys.prefix: {sys.prefix}")
    debug(f"sys.base_prefix: {sys.base_prefix}")
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def load_log():
    """Load existing log file or initialize a new one."""
    debug("Loading log file...")
    if os.path.exists(LOG_FILE):
        debug(f"Log file found: {LOG_FILE}")
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    debug("No log file found. Initializing new log.")
    return {"installations": []}


def save_log(log_data):
    """Save log data to the log file."""
    debug(f"Saving log data to {LOG_FILE}...")
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=4)


def track_installations(package_name, package_version):
    """Log installed package with version and timestamp."""
    log_data = load_log()
    log_entry = {
        "package": package_name,
        "version": package_version,
        "timestamp": datetime.now().isoformat()
    }
    log_data["installations"].append(log_entry)
    save_log(log_data)


def initialize_pyproject():
    """Initialize pyproject.toml if it doesn't exist."""
    debug("Checking for pyproject.toml...")
    if not os.path.exists(PYPROJECT_FILE):
        debug("Creating pyproject.toml...")
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
        debug("Created pyproject.toml.")
    else:
        debug("pyproject.toml already exists.")


def update_pyproject(package, version):
    """Update the pyproject.toml file with a new package and version."""
    initialize_pyproject()

    with open(PYPROJECT_FILE, "r") as f:
        project_data = toml.load(f)

    dependencies = project_data.setdefault("tool", {}).setdefault("custom", {}).setdefault("dependencies", {})

    # Check if the package is already listed
    if package in dependencies:
        if dependencies[package] == version:
            debug(f"{package}=={version} is already listed in pyproject.toml.")
        else:
            debug(f"Updating {package} version from {dependencies[package]} to {version}.")
            dependencies[package] = version
    else:
        debug(f"Adding {package}=={version} to pyproject.toml.")
        dependencies[package] = version

    with open(PYPROJECT_FILE, "w") as f:
        toml.dump(project_data, f)


def get_installed_packages():
    """Retrieve all installed packages using pip freeze."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True
    )
    packages = {}
    for line in result.stdout.splitlines():
        if "==" in line:
            name, version = line.split("==")
            packages[name] = version
    return packages


def reconcile_installed_packages():
    """Check for new or removed packages and update pyproject.toml."""
    debug("Reconciling installed packages...")
    
    # Ensure pyproject.toml exists
    initialize_pyproject()
    
    current_packages = get_installed_packages()
    with open(PYPROJECT_FILE, "r") as f:
        project_data = toml.load(f)

    dependencies = project_data.setdefault("tool", {}).setdefault("custom", {}).setdefault("dependencies", {})

    # Add or update packages
    for package, version in current_packages.items():
        if package not in dependencies or dependencies[package] != version:
            debug(f"Adding/Updating {package}=={version} in pyproject.toml.")
            dependencies[package] = version

    # Remove uninstalled packages
    to_remove = [pkg for pkg in dependencies if pkg not in current_packages]
    for pkg in to_remove:
        debug(f"Removing {pkg} from pyproject.toml.")
        dependencies.pop(pkg)

    with open(PYPROJECT_FILE, "w") as f:
        toml.dump(project_data, f)
    debug("Reconciliation complete.")


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


class InstallEventHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        """Handle any file system events."""
        debug("Filesystem change detected. Triggering reconciliation...")
        reconcile_installed_packages()


def monitor_virtualenv():
    """Monitor site-packages directory for changes."""
    if not is_virtual_env():
        print("Error: This script must be run inside a virtual environment.")
        sys.exit(1)

    site_packages_dir = sysconfig.get_paths()["purelib"]
    debug(f"Monitoring {site_packages_dir} for changes...")

    event_handler = InstallEventHandler()
    observer = Observer()
    observer.schedule(event_handler, site_packages_dir, recursive=True)
    observer.start()

    def periodic_reconcile():
        while True:
            time.sleep(10)
            reconcile_installed_packages()

    # Start periodic reconciliation in a separate thread
    threading.Thread(target=periodic_reconcile, daemon=True).start()

    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main():
    if not is_virtual_env():
        print("Error: This script must be run inside a virtual environment.")
        sys.exit(1)

    print("1. Monitor environment for changes")
    print("2. Install dependencies from pyproject.toml")
    choice = input("Select an option (1 or 2): \n").strip()

    if choice == "1":
        debug("Starting the monitoring process...")
        monitor_virtualenv()
    elif choice == "2":
        install_dependencies_from_pyproject()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
