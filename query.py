from datetime import datetime, date, time, timedelta
import re
import os
import yaml
import json
import csv

from parsers import parse_sql, parse_file_listing

def getattrs(adict, attrs):
    return dict(zip(attrs, [adict.get(attr) for attr in attrs]))

class Query(object):
    op_dict = {'=' : '__eq__',
              '<' : '__gt__',
              '>' : '__lt__',
               '!=' : '__neq__',
              '>=' : '__le__',
              '<=' : '__ge__' }
    def parse(self, sql):
        pr = parse_sql(sql)
        self.filename = pr.filename
        try:
            self.fields = pr.properties.asList()
        except:
            pass
            
        self.where = pr.where
        # Get all fields, it's strange that we need to set self.fields
        # = None for this

        self.order = pr.order
        
        # Now we scan the list of comparison and replace each value
        # with either a string, int, float or datetime. In the future
        # we add support for arbitrary objects that support
        # comparison.
        if self.where:
            self.filter_funcs = []
#           self.where = self.where.asList()
            for i in range(len(self.where)):
                field, op, test = self.where[i]
                try:
                    val = int(test)
                except:
                    try:
                        val = float(test)
                    except:
                        try:
                            val = parse_date(test)
                        except:
                            pass
                        else:
                            val = test
                op_func = getattr(test, self.op_dict[op])
                print test, op_func
                self.filter_funcs.append(op_func)
                self.where[i] = (field, op_func, test)
                
        if self.order:
#            self.order = self.order.asList()
            # Figure out whether the sort needs to be reveresed. Yes,
            # if want descending order
            for i, (field, direction) in enumerate(self.order):
                if direction == 'asc':
                    self.order[i] = (field, False)
                else:
                    self.order[i] = (field, True)

    def filter_func(self, x):
        for field, func, test in self.where:
            print field, func, test
            if not func(x[field]):
                return False
        return True
        
    def __init__(self,  datadir, sql = None):
        self.datadir = datadir
        self.sql = sql
        self.parse(sql)
        self.data = []
        self.fields = []
        self.datasource = []
        
    def _sort(self, xs):
        for field, direction in self.order:
            xs.sort(key = lambda x : x[field], reverse = direction)
        return xs
            
    def _filter(self, xs):
        return [x for x in xs if self.filter_func(x)]


    def _get_data(self):
        if not self._data:
            self._data = self.load_data()
        return self._data
    
    def load_data(self):
        data = []
        try:
            f = open(os.path.join(self.datadir, self.filename), 'r')
        except IOError:
            pass
        else:
            basename, ext = os.path.splitext(self.filename)
            if ext == '.yaml':
                data = yaml.load(f.read())
            elif ext == '.json':
                data = json.loads(f.read())
            elif ext == '.csv':
                reader = csv.DictReader(f)
                data = [row for row in reader]

        data = self._filter(data)
        # In-place sort
        print data
        self._sort(data)
        if self.fields:
            data = [getattrs(x, self.fields) for x in data]
        return data

    def _set_data(self, data):
        self._data = data

    def _del_data(self):
        self._data = {}

    data = property(_get_data, _set_data, _del_data)

