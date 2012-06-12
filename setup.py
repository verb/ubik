
from distutils.core import setup

setup(name='ubik',
      version='0.10.1',
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
      url='http://github.com/verb/ubik',
      )
