"""Build for zoozl services."""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

    setuptools.setup(
        name="zoozl",
        version="0.0.24",
        author="Juris Kaminskis",
        author_email="juris@kolumbs.net",
        description="Zoozl services for chatbots",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/Kolumbs/zoozl",
        install_requires=[
            "membank>=0.5.2",
            "scipy==1.14.0",
            "openai==1.38.0",
            "rapidfuzz==2.11.1"
        ],
        python_requires=">=3.11",
    )
