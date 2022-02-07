from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='TopasOpt',
    url='https://github.sydney.edu.au/Image-X/TopasBayesOpt',
    packages=find_packages(include=['TopasOpt', 'TopasOpt.*']),
    author='Brendan Whelan',
    author_email="bwheelz360@gmail.com",
    description='Inverse optimisation for topas Monte Carlo',
    long_description=long_description,
    long_description_content_type='text/markdown',
    download_url='https://github.com/fmfn/BayesianOptimization/tarball/0.6',
    install_requires=[
        "numpy >= 1.9.0",
        "scipy >= 0.14.0",
        "scikit-learn >= 0.18.0",
        "bayesian-optimization",
        "matplotlib",
        "jsonpickle",
        "topas2numpy"
    ],
    setup_requires=['pytest-runner', 'flake8'],
    tests_require=['pytest'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
    ]
)

