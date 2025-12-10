#!/usr/bin/env python
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="level-prediction",
    version="1.0.0",
    author="IDSS Flood Prediction Team",
    description="Self-contained flood level prediction for St. Louis region",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alobo01/mai-idss-flood",
    packages=find_packages(include=["level_prediction", "level_prediction.*"]),
    package_data={
        "level_prediction": [
            "models/L1d/*.json",
            "models/L1d/*.pkl", 
            "models/L1d/*.h5",
            "models/L2d/*.json",
            "models/L2d/*.pkl",
            "models/L2d/*.h5",
            "models/L3d/*.json",
            "models/L3d/*.pkl",
            "models/L3d/*.h5",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "xgboost>=1.7.6",
        "tensorflow>=2.15.0",
        "joblib>=1.3.0",
        "scipy>=1.11.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
)
