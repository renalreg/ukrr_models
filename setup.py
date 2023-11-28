from setuptools import setup
import re

setup(
    name="ukrr_models",
    version="1.1.0",
    author="UK Renal Registry",
    author_email="rrsystems@renalregistry.nhs.uk",
    url="https://www.renalreg.org/",
    packages=["ukrr_models"],
    install_requires=["sqlalchemy"],
    zip_safe=True,
)
