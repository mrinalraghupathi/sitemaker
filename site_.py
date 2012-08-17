import os
import codecs
import csv
import yaml
import re
import imp
from datetime import datetime, time, date
from handlers import *
from query import Query
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
        self.config = {'template_dir' : 'templates',
                       'data_dir' : 'data',
                       'src_dir' : 'src',
                       'dest_dir' : 'output',
                       'files_dir' : 'files',
                       'name' : '',
                       'template' : 'default.html',
                       'time' : datetime.now()}
        fh = open(opj(self.basepath, 'config.yaml'), 'r')
        self.config.update(yaml.load(fh.read()))
        
        settings_dir = opj(basepath, 'settings')
        self.settings = { 'routes' : [('.*.html$', HTMLPage)] }
        if os.path.isdir(opj(basepath, 'settings')):
            # import settings.py which should contain a routing table
            # at the minimum?
            if os.path.isfile(opj(basepath ,'settings', 'settings.py')):
                self.settings = imp.load_source('settings',
                                                opj(settings_dir, 'settings.py'))

        self.templates = {}
        self.env = utils.make_html_env(opj(self.basepath,
                                           self.config['template_dir']))
        
        self.things = []
        self.pages = []
        self.files = []
        
        self.routes = self.settings['routes']
        for i, rt in enumerate(self.routes):
            self.routes[i] = (re.compile(rt[0]), rt[1])
            
    def build(self):
        src_dir =  self.config['src_dir']
        for path, ds, fs in os.walk(src_dir):
            print self.basepath, path, fs
            for f in fs:
                fullpath = opj(self.basepath, path, f)
                path = os.path.relpath(opj(path, f), src_dir)
                fname, ext = os.path.splitext(f)
                for pattern, handler in self.routes:
                    m = pattern.match(path)
                    if m:
                        h = handler(self, path)
                        self.things.append(h)
                        for output in h.render():
                            o = open(opj(self.basepath,
                                         self.config['dest_dir'],
                                         output[0]),
                                     'w')
                            o.write(output[1])
                            o.close()

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
                    
    def get_template(self, name):
        if name not in self.templates:
            self.templates[name] = self.env.get_template(name)
        return self.templates[name]

    def get_data(self, query_string):
        q = Query(self.config['data_dir'], query_string)
        return q.load_data()
        
        
