"""Setup configuration for paralax-webframework."""

from setuptools import setup, find_packages

setup(
    package_dir={"": "."},
    packages=find_packages(include=["src", "src.*"]),
    include_package_data=True,
)
