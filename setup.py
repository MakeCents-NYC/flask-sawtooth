"""
Flask-Sawtooth
-------------

A Sawtooth utlity library as a Flask extension.
"""
from setuptools import setup


setup(
    name='Flask-Sawtooth',
    version='0.2',
    license='GPLv2',
    author='Thomas Veale',
    author_email='tveale@mymakecents.com',
    description='A Sawtooth utlity library as a Flask extension.',
    long_description=__doc__,
    url='https://github.com/MakeCents-NYC/flask-sawtooth',
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'sawtooth_sdk',
        'sawtooth_signing',
        'requests',
        'cbor2'
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
