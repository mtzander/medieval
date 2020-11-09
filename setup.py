from setuptools import setup, find_packages

setup(
    name='medieval',
    version='3.0.0',
    description='',
    url='',
    packages=find_packages(),
    install_requires=[
        'aiocache==0.11.1',
        'aiofiles==0.6.0',
        'Babel==2.9.0',
        'databases[postgresql]==0.4.0',
        'foreground==0.1.2',
        'jinja2==2.11.2',
        'natsort==7.0.1',
        'Pillow==8.0.1',
        'python-multipart==0.0.5',
        'rcssmin==1.0.6',
        'rjsmin==1.1.0',
        'starlette==0.13.8',
        'uvicorn==0.12.2'
    ]
)
