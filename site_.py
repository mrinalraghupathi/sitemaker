import os
import codecs
import re
import imp
from datetime import datetime
import shutil
import fnmatch
import glob
from hashlib import sha1
import yaml

from handlers import HTMLPage
from query import Query
import utils

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
        file_h = open(opj(self.basepath, 'config.yaml'), 'r')
        self.config.update(yaml.load(file_h.read()))
        
        settings_dir = opj(basepath, 'settings')

        if (os.path.isdir(opj(basepath, 'settings')) and
            os.path.isfile(opj(basepath, 'settings', 'settings.py'))):
            # import settings.py which should contain a routing table
            settings_file = opj(settings_dir, 'settings.py')
            self.settings = imp.load_source('settings', settings_file)
        else:
            self.settings = imp.new_module('__settings__')
            self.settings.routes = [('.*.html$', HTMLPage)]
            
        self.templates = {}
        self.env = utils.make_html_env(opj(self.basepath,
                                           self.config['template_dir']))

        self.things = []
        self.pages = []
        self.files = []
        
        self.routes = self.settings.routes
        for i, route in enumerate(self.routes):
            self.routes[i] = (re.compile(route[0]), route[1])


    def generate_path(self, relpath, force = False):
        """Decides whether a path needs to be written and if so writes
           the path to the output file"""
        def should_write(output, path):
            if os.path.isfile(path):
                file_h = open(path, 'rb')
                contents = file_h.read()
                file_h.close()
                current_hash = utils.hashfunc(contents)
                encode_txt = output['text'].encode('utf-8')
                new_hash = utils.hashfunc(encode_txt)
                if current_hash == new_hash:
                    return False
            return True

                    
        # fullpath = opj(self.basepath, path)
        # relpath = os.path.relpath(opj(path), self.config['src_dir'])
        # fname, ext = os.path.splitext(relpath)
        for pattern, handler_class in self.routes:
            
            match = pattern.match(relpath)
            if match:
                print 'Generating {0} {1}'.format(relpath, handler_class)
                handler = handler_class(self, relpath)
                self.things.append(handler)
                for output in handler.render():
                    opath = opj(self.basepath,
                                self.config['dest_dir'],
                                output['dest'])
                    odir = os.path.dirname(opath)
                    if not os.path.isdir(odir):
                        os.makedirs(odir)
                    if not force:
                        update = should_write(output, opath)
                    if update:
                        dest_file = codecs.open(opath, 'w', 'utf-8')
                        print "Writing {0}".format(output['dest']) 
                        dest_file.write(output['text'])
                        dest_file.close()
                break


    def generate(self, paths_to_build = None, force = False):
        src_dir =  self.config['src_dir']
        # compute the length, since we will strip off that many
        # characters from the path, plus one for the slash
        take_off = len(src_dir) + 1
        for path, _, files in os.walk(src_dir):
            files = [opj(path, file_)[take_off:] for file_ in files]
            if paths_to_build:
                temp = []
                for patt in paths_to_build:
                    # print patt, fs
                    temp += fnmatch.filter(files, patt)
                files = temp
            for file_ in files:
                self.generate_path(file_, force)

                                
    def copy_file_path(self):
        pass
    
    
    def copy_files(self):
        # copy and preserve symlinks
        def mycopy(src, dest):
            if os.path.islink(src):
                path = os.readlink(src)
                os.symlink(path, dest)
            else:
                shutil.copy2(src, dest)
                
        fdir = self.config['files_dir']
        for path, _, files in os.walk(fdir):
            # A hack on OSX to avoid copying DS_Store files
            files = [f for f in files if not f.startswith('.DS')]
            for file_ in files:
                src = opj(path, file_)
                relpath = os.path.relpath(opj(path, file_), fdir)
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
                    mycopy(src, dest)

    def clean_up(self):
        """Clean up the output directory by deleting files that did not appear"""
        pass
    
    def build(self, paths_to_build = [], force = False):
        self.generate(paths_to_build, force)
        self.copy_files()

        
    def get_template(self, name):
        if name not in self.templates:
            self.templates[name] = self.env.get_template(name)
        return self.templates[name]


    def get_data(self, query_string):
        query = Query(self.config['data_dir'], query_string)
        return query.load_data()

    def get_files(self, pattern):
        """Take a unix-style glob pattern and return all files
        matching the patter in the files directory"""
        basename = self.config['files_dir'] + '/'
        n = len(basename)
        return [f[n:] for f in glob.glob(basename + pattern)]
