
import subprocess

from distutils.core import setup

git_describe = subprocess.Popen(('git','describe'), stdout=subprocess.PIPE)
out, err = git_describe.communicate()
git_version = out.strip()

setup(name='ubik',
      version=git_version,
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
