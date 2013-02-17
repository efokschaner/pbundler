from __future__ import print_function
from __future__ import absolute_import

__all__ = ['LocalStore']

import os
import platform
import pkg_resources
import glob
import subprocess
import sys
import tempfile

from . import PBundlerException
from .util import PBFile, PBArchive


class LocalStore(object):

    def __init__(self, path=None):
        if path is None:
            if os.getenv('PBUNDLER_STORE'):
                self.path = os.getenv('PBUNDLER_STORE')
            else:
                self.path = os.path.expanduser('~/.cache/pbundler/')
        else:
            self.path = path

        PBFile.ensure_dir(self.path)
        self._temp_path = None
        self.python_name = ('%s-%s' % (platform.python_implementation(),
                            ('.'.join(platform.python_version_tuple()[:-1]))))

    @property
    def cache_path(self):
        path = os.path.join(self.path, 'cache')
        PBFile.ensure_dir(path)
        return path

    @property
    def temp_path(self):
        if not self._temp_path:
            self._temp_path = tempfile.mkdtemp(prefix='pbundle')
        return self._temp_path

    def get(self, cheese):
        lib_path = self.path_for(cheese, 'lib')
        if os.path.exists(lib_path):
            dists = [d for d in pkg_resources.find_distributions(lib_path, only=True)]
            if len(dists) == 1:
                return dists[0]

        return None

    def path_for(self, cheese, sub=None):
        path = [self.path, 'cheese', self.python_name,
                '%s-%s' % (cheese.name, cheese.exact_version)]
        if sub is not None:
            path.append(sub)
        return os.path.join(*path)

    def prepare(self, cheese, source):
        """Download and unpack the cheese."""

        print("Preparing %s %s..." % (cheese.name, cheese.exact_version))

        # path we use to install _from_
        source_path = os.path.join(self.temp_path, cheese.name, cheese.exact_version)

        sdist_filepath = source.download(cheese, self.cache_path)
        PBArchive(sdist_filepath).unpack(source_path)

        # FIXME: ugly hack to get the unpacked dir.
        # actually we should say unpack(..., strip_first_dir=True)
        source_path = glob.glob(source_path + '/*')[0]
        return UnpackedSdist(source_path)

    def install(self, cheese, unpackedsdist):
        print("Installing %s %s..." % (cheese.name, cheese.exact_version))
        setup_cwd = unpackedsdist.path
        cheese_path = self.path_for(cheese)
        lib_path = self.path_for(cheese, 'lib')
        PBFile.ensure_dir(lib_path)
        cmd = [sys.executable, 'setup.py', 'install',
               '--root', cheese_path,
               '--install-lib', 'lib',
               '--install-scripts', 'bin']
        env = dict(os.environ)
        env.update({'PYTHONPATH': lib_path})
        with tempfile.NamedTemporaryFile(delete=False) as logfile:
            proc = subprocess.Popen(cmd,
                                    cwd=setup_cwd,
                                    close_fds=True,
                                    stdin=subprocess.PIPE,
                                    stdout=logfile,
                                    stderr=subprocess.STDOUT,
                                    env=env)
            proc.stdin.close()
            rv = proc.wait()
        if rv == 0:
            return self.get(cheese)
        else:
            with file(logfile.name, 'rb') as logfile:
                print(logfile.read())
            msg = "Installing failed with exit code %d. Source files have been left in %r for you to examine." % (rv, setup_cwd)
            raise PBundlerException(msg)


class UnpackedSdist(object):

    def __init__(self, path):
        self.path = path
        self.is_sdist = True

    def requires(self):
        requires_path = os.path.join(self.path, 'PKG-INFO', 'requires.txt')
        if not os.path.exists(requires_path):
            return []

        with file(requires_path, 'rt') as f:
            return pkg_resources.parse_requirements(f)
