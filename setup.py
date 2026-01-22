from setuptools import setup, find_packages

setup(
    name="wickit",
    version="0.1.0",
    description="Wicked utilities for Python",
    packages=find_packages(where="src", include=["wickit*"]),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[],
)
