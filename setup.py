from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()

version = '1.3.4'

install_requires = [
    'pyxattr',
    'psutil',
    'scandir;python_version<"3.5"'
]


setup(name='collectd_cvmfs',
    version=version,
    description="Collectd Plugin to Monitor CvmFS Clients",
    long_description=README + '\n\n' + NEWS,
    long_description_content_type='text/x-rst',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Topic :: System :: Monitoring",
    ],
    keywords='collectd cvmfs monitoring',
    author='Luis Fenandez Alvarez',
    author_email='luis.fernandez.alvarez@cern.ch',
    url='https://github.com/cvmfs/collectd-cvmfs',
    license='Apache II',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    data_files = [('/usr/share/collectd/', ['resources/collectd_cvmfs.db'])],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires
)
