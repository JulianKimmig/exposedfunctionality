from setuptools import setup, find_packages
import exposedfunctionality

from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="exposedfunctionality",
    version=exposedfunctionality.__version__,
    description="tool to expose functionalities to multiple tools",
    long_description=long_description,
    author="Julian Kimmig",
    author_email="julian.kimmig@linkdlab.de",
    packages=find_packages(),  # Update with your package name
    install_requires=["pyyaml"],
    # github
    url="https://github.com/JulianKimmig/ExposedFunctionality",
    # license
    license="MIT",
    long_description_content_type="text/markdown",
    # classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",  # Adjust to your Python version
    ],
)
