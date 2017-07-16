from setuptools import setup

setup(
    name='undoable_transaction',
    version='0.1.0',
    packages=['undoable_transaction'],
    zip_safe=True,
    author='Nicolas Bigot',
    author_email='nicbigot@gmail.com',
    description='Undoable transaction',
    long_description='Undoable transaction',
    license='MIT',
    keywords=['undo', 'undoable', 'transaction'],
    url='https://github.com/nbigot/python-undoable-transaction',
    download_url='https://github.com/nbigot/python-undoable-transaction/archive/0.1.0.tar.gz',
    platforms='any',
    tests_require=[
        'pytest>=2.5.0'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
