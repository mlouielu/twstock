try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

tests_require = ['pytest', 'Sphinx']

long_description = """
twstock is a minimum re-implement of grs
"""


setup(name="twstock",
      description="twstock - Taiwan Stock Data",
      long_description=long_description,
      license="MIT",
      version="0.1",
      author="Louie Lu",
      author_email="git@louie.lu",
      maintainer="Louie LU",
      maintainer_email="git@louie.lu",
      url="https://github.com/mlouielu/twstock",
      packages=['twstock'],
      tests_require=tests_require,
      extras_require={
          'test': tests_require,
      },
      classifiers=[
          'Programming Language :: Python :: 3',
      ]
      )
