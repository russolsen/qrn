x = '{:foo => "hello", :bar => "zzz",   "baz" => 3987 } '

import re

BR = re.compile('^ *\{')
ACE = re.compile('\} *$')
def parse_attrs(s):
    s = BR.sub('', s)
    s = ACE.sub('', s)
    print("after subs", s)
    parts = re.split(',', s)
    result = {}
    for p in parts:
        nv = re.split('=>', p)
        name = nv[0].strip()
        name = name.replace(':', '')
        name = name.replace('"', '')
        name = name.replace("'", '')
        value = nv[1].strip()
        result[name] = eval(value)
    return result

print(parse_attrs(x))
