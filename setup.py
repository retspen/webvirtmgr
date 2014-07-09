import os
from setuptools import setup, find_packages


__version__ = "4.8.4"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    # package name in pypi
    name='webvirtmgr',
    # extract version from module.
    version=__version__,
    description="WebVirtMgr panel for manage virtual machine",
    long_description=read('README.rst'),
    classifiers=[],
    keywords='',
    author='Aktivcorp, LLC',
    author_email='anatoliy.guskov@gmail.com',
    url='http://retspen.github.io',
    license='Apache Licence, Version 2.0.',
    # include all packages in the egg, except the test package.
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    # for avoiding conflict have one namespace for all webvirtmgr related eggs.
    namespace_packages=[],
    # include non python files
    include_package_data=True,
    zip_safe=False,
    # specify dependencies
    install_requires=[
        'setuptools',
        'django>=1.5.5',
        'gunicorn>=18.0',
        'lockfile>=0.9',
    ],
    # mark test target to require extras.
    extras_require = {
        'ldap':  ["django-auth-ldap>=1.2.0"]
    },
    scripts=[
        'manage.py',
    ],
)
