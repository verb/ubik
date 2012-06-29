
import subprocess

from distutils.core import setup

setup(name='ubik',
      version=subprocess.check_output(('git','describe')).strip(),
      author='Lee Verberne',
      author_email='lee@blarg.org',
      description='Use only as directed.',
      license='GPLv3',
      package_dir={'': 'lib'},
      packages=['ubik',
                'ubik.fab',
                'ubik.hats',
                'ubik.infra',
                'ubik.rug',
                ],
      requires=['fabric'],
      scripts=['bin/rug'],
      url='http://github.com/verb/ubik',
      )
