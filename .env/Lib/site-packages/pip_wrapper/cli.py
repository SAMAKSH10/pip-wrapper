import subprocess
import sys
import os
import toml

PYPROJECT_FILE = "pyproject.toml"

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
    dependencies[package] = version

    with open(PYPROJECT_FILE, "w") as f:
        toml.dump(project_data, f)
    
    print(f"Updated pyproject.toml: {package}=={version}")

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

def install_dependencies_from_pyproject():
    
    """Install all dependencies listed in pyproject.toml."""
    
    if not os.path.exists(PYPROJECT_FILE):
        print("Error: pyproject.toml not found.")
        sys.exit(1)
    
    with open(PYPROJECT_FILE, "r") as f:
        project_data = toml.load(f)
    
    dependencies = project_data.get("tool", {}).get("custom", {}).get("dependencies", {})
    if not dependencies:
        print("No dependencies found in pyproject.toml.")
        return
    
    print("Installing dependencies from pyproject.toml...")
    for package, version in dependencies.items():
        package_spec = f"{package}=={version}" if version else package
        print(f"Installing {package_spec}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package_spec])

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  pip install <package>          - Install a package and update pyproject.toml.")
        print("  pip install-all                - Install all dependencies from pyproject.toml.")
        print("  pip <other pip commands>       - Pass through to pip.")
        sys.exit(1)

    if sys.argv[1] == "install-all":
        install_dependencies_from_pyproject()
    elif sys.argv[1] == "install" and len(sys.argv) > 2:
        packages = sys.argv[2:]
        # Install packages using pip
        subprocess.run([sys.executable, "-m", "pip"] + sys.argv[1:])
        
        # Update pyproject.toml
        for package in packages:
            # Handle package version pinning (e.g., flask==2.3.3)
            if "==" in package:
                pkg_name, pkg_version = package.split("==")
            else:
                pkg_name = package
                pkg_version = get_installed_version(pkg_name)
            
            if pkg_version:
                update_pyproject(pkg_name, pkg_version)
            else:
                print(f"Warning: Could not determine version for {pkg_name}")
    else:
        # Forward all other pip commands to the real pip
        subprocess.run([sys.executable, "-m", "pip"] + sys.argv[1:])

if __name__ == "__main__":
    main()
