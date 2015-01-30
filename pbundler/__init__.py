from __future__ import absolute_import

__all__ = ['PBundler']

from .exceptions import *
from .bundle import Bundle
from .cli import PBCli


class PBundler(object):
    """Public API"""

    @classmethod
    def load_bundle(cls, path=None):
        """Load a bundle from path and return it. Does not modify the
        current environment."""
        return Bundle.load(path)

    @classmethod
    def setup(cls, path=None, groups=None):
        """Load a bundle from path and activate it in the current
        environment.

        Returns the bundle."""
        bundle = Bundle.load(path)
        if groups is None:
            groups = 'default'
        bundle.enable(groups)
        return bundle

