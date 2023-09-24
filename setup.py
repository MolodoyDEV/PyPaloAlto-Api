from setuptools import find_packages, setup

setup(name='pypaloalto_api',
      version='0.6.4',
      url='https://github.com/MolodoyDEV/PyPaloAlto-Api',
      license='MIT',
      author='Nikita Potapov',
      author_email='Nikita1Potapov@yandex.ru',
      description='Framework grant simple access to PaloAlto devices API',
      packages=find_packages(exclude=['tests']),
      install_requires=[
          'requests',
          'urllib3',
          'pyyaml'
      ],
      zip_safe=False)
