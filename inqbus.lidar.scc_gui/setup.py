from setuptools import setup, find_packages
import os

version = '2.0'


setup(name='lidar.scc_gui',
      version=version,
      description="Analysis is LIDAR data for PollXT Lidars.",
      long_description=open("README.txt").read() + "\n" +
      open("HISTORY.txt").read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          "Programming Language :: Python",
          "Environment :: Plugins",
          "Intended Audience :: System Administrators",
          "License :: Other/Proprietary License",
          "Natural Language :: English",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
      ],
      keywords='LIDAR',
      author='Inqbus',
      author_email='admin@inqbus.de',
      url='http://inqbus.de',
      download_url='',
      license='other',
      packages=find_packages('src', exclude=['ez_setup']),
      namespace_packages=['inqbus', 'inqbus.lidar'],
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      extras_require=dict(
          extra=[
          ],
          docs=[
              'z3c.recipe.sphinxdoc',
              'sphinxcontrib-requirements',
          ],
          test=[
          ]
      ),
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      [console_scripts]
      quicklook = lidar.scc_gui.quicklook:main
      """,
      )

#pyqtgraph
#qtpy