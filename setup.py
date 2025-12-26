# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="htmltestrunner-lit",
    version="1.0.2",
    author="Lit",
    author_email="clm24Kmagic@163.com",
    description="现代化的 Python unittest HTML 测试报告生成器",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Aquarius-0455/HTMLTestRunner-Lit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    keywords="unittest, test, testing, report, html, htmltestrunner",
)

