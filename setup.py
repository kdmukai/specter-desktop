from setuptools import setup, find_packages
from glob import glob


setup(
    name="specter-desktop", 
    packages=find_packages('specter'),
    package_dir={'': 'src/specter'}
)