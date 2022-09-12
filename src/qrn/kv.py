class KV:
    "Key/value object, syntactic sugar around a dict."
    def __init__(self, **kvs):
        attrs = {}
        for k in kvs:
            attrs[k] =  kvs[k]
        super().__setattr__('attrs', attrs)

    def update(self, attrs):
        self.attrs.update(attrs)

    def __getattr__(self, name):
        return self.attrs[name]

    def __setattr__(self, name, value):
        self.attrs[name] = value

    def __iter__(self):
        return self.attrs.__iter__()

    def __getitem__(self, x):
        return self.attrs[x]

    def __repr__(self):
        return f'KV: {self.attrs}'



if __name__ == '__main__':
    kv = KV(fn='Russ', ln='Olsen')
    kv.age = 99
    print(kv.age)
    print(kv)

    m = {'foo': 7717, 'bar':88}
    kv.update(m)
    print(kv)
    print(kv.age)
    print(kv.foo)
