from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='onnawsorgs',
    version='0.0.2',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    url='https://oznetnerd.com',
    install_requires=[
        'onnlogger==0.0.5'
    ],
    license='',
    author='Will Robinson',
    author_email='will@oznetnerd.com',
    description='Convenience Python module for AWS Organisations & STS'
)
