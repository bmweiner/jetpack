import sys
from setuptools import setup

from jetpack import __version__
from jetpack import __doc__ as description

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    with open('README.md') as file:
        long_description = file.read()

setup(name='jetpack',
      version=__version__,
      author='Benjamin Weiner',
      author_email='bmweiner@users.noreply.github.com',
      url='https://github.com/bmweiner/jetpack',
      description=description,
      long_description=long_description,
      classifiers = [
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          ],
      platforms=['py27', 'py35'],
      packages=['jetpack'],
      scripts =['scripts/jetpack'],
      install_requires=['six', 'pystache'],
      setup_requires=[] + pytest_runner,
      tests_require=['pytest'])
