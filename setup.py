"""
Flask-Sawtooth
-------------

A Sawtooth utility library as a Flask extension.
"""
from setuptools import setup


setup(
    name='Flask-Sawtooth',
    version='0.3.0',
    license='GPLv2',
    author='Thomas Veale, Bo Yao',
    author_email='tveale@mymakecents.com, byao@mymakecents.com',
    description='A Sawtooth utlity library as a Flask extension.',
    long_description=__doc__,
    url='https://github.com/MakeCents-NYC/flask-sawtooth',
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    packages=['flask_sawtooth'],
    install_requires=[
        'Flask',
        'sawtooth_sdk>=1.0, <1.1',
        'sawtooth_signing>=1.0, <1.1',
        'requests',
        'cbor2',
        'pyzmq'
    ],
    tests_require=[

    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
