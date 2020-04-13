from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='onnawsorgs',
    version='0.0.4',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    url='https://onnawsorgs.oznetnerd.com',
    install_requires=[
        'boto3'
    ],
    license='',
    author='Will Robinson',
    author_email='will@oznetnerd.com',
    description='Convenience Python module for AWS Organisations & STS'
)
