import os

from setuptools import setup


__version__ = ''
version_py_file = os.path.join(os.path.dirname(__file__), 'lambdex', 'version.py')
with open(version_py_file) as version_py:
  exec(compile(version_py.read(), version_py_file, 'exec'))


setup(
  name = 'lambdex',
  version = __version__,
  description = 'lambdex is a python environment packager for aws lambda',
  zip_safe = True,
  entry_points = {
    'console_scripts': [
      'lambdex = lambdex.bin.lambdex:main',
    ]
  },
  packages = [
    'lambdex',
    'lambdex.bin',
  ],
  install_requires = [
    'pex==1.1.10',
  ]
)
