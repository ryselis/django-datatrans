#!/usr/bin/env python3
from setuptools import (setup, find_packages)
import datatrans3

LONG_DESCRIPTION = """

"""

setup(name='django-datatrans3',
      version=datatrans3.__version__,
      description='Translate Django models without changing anything to existing applications and their '
                  'underlying database.',
      long_description=LONG_DESCRIPTION,
      author='Karolis Ryselis, Esperonus',
      author_email='karolis@esperonus.com',
      url='https://github.com/ryselis/django-datatrans3',
      license='LICENSE',
      packages=find_packages(),

      include_package_data=True,
      zip_safe=False,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Topic :: Software Development :: Internationalization',
      ],
      install_requires=[
          'Django>=1.8.13',
      ]
)

