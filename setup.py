from setuptools import setup, find_packages

setup(
    name='experiments_utils',
    version='2.1.0',
    author='Cezary Maszczyk',
    author_email='cezary.maszczyk@gmail.com',
    description='Microframework to speed up writing scientific experiment code',
    packages=find_packages(),
    install_requires=[
        'multiprocess==0.70.13',
    ],
)
