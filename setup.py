from setuptools import setup, find_packages

__version__ = '0.0.1'

setup(name='wasp-gateway',
      description=('API Gateway: Central access point to a microservice based'
                   ' platform. Translates all communication from REST to '
                   'the backend speak. Adapters provided for HTTP Proxying '
                   'and rabbitmq BUSes'),
      author='Matt Rasband, Nick Humrich',
      author_email='matt.rasband@gmail.com',
      license='Apache-2.0',
      url='',
      download_url='',
      keywords=(
          'microservice',
          'gateway',
          'api',
          'asyncio',
      ),
      packages=find_packages(),
      classifiers=[
          'Programming Language :: Python :: 3.5',
          'License :: OSI Approved :: Apache Software License',
          'Intended Audience :: Developers',
          'Development Status :: 2 - Pre-Alpha',
          'Topic :: Software Development',
      ],
      setup_requires=[
          'pytest-runner',
          'flake8',
      ],
      install_requires=[
          'httptools<=0.9',
      ],
      extras_require={
          # The BUS version translates HTTP Rest calls for wasp-bus-worker
          # based applications
          'bus': ['aiomqp'],
          # The HTTP version simply proxies all requests through to known
          # applications provided by your provided service resolver
          'http': ['aiohttp>=1.0'],
          # Compatibility for spring-cloud (eureka)
          # 'springcloud': ['wasp-eureka'],
      },
      tests_require=[
          'pytest',
      ],
      entry_points={},
      zip_safe=False)
