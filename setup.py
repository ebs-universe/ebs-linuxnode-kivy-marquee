import setuptools

_requires = [
    'setuptools-scm',
    'ebs-linuxnode-gui-kivy-core>=2.0',
    # ebs Widgets
    'kivy_garden.ebs.marquee>=1.2',
]

setuptools.setup(
    name='ebs-linuxnode-gui-kivy-marquee',
    url='https://github.com/ebs-universe/ebs-linuxnode-kivy-marquee',

    author='Chintalagiri Shashank',
    author_email='shashank.chintalagiri@gmail.com',

    description='Marquee for EBS Linuxnode Kivy Applications',
    long_description='',

    packages=setuptools.find_packages(),
    install_requires=_requires,

    setup_requires=['setuptools_scm'],
    use_scm_version=True,

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX :: Linux',
    ],
)
