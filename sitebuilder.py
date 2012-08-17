#!/usr/bin/env python
import argparse
import os
import yaml

import sys
from handlers import *
from site_ import Site

default_config = { 'template_dir' : 'templates',
                   'data_dir' : 'data',
                   'src_dir' : 'src',
                   'dest_dir' : 'output',
                   'files_dir' : 'files',
                   'settings_dir' : 'settings',
                   'pagetitle' : '',
                   'sitetitle' : '',
                   'template' : 'default.html' }
def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", nargs='?', default="build")
    args = parser.parse_args()
    basedir = os.getcwd()
    if args.action == 'quickstart':
        
        for k, v in default_config.iteritems():
            if k.endswith('_dir'):
                os.mkdir(os.path.join(basedir, v))
        o = open('config.yaml', 'w')
        o.write(yaml.dump(default_config, default_flow_style = False))
        o.close()
    elif args.action == 'build':
        s = Site(basedir)
        s.build()
        

if __name__ == "__main__":
    run()
