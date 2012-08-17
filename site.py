import os
import codecs
import csv
import yaml
import re

from datetime import time, date
from handlers import *

opj = os.path.join

class Site(object):
    """The object that contains site configuration information and
    routing information.

    routes: array of tuples containing regexes and handlers. Any files
    that do not match any of the regexps are treated as static
    files. Be careful, a catch-all regex will match"""
    
    def __init__(self, basepath = None):
        if not basepath:
            self.basepath = os.getcwd()
        else:
            self.basepath = basepath
        self.config = {'template_dir' : opj(basepath, 'templates'),
                       'data_dir' : opj(basepath, 'data'),
                       'src_dir' : opj(basepath, 'src'),
                       'dest_dir' : opj(basepath, 'output'),
                       'files_dir' : opj(basepath, 'files'),
                       'name' : '',
                       'template' : 'default.html',
                       'time' : time.now()}
        fh = open(opj(self.basepath, 'config.yaml'), 'r')
        self.config.update(yaml.load(fh.read()))
        settings_dir = opj(basepath, 'settings')
        if os.path.isdir(opj(basepath, 'settings')):
            # import settings.py which should contain a routing table
            # at the minimum??
            self.settings = imp.load_source('settings',
                                            opj(settings_dir, 'settings.py'))
        else:
            self.settings = { 'routes' : [('.*.html$', HTMLPage)] }

        self.things = []
        self.pages = []
        self.files = []
        
        self.routes = self.settings['routes']
        for i, rt in self.routes.enumerate():
            self.routes[i] = (re.compile(rt[0]), rt[1])
        for path, ds, fs in os.walk(self.config['src_dir']):
            for f in fs:
                relpath = opj(path, f)
                fullpath = opj(self.config['src_dir'], path, f)
                fname, ext = os.path.splitext(f)
                for pattern, handler in self.routes:
                    m = pattern.match(relpath)
                    if m:
                        self.things.append(handler(self, relpath))
                        print handler
                        break
        fdir = self.config['files_dir']
        for path, ds, fs in os.walk(fdir):
            for f in fs:
                src = opj(fdir, path, f)
                dest = opj(self.config['dest_dir'], path, f)
                
                src_time = os.path.getmtime(src)
                dest_time = os.path.getmtime(dest)

                if src_time > dest_time:
                    print "Copying {0} --> {1}".format(src, dest)
                else:
                    print "The files are fine"
                
        
        
