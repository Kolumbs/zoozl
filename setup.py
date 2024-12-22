"""Build for zoozl services."""

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

    setuptools.setup(
        name="zoozl",
        version="0.1.6",
        author="Juris Kaminskis",
        author_email="juris@kolumbs.net",
        description="Zoozl services for chatbots",
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/Kolumbs/zoozl",
        install_requires=[
            "aiosmtpd==1.4.6,<2",
            "membank==0.5.3",
            "scipy>=1.14.0,<2",
            "openai>=1.43.1,<2",
            "rapidfuzz>=2.11.1,<3",
            "slack-sdk>=3.33.1,<4",
        ],
        python_requires=">=3.11,<4",
    )
