import os

class PBFile:

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
