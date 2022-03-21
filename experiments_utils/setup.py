from setuptools import setup, find_packages

setup(
    name='experiments_utils',
    version='1.0.0',
    author='Cezary Maszczyk',
    author_email='cmaszczyk@polsl.com',
    description='',
    packages=find_packages(),
    install_requires=[
        'numpy==1.19.5',
        'pandas==1.2.1',
    ],
)
