"""Setup."""
from setuptools import setup, find_packages

setup(
    name='medieval',
    version='3.0.0',
    description='',
    url='https://github.com/mtzander/medieval',
    packages=find_packages(),
    install_requires=[
        'aiocache==0.12.3',
        #'aiofiles==24.1.0',
        'Babel==2.14.0',
        'databases[postgresql]==0.9.0',
        'foreground==0.1.2',
        'jinja2==3.1.6',
        'natsort==8.4.0',
        'Pillow==11.2.1',
        'python-multipart==0.0.20',
        'rcssmin==1.2.1',
        'rjsmin==1.2.4',
        'starlette==0.46.2',
        'uvicorn==0.34.2'
    ]
)
