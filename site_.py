import os
import codecs
import csv
import yaml
import re
import imp
from datetime import datetime, time, date
from handlers import *
from query import Query
import shutil
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
            for f in fs:
                fullpath = opj(self.basepath, path, f)
                relpath = os.path.relpath(opj(path, f), src_dir)
                fname, ext = os.path.splitext(f)
                for pattern, handler in self.routes:
                    m = pattern.match(relpath)
                    print pattern
                    if m:
                        h = handler(self, relpath)
                        self.things.append(h)
                        for output in h.render():
                            opath = opj(self.basepath,
                                        self.config['dest_dir'],
                                        output[0])
                            odir = os.path.dirname(opath)
                            if not os.path.isdir(odir):
                                os.makedirs(odir)
                            o = open(opath, 'w')
                            print "Writing {0}".format(opath)
                            o.write(output[1])
                            o.close()

        fdir = self.config['files_dir']
        for path, ds, fs in os.walk(fdir):
            for f in fs:
                src = opj(path, f)
                relpath = os.path.relpath(opj(path, f), fdir)
                dest = opj(self.config['dest_dir'], relpath)
                
                src_time = os.path.getmtime(src)
                should_copy = False
                if os.path.isfile(dest):
                    dest_time = os.path.getmtime(dest)
                    if src_time > dest_time:
                        should_copy = True
                else:
                    should_copy = True
                print "Will this be copied {0}".format(should_copy)
                if should_copy:
                    odir = os.path.dirname(dest)
                    if not os.path.isfile(odir):
                        os.makedirs(odir)
                    shutil.copy2(src, dest)
                    
    def get_template(self, name):
        if name not in self.templates:
            self.templates[name] = self.env.get_template(name)
        return self.templates[name]

    def get_data(self, query_string):
        q = Query(self.config['data_dir'], query_string)
        return q.load_data()        
