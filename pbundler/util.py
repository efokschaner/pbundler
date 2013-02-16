import os
from hashlib import md5
from urllib2 import Request, urlopen, HTTPError
import subprocess
import shutil

from . import PBundlerException


class PBFile(object):

    @staticmethod
    def read(path, filename):
        try:
            with open(os.path.join(path, filename), 'r') as f:
                return f.read()
        except Exception as e:
            return None


    @staticmethod
    def find_upwards(fn, root=os.path.realpath(os.curdir)):
        if os.path.exists(os.path.join(root, fn)):
            return root
        up = os.path.abspath(os.path.join(root, '..'))
        if up == root:
            return None
        return PBFile.find_upwards(fn, up)


    @staticmethod
    def ensure_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)


    @staticmethod
    def md5_digest(path):
        digest = md5()
        with file(path, 'rb') as f:
            digest.update(f.read())
        return digest.hexdigest()


class PBDownloader(object):

    @staticmethod
    def download_checked(url, target_file, expected_digest):
        if os.path.exists(target_file):
            # file already exists, see if we can use it.
            if PBFile.md5_digest(target_file) == expected_digest:
                # local file is ok
                return
            else:
                os.unlink(target_file)

        try:
            req = Request(url)
            req.add_header("User-Agent", "pbunder/0.8DEV (http://github.com/zeha/pbundler/issues)")
            req.add_header("Accept", "*/*")
            with file(target_file, 'wb') as f:
                sock = urlopen(req)
                try:
                    f.write(sock.read())
                finally:
                    sock.close()

        except Exception as e:
            raise PBundlerException("Downloading %s failed (%s)" % (url, e))


        local_digest = PBFile.md5_digest(target_file)
        if local_digest != expected_digest:
            os.unlink(target_file)
            raise PBundlerException("Downloading %s failed (MD5 Digest %s did not match expected %s)" % (url, local_digest, expected_digest))
        else:
            # local file is ok
            return


class PBArchive(object):

    def __init__(self, path):
        self.path = path
        self.filetype = os.path.splitext(path)[1][1:]
        if self.filetype in ['tgz', 'gz', 'bz2', 'xz']:
            self.filetype = 'tar'
        if self.filetype not in ['zip', 'tar']:
            raise PBundlerException("Unsupported Archive file: %s" % (self.path))


    def unpack(self, destination):
        if os.path.exists(destination):
            shutil.rmtree(destination)
        PBFile.ensure_dir(destination)
        # FIXME: implement this stuff in pure python
        if self.filetype == 'zip':
            subprocess.call(['unzip', '-q', self.path, '-d', destination])
        elif self.filetype == 'tar':
            subprocess.call(['tar', 'xf', self.path, '-C', destination])
