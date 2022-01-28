from setuptools import setup, find_packages


def read(file_name):
    with open(file_name) as fp:
        content = fp.read()
    return content


setup(
    name='apispec-plugins',
    version='0.0.1',
    description='Plugins for apispec.',
    long_description=read('README.md'),
    author='Renato Damas',
    author_email='rena2damas@gmail.com',
    url='https://github.com/rena2damas/apispec-plugins',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=["apispec>=2.0.0"],
    python_requires='>=3.6',
    license='MIT',
    zip_safe=False,
    keywords=[
        'apispec',
        'plugins',
        'swagger',
        'openapi',
        'specification',
        'documentation',
        'spec',
        'rest',
        'api',
        'web',
        'flask',
        'frameworks',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    test_suite='tests',
    project_urls={
        'Issues': 'https://github.com/rena2damas/apispec-plugins/issues'
    },
)
