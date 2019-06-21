import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="soyla",
    version="0.0.1",
    author="Azat Khasanshin",
    author_email="azatkhasanshin@gmail.com",
    description="Simple terminal program to record tts dataset",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bazukas/soyla",
    packages=['soyla'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'numpy',
        'scipy',
        'sounddevice',
        'urwid',
    ]
)
