import os
import yaml
import utils
from pprint import pprint, pformat

class HTMLPage(object):
    def __init__(self, site, path):
        self.path = path
        self.site = site
        self.queries = {}
        self.data = {}

        fullpath = os.path.join(site.basepath, site.config['src_dir'], path)
        fh = open(fullpath, 'r')
        firstline = fh.readline()
        if firstline.startswith('---'):
            s = fh.read()
            metadata, content = s.split('---')
            metadata = yaml.load(metadata)
            content = content.strip()
        if 'data' in metadata:
            for k, v in metadata['data'].iteritems():
                self.queries[k] = v
        if 'template' not in metadata:
            self.template = site.config['template']
        else:
            self.template = metadata['template']
            
        self.data = metadata
        self.data['content'] = content
        self.dest = self.path
        self.data['root'] = utils.compute_root(self.dest)
        self.data['gentime'] = self.site.config['time']
    def load_template(self):
        self.tmpl = self.site.get_template(self.template)
    def load_data(self):
        for k, v in self.queries.iteritems():
            self.data[k] = self.site.get_data(v)
    def render(self):
        """Return an iterable of destinations and strings to render"""
        self.load_template()
        self.load_data()
        pprint(self.data)
        return [(self.dest, self.tmpl.render(**self.data))]

class IntranetCopy(HTMLPage):
    def render(self):
        self.load_template()
        self.load_data()

        return [(self.dest, self.tmpl.render(**self.data)),
                ('local/' + self.dest, self.tmpl.render(intranet = True,
                                                        **self.data))]
        
class File(object):
    pass
