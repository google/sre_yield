from setuptools import setup, find_packages
import os.path

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

version = '1.0'

setup(name='sre_yield',
      version=version,
      description='Expands a regular expression to its possible matches',
      long_description=README,
      classifiers = [
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: OS Independent',
      ],
      keywords='',
      author='Alex Perry',
      author_email='alex.perry@google.com',
      url='https://github.com/google/sre_yield',
      license='Apache',
      packages=find_packages('.'),
      install_requires=[],
      entry_points={
        'console_scripts': [
            'demo_sre_yield=sre_yield:main',
        ],
      },
      test_suite='nose.collector', # doesn't find doctests though
      tests_require=['nose'],
)
