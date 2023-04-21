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

# requirements for the utility functions which produce 
extract_requirements = [
    "rr.nhs @ git+ssh://git@github.com/renalreg/rr-nhs.git",
    "git+ssh://git@github.com/renalreg/cohort_extract.git#egg=ukrdc_cohort_extract",
    "ukrdc.database @ git+ssh://git@github.com/renalreg/ukrdc_database.git",
    "uuid",
    "ukrdc_schema",
    "pyxb"
]

setup(
    name="ukrr_models",
    version="0.0.4",
    author="UK Renal Registry",
    author_email="rrsystems@renalregistry.nhs.uk",
    url="https://www.renalreg.org/",
    packages=["ukrr_models"],
    install_requires=[
        "sqlalchemy"
    ],
    zip_safe=True,
    tests_require=test_deps,
    extras_require={
        "test": test_deps,
        "extract": extract_requirements
    },
)
