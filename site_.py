import os
import codecs
import csv
import re
import imp
from datetime import datetime, time, date
import shutil

from hashlib import sha1
import yaml

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
                       'sitetitle' : '',
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
        # Hacky, clean up later
        def string_to_date(value, format='%H:%M / %d-%m-%Y'):
            dt = datetime.strptime(value, '%m/%d/%Y')
            return dt.strftime(format)
        def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
            return value.strftime(format)
        
        def linktofile(value):
            name, ext = os.path.splitext(value)
            return '<a href="{0}">[{1}]</a>'.format(value, ext[1:].upper())
        self.env = utils.make_html_env(opj(self.basepath,
                                           self.config['template_dir']))
        self.env.filters['datetimeformat'] = string_to_date
        self.env.filters['linktofile'] = linktofile
        self.env.filters['formattime'] = datetimeformat
        self.things = []
        self.pages = []
        self.files = []
        
        self.routes = self.settings['routes']
        for i, rt in enumerate(self.routes):
            self.routes[i] = (re.compile(rt[0]), rt[1])
            
    def build(self, paths_to_build = []):
        src_dir =  self.config['src_dir']
        for path, ds, fs in os.walk(src_dir):
            for f in fs:
                fullpath = opj(self.basepath, path, f)
                relpath = os.path.relpath(opj(path, f), src_dir)
                fname, ext = os.path.splitext(f)
                for pattern, handler in self.routes:
                    m = pattern.match(relpath)
                    if m:
                        h = handler(self, relpath)
                        self.things.append(h)
                        for output in h.render():
                            opath = opj(self.basepath,
                                        self.config['dest_dir'],
                                        output['dest'])
                            odir = os.path.dirname(opath)
                            if not os.path.isdir(odir):
                                os.makedirs(odir)
                                
                            should_write = True
                            if os.path.isfile(opath):
                                fh = open(opath, 'rb')
                                s = fh.read()
                                fh.close()
                                current_hash = sha1(s).hexdigest()
                                new_hash = sha1(output['text'].encode('utf-8')).hexdigest()
                                if current_hash == new_hash:
                                    should_write = False
                                
                            if should_write:
                                o = codecs.open(opath, 'w', 'utf-8')
                                print "Writing {0}".format(output['dest']) 
                                o.write(output['text'])
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

                if should_copy:
                    print "Copying {0} {1}".format(src, dest)
                    odir = os.path.dirname(dest)
                    if not os.path.isdir(odir):
                        os.makedirs(odir)
                    shutil.copy2(src, dest)
                    
    def get_template(self, name):
        if name not in self.templates:
            self.templates[name] = self.env.get_template(name)
        return self.templates[name]

    def get_data(self, query_string):
        q = Query(self.config['data_dir'], query_string)
        return q.load_data()        
