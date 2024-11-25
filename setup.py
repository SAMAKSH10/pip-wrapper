from setuptools import setup, find_packages

# Read the README.md file for the long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A custom pip wrapper to manage dependencies and update pyproject.toml."

setup(
    name="pip-wrapper",
    version="0.1.0",
    description="A custom pip wrapper to manage dependencies and update pyproject.toml.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SAMAKSH10/pip-wrapper.git",
    author="Samaksh",
    author_email="samakshsinghal5@gmail.com",
    license="MIT",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "pip-wrapper=pip_wrapper.cli:main",
        ]
    },
    install_requires=[
        "toml>=0.10.0",  # TOML support for pyproject
    ],
    extras_require={
        "dev": ["pytest", "flake8"],
        "docs": ["sphinx", "sphinx_rtd_theme"],
    },
    setup_requires=["wheel", "setuptools"],
    tests_require=["pytest"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    keywords="pip wrapper pyproject.toml dependency management",
    include_package_data=True,
)
