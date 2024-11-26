# pip-wrapper

`pip-wrapper` is a lightweight Python tool designed to streamline dependency management in Python projects. It provides commands to automatically sync installed packages with a `pyproject.toml` file, monitor your virtual environment for changes, and manage dependencies with ease.

--------------------------------------------------------------

## Features

- **Automated Dependency Tracking**: Keeps the `pyproject.toml` file in sync with installed packages.
- **Monitoring**: Watches for changes in the environment and updates dependencies in real-time.
- **Centralized Installation**: Install all dependencies from the `pyproject.toml` file.
- **Clear Command**: Easily clear all dependencies from the `pyproject.toml` file.

---

## Installation

To install `pip-wrapper`, run:

**pip install pip-wrapper**

## Commands:

1. Create pyproject.toml:
Initialize a new pyproject.toml file with a default structure.

**pip-wrapper create**

2. Monitor Environment:
Start monitoring your virtual environment for changes and automatically update the pyproject.toml file.

**pip-wrapper monitor**

3. Install Dependencies :
Install all dependencies listed in the pyproject.toml file.

**pip-wrapper install**

4. Clear Dependencies :
Clear all dependencies from the pyproject.toml file.

**pip-wrapper clear**

-------------------------------------------------------------

## Usage Instructions

1. Start by creating a pyproject.toml file in your project directory:

`pip-wrapper create`

2. Monitor changes in your virtual environment to keep your pyproject.toml updated:

`pip-wrapper monitor`

3. Install dependencies from your pyproject.toml in a new environment:

`pip-wrapper install`

4. Clear dependencies if needed:

`pip-wrapper clear`

------------------------------------------------------------------


## Why Use `pip-wrapper`?

-**Simplifies dependency management**.
-**Avoids manual updates to the `pyproject.toml` file**.
-**Ensures your dependencies are always in sync with your environment**.
