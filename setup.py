from setuptools import find_packages, setup

setup(
    name='experiments_utils',
    version='3.0.0',
    author='Cezary Maszczyk',
    author_email='cezary.maszczyk@gmail.com',
    description='Microframework to speed up writing scientific experiment code',
    packages=find_packages(),
    install_requires=[
        'multiprocess==0.70.13',
        'dill==0.3.8',
    ],
)
