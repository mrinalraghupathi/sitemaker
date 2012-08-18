from pyparsing import *
import re

# Regexs
re_date = re.compile(r'(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})')
re_space = re.compile('\s+')

#Conversion functions
def make_dict(tokens):
    k = tokens[0]
    return {tokens[0] : tokens[1]}
    
def to_pair(tokens):
    return (tokens[0], tokens[1])

def to_triple(tokens):
    return (tokens[0], tokens[1], tokens[2])

def convert_ordercondition(tokens):
    if len(tokens) >= 2:
        return (tokens[0], tokens[1])
    else:
        return (tokens[0], 'asc')
        
def orderprops(tokens):
    a = []
    for i in range(2,len(tokens)):
        a.append(tokens[i])
        return [a]

def clean_up_values(tokens):
    print tokens
    return " ".join([t.replace('\'','') for t in tokens])

def to_int(tokens):
    try:
        return int(tokens[0])
    except ValueError:
        return tokens

def parse_date(val):
    m = re_date.match(val)
    if m:
        d = m.groupdict()
        try:
            dt = datetime.strptime(d['year'], d['month'], d['day'])
        except ValueError:
            raise
        else:
            return dt
                
w = Word(alphas + '_')
w1 = Word(alphanums + '_')
wf = Word(alphanums + '_-.$%#/')
op = oneOf('= < > !=')
key = w1    
values = OneOrMore(Word(alphanums + "_'"))
values = values.setParseAction(clean_up_values)

select_keyword = Suppress(Optional(Keyword('select', caseless = False)))
wildcard = Literal('*')
# wildcard = wildcard.setParseAction(lambda x : [["*"]])
fields = delimitedList(w1).setResultsName('properties')
select_fields =  (wildcard ^ fields).setResultsName('properties')
from_keyword = Suppress(Keyword('from', caseless = False))
filename = wf.setResultsName('filename')

select_clause =  Optional(select_keyword + select_fields + from_keyword) + filename

keyvalpair = (key + op + values).setParseAction(to_triple)
keyval = delimitedList(keyvalpair)

# keyval = keyval.setResultsName('where')
where_keyword = Suppress(Keyword('where', caseless = False))
where_clause =  where_keyword + keyval
where_clause = where_clause.setResultsName('where')

_order_condition = w1 + Optional(oneOf('asc desc', caseless = True))
order_condition = _order_condition.setParseAction(convert_ordercondition)
order_keyword = Suppress(Keyword('order', caseless = True) + Keyword('by'))
order_clause = order_keyword + delimitedList(order_condition).setResultsName('order')
#    orderbyclause = orderbyclause.setResultsName('order').setParseAction(lambda t : [t[2:]])
sqlparser = select_clause + Optional(where_clause) + Optional(order_clause)


def parse(parser, string):
    return parser.parseString(string)



def parse_file_listing(s):
    xs = s.split('from')
    globs = re_space.split(xs[0])
    directory = xs[1].strip()
    return dict(globs = globs,
                directory = directory)

def parse_sql(s):
    return parse(sqlparser, s)
