import setuptools
import os
import re

def get_version(package_init_file):
    """Reads the version string from a package's __init__.py file."""
    with open(package_init_file, 'r') as f:
        content = f.read()
    match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find version string.")

# Define the path to the __init__.py file
init_py_path = os.path.join(os.path.dirname(__file__), 'mapvis', '__init__.py')

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='mapvis',
    version=get_version(init_py_path),
    author='AI Agent',
    author_email='ai@example.com',
    description='A Python package for visualizing cell type and feature mappings.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/example/mapvis',  # Placeholder URL
    packages=setuptools.find_packages(),
    install_requires=[
        'pandas>=1.0',
        'matplotlib>=3.0'  # Used in utils.py for default color generation
    ],
    classifiers=[
        'Development Status :: 3 - Alpha', # Starting point, can be updated
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License', # Assuming MIT License
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.7',
)
