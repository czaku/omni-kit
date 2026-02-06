from setuptools import setup, find_packages

setup(
    name="wickit",
    version="0.3.0",
    description="Wicked utilities for Python: hideaway, knobs, alter-egos, synapse, pulse, blueprint, humanize, landscape, vault, shuffle, flavour, and more",
    packages=find_packages(where="src", include=["wickit*"]),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[],
)
