import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


requires = [
    'pyramid',
    'pyramid_jinja2',
    'pyramid_debugtoolbar',
    'waitress',
    'lxml',
    'logsna',
    'wheel',
    'distribute',
]

test_requires = [
    'fudge',
    'httpretty',
    'pytest-cov',
    'pytest',
]

setup(name='belt',
      version='0.3.1',
      description='belt',
      license='BSD',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "License :: OSI Approved :: BSD License",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='Rob Berry',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='belt',
      install_requires=requires,
      tests_require=test_requires,
      cmdclass={'test': PyTest},
      entry_points="""\
      [paste.app_factory]
      main = belt:main
      """,
      )
