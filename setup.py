from setuptools import setup
import re

test_deps = [
    "coverage2clover==1.4.0",
    "flake8",
    "flake8-junit-report",
    "mypy",
    "pytest-cov>=2.10",
    "pytest>=6.1",
    "tox",
    "types-setuptools",
    "unittest-xml-reporting",
]

setup(
    name="ukrr_models",
    version="0.0.2",
    author="UK Renal Registry",
    author_email="rrsystems@renalregistry.nhs.uk",
    url="https://www.renalreg.org/",
    packages=["ukrr_models"],
    install_requires=[],
    zip_safe=True,
    tests_require=test_deps,
    extras_require={
        "test": test_deps,
    },
)
