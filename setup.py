from setuptools import setup, find_packages
from pathlib import Path
from pystanssh.__init__ import __version__

base_path = Path(__file__).parent

readme = (base_path / 'README.md').read_text()

setup(
    name='pystanssh',
    version=__version__,
    description='PyStan I/O between servers with ssh',
    url='https://github.com/jhand1993/pystanssh',
    author='Jared Hand',
    author_email='jared.hand1993@gmail.com',
    license='GPL V3',
    packages=find_packages(exclude=('tests')),
    zip_safe=False,
    install_requires=['paramiko', 'numpy'],
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True
)