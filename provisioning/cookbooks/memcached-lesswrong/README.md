Description
===========

Installs memcached-1.2.5 with the patch required for lesswrong

Requirements
============

Attributes
==========

The following are node attributes passed to the template for the runit
service.

* `memcached[:memory]` - maximum memory for memcached instances.
* `memcached[:user]` - user to run memcached as.
* `memcached[:port]` - port for memcached to listen on.
* `memcached[:listen]` - IP address for memcached to listen on.

Usage
=====

Simply set the attributes and it will configure the
/etc/memcached.conf file. If you want to use multiple memcached
instances, you'll need to modify the recipe to disable the startup
script and the template in the default recipe.

Use the define, memcached_instance, to set up a runit service for the
named memcached instance.

    memcached_instance "myproj"

The recipe also reads in whether to start up memcached from a
/etc/default/memcached "ENABLE_MEMCACHED" setting, which is "yes" by
default.

License and Author
==================

Author:: Catherine Truscott
Based on the memcached recipe authored by:
Joshua Timberman (<joshua@opscode.com>)
Joshua Sierles (<joshua@37signals.com>)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
