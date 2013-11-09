from __future__ import print_function
from __future__ import absolute_import

__all__ = ['CheeseshopSource']

import os
import pkg_resources
import xmlrpclib

from . import PBundlerException
from .util import PBDownloader


class CheeseshopSource(object):

    def __init__(self, url):
        self.url = url
        if self.url.endswith('/'):
            self.url = self.url[:-1]

    def _src(self):
        return xmlrpclib.ServerProxy(self.url, xmlrpclib.Transport())

    def available_versions(self, cheese):
        versions = self._src().package_releases(cheese.name, True)
        return versions

    def requires(self, cheese):
        d = self._src().release_data(cheese.name, cheese.exact_version)
        return d["requires"]

    def download(self, cheese, target_path):
        urls = self._src().release_urls(cheese.name, cheese.exact_version)
        filename = None
        url = None
        remote_digest = None
        for urlinfo in urls:
            if urlinfo['packagetype'] != 'sdist':
                continue
            filename = urlinfo['filename']
            url = urlinfo['url']
            remote_digest = urlinfo['md5_digest']
            break

        if not url:
            print(repr(urls))

            raise PBundlerException("Did not find an sdist for %s %s on %s" % (cheese.name, cheese.exact_version, self.url))

        target_file = os.path.join(target_path, filename)
        PBDownloader.download_checked(url, target_file, remote_digest)
        return target_file


class FilesystemSource(object):

    def __init__(self, path):
        self.path = os.path.expanduser(path)

    def available_versions(self, cheese):
        dists = pkg_resources.find_distributions(self.path, only=True)
        return [dist.version for dist in dists]

    def get_distribution(self, cheese):
        dists = pkg_resources.find_distributions(self.path, only=True)
        return [dist for dist in dists][0]
