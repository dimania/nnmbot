from babel.messages import frontend as babel
from distutils.core import setup

setup(name='nnmbot',
      version='0.2',
      cmdclass = {'extract_messages': babel.extract_messages,
                  'init_catalog': babel.init_catalog,
                  'update_catalog': babel.update_catalog,
                  'compile_catalog': babel.compile_catalog,}
)

