import os
from datetime import datetime
from hashlib import sha1

from jinja2 import Environment, FileSystemLoader, contextfilter

@contextfilter
def link(ctx, val):
    return ctx['root'] + val.dest


def string_to_date(value, format='%H:%M / %d-%m-%Y'):
    dt = datetime.strptime(value, '%m/%d/%Y')
    return dt.strftime(format)


def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)


def linktofile(value):
    name, ext = os.path.splitext(value)
    return '<a href="{0}">[{1}]</a>'.format(value, ext[1:].upper())


def make_html_env(dir):
    env = Environment(loader = FileSystemLoader(dir),
                      trim_blocks = True)
    env.filters['link'] = link
    env.filters['datetimeformat'] = string_to_date
    env.filters['linktofile'] = linktofile
    env.filters['formattime'] = datetimeformat
    return env


def remove_quotes(s):
    return s.strip('\'"')
        

def hashfunc(contents):
    return sha1(contents).hexdigest()


def compute_root(path):
    n = len(path.split('/')) - 1
    return '../'*n


def walker(directory, func):
    """Walk a directory and apply a function to each file

    The function walker applies func, func should accept the file
    handle as a parameter. The value returned from func is stored in a
    dict with the key being the files relative path. The dict is
    returned at the end of walker. If the return value is falsy, then
    the file is skipped

    Args:
        directory: string representing the path at which to begin the walk
        func: function or callable applied to each file handleand should
            return a value

    Returns:
        A dict keys are relative paths and the values are those
        returned by func
    """
    d = {}
    for path, ds, fs in os.walk(directory):
        fs = [f for f in fs if not f.endswith('~')]
        for f in fs:
            ff = os.path.join(path, f)
            fh = open(ff, 'r')
            x = func(fh)
            if x:
                d[f] = x
    return d

