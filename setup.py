try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

long_description = """
The P3D-Sprite module provides spritesheet capabilities to the Panda3D game engine. This module is a modification and slight redesign of work done by Panda3D forum user ZeroByte.
"""

setup(
    name='panda3d_sprite',
    description='Panda3D module provides spritesheet capabilities to the Panda3D game engine',
    long_description=long_description,
    license='MIT',
    version='1.0.0',
    author='Jordan Maxwell',
    maintainer='Jordan Maxwell',
    url='https://github.com/NxtStudios/p3d-prite',
    packages=['panda3d_sprite'],
    classifiers=[
        'Programming Language :: Python :: 3',
    ])
