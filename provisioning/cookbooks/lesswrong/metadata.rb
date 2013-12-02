name             'lesswrong'
maintainer       'Trike Apps'
maintainer_email 'cookbooks@trikeapps.com'
license          'Same as Less Wrong'
description      'Installs/Configures lesswrong'
long_description IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version          '0.1.0'
depends          %w[xml apache2 postgresql database memcached-lesswrong]
