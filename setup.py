#!/usr/bin/env python3
"""Setup configuration for skyink package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="skyink",
    version="1.0.7",
    author="skyink contributors",
    author_email="info@farhangnaderi.com",
    description="Convert text to PX4 drone flight paths using Hershey stroke fonts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/farhangnaderi/skyink",
    project_urls={
        "Bug Reports": "https://github.com/farhangnaderi/skyink/issues",
        "Source": "https://github.com/farhangnaderi/skyink",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["templates/*.html", "static/*"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Hershey-Fonts>=0.2.0",
        "pymap3d>=3.0.0",
        "simplification>=0.7.0",
        "numpy>=1.24.0",
        "flask>=3.0.0",
        "folium>=0.15.0",
    ],
    extras_require={
        "gui": [
            "flask>=3.0.0",
            "folium>=0.15.0",
        ],
        "server": [
            "flask>=3.0.0",
            "folium>=0.15.0",
            "gunicorn>=21.2.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "skyink=skyink.text_to_drone_path:main",
            "skyink-gui=skyink.gui_server:main",
        ],
    },
    keywords="drone px4 mavlink qgroundcontrol mission-planning path-planning fonts trajectory",
    license="MIT",
    zip_safe=False,
)
