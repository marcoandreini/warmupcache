#!/usr/bin/env python

from setuptools import setup, find_packages

__author__ = 'Marco Andreini'
__version__ = '0.1.0'
__contact__ = 'marco.andreini@gmail.com'
__url__ = 'https://github.com/marcoandreini/warmupcache'
__license__ = 'GPLv3'


setup(name='warmupcache',
      version=__version__,
      description='Warm up cache from sitemap',
      author=__author__,
      author_email=__contact__,
      url=__url__,
      license=__license__,
      packages=find_packages(),
      entry_points='''
        [console_scripts]
        warmupcache=warmupcache.main:cli
      ''',
      install_requires=['requests', 'progressbar'],
      classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
      ]
     )
