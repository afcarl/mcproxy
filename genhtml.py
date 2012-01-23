#!/usr/bin/env python
##
##  map html generator (for pigmap)
##

import sys, os, re, time, stat, fileinput

LINE = re.compile(r'^([^:]+):([^:]+):(.*)')
COORDS = re.compile(r'[-\d]+')
def get_entry(line):
    m = LINE.match(line)
    if not m: raise ValueError(line)
    (t, title, xyz) = m.groups()
    title = re.sub(r'\s+portal\s*$', '', title, flags=re.I)
    name = re.sub(r'[^-_a-z0-9]', '', title, flags=re.I)
    f = [ int(m.group(0)) for m in COORDS.finditer(xyz) ]
    if len(f) == 3:
        (x,y,z) = f
    elif len(f) == 2:
        (x,z) = f
        y = 64
    else:
        raise ValueError(line)
    return (t, (t+'_'+name, title, (x,y,z)))

def read_entries(fp):
    for line in fp:
        try:
            line = line[:line.index('#')]
        except ValueError:
            pass
        line = line.strip()
        if not line: continue
        yield get_entry(line)
    return

def read_params(params, fp):
    for line in fp:
        line = line.strip()
        try:
            i = line.index(' ')
        except ValueError:
            continue
        (k,v) = (line[:i], line[i+1:])
        params[k] = v
    return params

ENTRIES = re.compile(r'@@ENTRIES@@')
MARKERS = re.compile(r'@@MARKERS:([^@]+)@@')
PARAM = re.compile(r'@@PARAM:([^@]+)@@')
def main(argv):
    import getopt
    def usage():
        print 'usage: %s [-C] [-i src.html] [-b pigmap.params] [-p key=value] coords.txt ...' % argv[0]
        return 100
    try:
        (opts, args) = getopt.getopt(argv[1:], 'Ci:b:p:')
    except getopt.GetoptError:
        return usage()
    add_commap = False
    src_html = 'src.html'
    pigmap_params = 'pigmap.params'
    params = {
        'date': time.strftime('%Y-%m-%d GMT'),
        }
    for (k, v) in opts:
        if k == '-C': add_commap = True
        elif k == '-i': src_html = v
        elif k == '-b': pigmap_params = v
        elif k == '-p':
            (k,v) = v.split('=')
            params[k] = v
    #
    entries = sorted(read_entries(fileinput.input(args)))
    #
    fp = file(pigmap_params)
    read_params(params, fp)
    fp.close()
    mtime = os.stat(pigmap_params)[stat.ST_MTIME]
    params['lastUpdated'] = time.strftime('%Y-%m-%d GMT', time.gmtime(mtime))
    #
    out = sys.stdout
    fp = file(src_html)
    for line in fp:
        m = ENTRIES.search(line)
        if m:
            for (_,(name,title,(x,y,z))) in entries:
                out.write(' { name:"%s", title:"%s", x:%s, y:%s, z:%s },\n' % (name,title,x,y,z))
            continue
        m = MARKERS.search(line)
        if m:
            t0 = m.group(1)
            for (t1,(name,title,_)) in entries:
                if t0 != t1: continue
                out.write('<div>')
                out.write('<a href="javascript:void(0);" onclick="gotoLocationByName(%r);">%s</a>' % (name, title))
                if add_commap:
                    out.write(' <small>(<a href="./map/%s/index.html#name=%s" target="%s">map</a>)</small>' % (name, name, name))
                out.write('</div>\n')
            continue
        out.write(PARAM.sub(lambda m: params[m.group(1)], line))
    fp.close()
    return 0

if __name__ == '__main__': sys.exit(main(sys.argv))