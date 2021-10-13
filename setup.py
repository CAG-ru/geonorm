import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='geonorm',
    version='1.1',
    author='INID',
    author_email='m.vedenkov@data-in.ru',
    description='Testing installation of Package',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/CAG-ru/geonorm',
    project_urls={
        "Bug Tracker": "https://github.com/CAG-ru/geonorm/issues"
    },
    license='Apache',
    package_data={'geonorm': ['geonorm/*.json']},
    include_package_data=True,
    packages=['geonorm', 'geonorm.nat_new', 'geonorm.nat_new.grammars'],
    install_requires=['requests', 'pandas', 'natasha', 'sklearn', 'thefuzz', 'python-Levenshtein'],
)