from setuptools import setup
from os import path

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
        name='pysaucenao',  # How you named your package folder (MyLib)
        packages=['pysaucenao'],  # Chose the same as "name"
        version='1.1.1',  # Start with a small number and increase it with every change you make
        license='gpl-3.0',  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
        description='PySauceNao is an unofficial asynchronous library for the SauceNao API. It supports lookups via URL or from the local filesystem.',  # Give a short description about your library
        long_description=long_description,
        long_description_content_type='text/markdown',
        author='Makoto',  # Type in your name
        author_email='makoto+github@taiga.sh',  # Type in your E-Mail
        url='https://github.com/FujiMakoto/pysaucenao',  # Provide either the link to your github or to your website
        download_url='https://github.com/FujiMakoto/pysaucenao/archive/1.1.1.tar.gz',
        keywords=['saucenao', 'anime', 'artwork'],  # Keywords that define your package best
        install_requires=[
            'aiohttp',
        ],
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Topic :: Multimedia :: Graphics',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',  # Again, pick a license
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8'
        ],
)
