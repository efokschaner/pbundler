from __future__ import print_function
from __future__ import absolute_import

__all__ = ['DslRunner']


class DslRunner(object):
    """Runs Python code in the context of a class.

    Public methods will be exposed to the DSL code.
    """

    def __init__(self, contextclass):
        self.contextclass = contextclass

    def make_context(self):
        ctx = self.contextclass()
        ctxmap = {}
        method_names = [fun for fun in ctx.__class__.__dict__ if not fun.startswith('_')]
        methods = ctx.__class__.__dict__

        def method_caller(fun):
            unbound = methods[fun]
            def wrapped(*args, **kw):
                args = (ctx,) + args
                return unbound(*args, **kw)
            return wrapped

        for fun in method_names:
            ctxmap[fun] = method_caller(fun)

        return (ctx, ctxmap)

    def execfile(self, filename):
        ctx, ctxmap = self.make_context()
        execfile(filename, {}, ctxmap)
        return ctx
