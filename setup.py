try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='panda3d_sprite',
    description='Panda3D module provides spritesheet capabilities to the Panda3D game engine',
    long_description=open("README.md", 'r').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    version='1.1.0',
    author='Jordan Maxwell',
    maintainer='Jordan Maxwell',
    url='https://github.com/NxtStudios/panda3d-sprite',
    packages=['panda3d_sprite'],
    classifiers=[
        'Programming Language :: Python :: 3',
    ])
