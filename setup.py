import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='popstore',
    version='0.1.1',
    description='',
    url='https://github.com/jesseneverdie/popstore.git',
    author='Jesse Kim',
    author_email='jesse@nextwith.com',
    long_description=long_description,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    zip_safe=False
)