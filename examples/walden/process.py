from sys import stdin, stdout
import re

outf = stdout

line = stdin.readline()
while line:
    if re.match('^##.*', line):
        name = line[3:].lower().strip()
        name = name.replace(' ', '-')
        fn = name + '.md'
        outf = open(fn, 'w')
        outf.write('---\n')
        outf.write(f'title: {line[3:]}')
        outf.write(f'id: {name}\n')
        outf.write(f'layout: default.haml\n')
        outf.write(f'author: Henry David Thoreau\n')
        outf.write(f'date: 2018-04-15\n')
        outf.write(f'kind: article\n')
        outf.write('---\n\n')
    outf.write(line)
    line = stdin.readline()
