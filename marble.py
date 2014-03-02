'''
(marble)
'''

'''
------------------------------------------------------------------------------
PART 1 -----------------------------------------------------------------------
------------------------------------------------------------------------------

Parsing

isntances of subclasses of `Token` are essentially just one of the immutable
builtin Python types with some extra data

parse function takes a string and returns a `list` of instances of subclasses
of `Token` with all the proper metadata filled in.

'''
from sys import stdout, stdin

class Token(object):
	def __new__(cls,text,begin,end,*args,**kargs):
		self = super(Token,cls).__new__(cls,*args,**kargs)
		self.text = text
		self.begin = begin
		self.end = end
		return self

class Int(Token,int): pass
class Float(Token,float): pass
class Name(Token,str): pass
class Str(Token,str): pass
class Tuple(Token,tuple): pass

def parse(s):
	s += '\0'
	t = [ [] ]
	b = [    ]
	i = next(k for k in range(len(s)) if not s[k].isspace())
	while s[i]!='\0':
		j = i
		if s[i] == '(':
			t.append([])
			b.append(i)
			i += 1
		elif s[i] == ')':
			i += 1
			t[-2].append(Tuple(s,b.pop(),i,t.pop()))
		elif s[i] == '"':
			i=next(
				k for k in range(i+1,len(s))if s[k]=='"'and s[k-1]!='\\')+1
			t[-1].append(Str(s,j,i,eval(s[j:i])))
		else:
			i=next(
				k for k in range(i,len(s))if s[k]in'"()\0'or s[k].isspace())
			x = s[j:i]
			try:
				x = Int(s,j,i,x)
			except ValueError:
				try:
					x = Float(s,j,i,x)
				except ValueError:
					x = Name(s,j,i,x)
			t[-1].append(x)
		i = next(k for k in range(i,len(s)) if not s[k].isspace())
	return t[0]


'''
------------------------------------------------------------------------------
PART 2 -----------------------------------------------------------------------
------------------------------------------------------------------------------

environment (and builtin functions)

In this PART we define functions that are going to be callable from the
(marble) langauge.

The goal of this part is to create carefully chosen primitives for (marble)
that it becomes a practical language.
'''

def function(f):
	return lambda env, *args : f(*[evaluate(env,x) for x in args])

def evaluate(env,x):
	if isinstance(x,(Int,Float,Str)):
		return x
	elif isinstance(x,Name):
		x = str(x)
		while x not in env:
			try:
				env = env['__parent__']
			except KeyError:
				raise KeyError(x)
		return env[x]
	elif isinstance(x,Tuple):
		return evaluate(env,x[0])(env,*x[1:])
	else:
		raise Exception()

def execute(env,xs):
	e = {'__parent__' : env}
	for x in xs:
		evaluate(e,x)

def run(env,s):
	execute(env,parse(s))

def str_(x):
	return (
		'none'  if x is None else
		'true'  if x is True else
		'false' if x is False else
		'('+' '.join(map(str_,x))+')' if isinstance(x,Tuple) else
		str(x))

def repr_(x):
	return (
		'none'  if x is None else
		'true'  if x is True else
		'false' if x is False else
		str(x)  if isinstance(x,Name) else
		'('+' '.join(map(repr_,x))+')' if isinstance(x,Tuple) else
		repr(x))

def print_(x):
	print(str_(x))

def quote(env,x):
	return x

def declare(env,name,value):
	value = evaluate(env,value)
	env[str(name)] = value
	return value

def assign(env,name,value):
	name =str(name)
	value = evaluate(env,value)
	while name not in env:
		try:
			env = env['__parent__']
		except KeyError:
			raise KeyError(name)
	env[name] = value
	return value

def lambda_(env,argnames,body):
	def lambda_instance(ienv,*args):
		if len(argnames) != len(args):
			raise TypeError((len(argnames),argnames,len(args),args))
		nenv = {name:evaluate(ienv,arg) for name, arg in zip(argnames,args)}
		nenv['__parent__'] = env
		return evaluate(nenv,body)
	return lambda_instance

def while_(env,condition,body):
	while evaluate(env,condition):
		last = evaluate(env,body)
	return last

def do(env,expressions):
	for expression in expressions:
		last = evaluate(env,expression)
	return last

env = {
	'none'    : None,
	'true'    : True,
	'false'   : False,

	'eval'    : function(evaluate),
	'str'     : function(str_),
	'repr'    : function(repr_),
	'print'   : function(print_),

	'quote'   : quote,
	'declare' : declare,
	'\\'      : lambda_,
	'='       : assign,

	'+'       : function(lambda a, b: a + b),
	'-'       : function(lambda a, b: a - b),
	'*'       : function(lambda a, b: a * b),
	'/'       : function(lambda a, b: a / b),
	'//'      : function(lambda a, b: a // b),
	'**'      : function(lambda a, b: a ** b),
	'<'       : function(lambda a, b: a <  b),
	'<='      : function(lambda a, b: a <= b),
	'>'       : function(lambda a, b: a >  b),
	'>='      : function(lambda a, b: a >= b),
	'[]'      : function(lambda a, b: a[b]),
	'length'  : function(lambda x : len(x)),

	'tuple?'  : function(lambda x : isinstance(x,tuple)),
	'int?'    : function(lambda x : isinstance(x,int)),
	'float?'  : function(lambda x : isinstance(x,float)),
	'str?'    : function(lambda x : isinstance(x,str))),

	'while'   : while_,
	'do'      : do
}

run(env,'''
(declare i 0)
(declare f (\ (a b c) (+ (+ a b) c)))


(while (< i 10)
	(do(
		(print (f i i i))
		(= i (+ i 1))
	))
)


''')