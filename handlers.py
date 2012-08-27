import os
import yaml
import utils
from pprint import pprint, pformat
import codecs 
class HTMLPage(object):
    def __init__(self, site, path):
        self.path = path
        self.site = site
        self.queries = {}
        self.data = {}

        fullpath = os.path.join(site.basepath, site.config['src_dir'], path)
        fh = codecs.open(fullpath, 'r', 'utf-8')
        firstline = fh.readline()
        if firstline.startswith('---'):
            # For some strange reason readline causes the next call to
            # read to not read the entire file. Is this a bug in codecs?
            s = fh.read() + fh.read()
            # print s.split('---')
            stuff = s.split('---')

            if len(stuff) >= 1:
                metadata = yaml.load(stuff[0]) or {}
                if len(stuff) >= 2:
                    content = stuff[1].strip()
                else:
                    content = ''
                    
        if 'data' in metadata:
            for k, v in metadata['data'].iteritems():
                self.queries[k] = v
        if 'template' not in metadata:
            self.template = site.config['template']
        else:
            self.template = metadata['template']

        self.metadata = metadata
        self.data = metadata
        self.data['content'] = content
        self.dest = self.path
        self.data['root'] = utils.compute_root(self.dest)
        self.data['gentime'] = self.site.config['time']
        self.data['sitetitle'] = self.site.config['sitetitle']


    def load_template(self):
        self.tmpl = self.site.get_template(self.template)

        
    def load_data(self):
        for k, v in self.queries.iteritems():
            self.data[k] = self.site.get_data(v)


    def load_files(self):
        self.files = {}
        if 'files' in self.metadata:
            for k, v in self.metadata['files'].iteritems():
                self.files[k] = self.site.get_files(v)


    def render_content(self):
        content_template = self.site.env.from_string(self.data['content'])
        content = content_template.render(**self.data)
        self.data['content'] = content
        

    def process(self):
        pass

    
    def run(self):
        """Run before rendering. Need a better name!"""
        self.load_template()
        self.load_data()
        self.load_files()
        self.render_content()
        self.process()
        # pprint(self.data)

    def render(self):
        """Return an iterable of destinations and strings to render"""
        self.run()
        return [{'dest' : self.dest,
                 'text' : self.tmpl.render(**self.data)}]
