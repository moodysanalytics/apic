import os

import setuptools

REQUIRED = ['pyhocon>=0.3.54', 'requests>=2.23.0', 'PyJWT>=1.7.1']

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(BASE_DIR, 'api_client', '__version__.py'), 'r') as file:
    exec(file.read(), about)

with open(os.path.join(BASE_DIR, 'README.md'), encoding='utf-8') as file:
    long_description = '\n' + file.read()

setuptools.setup(name=about['__name__'],
                 version=about['__version__'],
                 description=about['__description__'],
                 long_description=long_description,
                 author=about['__author__'],
                 author_email=about['__author_email__'],
                 python_requires='>=3.6',
                 packages=['api_client'],
                 install_requires=REQUIRED)
