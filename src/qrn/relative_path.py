import os.path as path
import qrn.utils as utils

class RelativePath:
    def __init__(self, root, directory, name, suffix):
        self.root = root
        self.dir = directory
        self.name = name
        self.suffix = suffix

    @classmethod
    def from_path(cls, root, path):
        d, n, s = utils.split_path(path)
        return cls(root, d, n, s)

    def path(self):
        return f'{self.dir}/{self.name}.{self.suffix}'

    def modify(self, root=None, directory=None, name=None, suffix=None):
        root = root or self.root
        directory = directory or self.dir
        name = name or self.name
        suffix = suffix or self.suffix
        clz = type(self)
        result = clz(root, directory, name, suffix)
        return result

    def full_path(self):
        return f'{self.root}/{self.dir}/{self.name}.{self.suffix}'

    def __repr__(self):
        return f'{self.root}/{self.dir}/{self.name}.{self.suffix}'


