from setuptools import setup, find_packages

setup(
    name='behest',
    version='0.0.1',
    description='A testing focused opinionated wrapper for requests.',
    author='dwalleck and jidar',
    author_email='core.machinarum@gmail.com',
    install_requires=['requests', 'six'],
    packages=find_packages(exclude=('tests*', 'docs')),
    package_dir={'behest': 'behest'},
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ))
