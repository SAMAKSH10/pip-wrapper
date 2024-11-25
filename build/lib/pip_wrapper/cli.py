import subprocess
import sys
import os
import toml
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PYPROJECT_FILE = "pyproject.toml"
LOG_FILE = "installed_packages.json"

# Check if we are in a virtual environment
def is_virtual_env():
    """Check if the script is running in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def load_log():
    """Load existing log file or initialize a new one."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {"installations": []}

def save_log(log_data):
    """Save log data to the log file."""
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
    if not os.path.exists(PYPROJECT_FILE):
        print("Initializing pyproject.toml...")
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
        print("Created pyproject.toml.")
    else:
        print("pyproject.toml already exists.")

def update_pyproject(package, version):
    """Update the pyproject.toml file with a new package and version."""
    if not os.path.exists(PYPROJECT_FILE):
        initialize_pyproject()

    with open(PYPROJECT_FILE, "r") as f:
        project_data = toml.load(f)

    dependencies = project_data.setdefault("tool", {}).setdefault("custom", {}).setdefault("dependencies", {})

    # Check if the package is already listed
    if package in dependencies:
        if dependencies[package] == version:
            print(f"{package}=={version} is already listed in pyproject.toml.")
        else:
            print(f"Updating {package} version from {dependencies[package]} to {version}.")
            dependencies[package] = version
    else:
        print(f"Adding {package}=={version} to pyproject.toml.")
        dependencies[package] = version

    with open(PYPROJECT_FILE, "w") as f:
        toml.dump(project_data, f)

def get_installed_version(package):
    """Retrieve the installed version of a package using pip show."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", package],
        capture_output=True,
        text=True
    )
    for line in result.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":")[1].strip()
    return None

# Define Watchdog Handler for Monitoring Installations
class InstallEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".dist-info"):
            package_name = os.path.basename(os.path.dirname(event.src_path))
            package_version = get_installed_version(package_name)
            if package_version:
                print(f"New package installed: {package_name}=={package_version}")
                update_pyproject(package_name, package_version)

def monitor_virtualenv():
    """Monitor site-packages directory for new installations."""
    if not is_virtual_env():
        print("Warning: You are not in a virtual environment. To effectively track dependencies, please activate a virtual environment.")
        sys.exit(1)

    site_packages_dir = os.path.join(sys.prefix, 'lib', 'python' + sys.version[:3], 'site-packages')
    print(f"Monitoring {site_packages_dir} for new package installations...")
    
    event_handler = InstallEventHandler()
    observer = Observer()
    observer.schedule(event_handler, site_packages_dir, recursive=True)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    if not is_virtual_env():
        print("Warning: You are not in a virtual environment. To effectively track dependencies, please activate a virtual environment.")
        sys.exit(1)

    monitor_virtualenv()

if __name__ == "__main__":
    main()
