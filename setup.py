from setuptools import setup, find_packages

setup(
    name="omni-kit",
    version="0.1.0",
    description="Shared libraries for AI products",
    packages=find_packages(where="src", include=["local_stash*", "knobsy*", "alter_egos*", "sync_bridge*"]),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[],
)
