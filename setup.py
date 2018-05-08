"""
Flask-Sawtooth
-------------

This is the description for that library
"""
from setuptools import setup


setup(
    name='Flask-Sawtooth',
    version='0.2',
    url='',
    license='GPLv2',
    author='Thomas Veale',
    author_email='tveale@mymakecents.com',
    description='Utility library for using Hyperledger Sawtooth-Lake Rest-API',
    long_description=__doc__,
    py_modules=['sawtooth'],
    # if you would be using a package instead use packages instead
    # of py_modules:
    # packages=['flask_sqlite3'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'sawtooth_sdk',
        'sawtooth_signing'
    ],
    classifiers=[
        'Environment :: Server',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPLv2 License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Blockchain :: Protobuf :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
