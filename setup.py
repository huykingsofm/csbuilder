import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
    long_description += "\n"


with open("CHANGELOG.md", "r", encoding="utf-8") as fh:
    long_description += fh.read()


setuptools.setup(
    name="csbuilder",
    version="0.0.2",
    author="huykingsofm",
    author_email="huykingsofm@gmail.com",
    description="The Python framework which is used to build complex Client-Server applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/huykingsofm/csbuilder",
    project_urls={
        "Bug Tracker": "https://github.com/huykingsofm/csbuilder/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7.1",
    install_requires=["hks_pynetwork>=0.0.4", "hks_pylib>=0.0.7", "hkserror>=0.0.2"],
    setup_requires=["pytest-runner==4.4"],
    tests_require=["pytest==4.4.1"],
    test_suite="tests",
)