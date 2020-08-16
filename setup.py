import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='courier',
    version='0.0.1',
    description='Python IOT Data Collector',
    author='jalepi',
    author_email='jalepi@live.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/jalepi/courier',
    packages=['courier', 'courier.run'],
    install_requires=[
        'flask',
        'applicationinsights',
    ],
)