'''
(marble) language

Looks like lisp, but is semantically more like python or javascript.
'''

class Token(object):
	'''
	Construct resulting from parse

	Initially I wanted to mix both mutable and immutable Python types.
	However, I realized that depending on whether I wanted to mix with
	immutable or mutable, it was better to leave __new__ or __init__ 
	unimplemented.

	So I have instead decided to require that any type mixing in with Token
	must be immutable (so instead of with list, I mix with tuple).

	This way I don't touch __init__ but only override __new__
	'''
	def __new__(cls,text,begin,end,*args,**kargs):
		self = super(Token,cls).__new__(cls,*args,**kargs)
		self.text = text
		self.begin = begin
		self.end = end
		return self

class Tuple(Token,tuple):
	'''
	Tuple
	Used as function call in code.
	'''
	def evaluate(self,env):
		env.root.call_stack.append(self)
		try:
			return self[0].evaluate(env)(env,*self[1:])
		finally:
			env.root.call_stack.pop()

class Str(Token,str):
	'''
	String
	Used as variable name/symbol in code.
	'''
	def evaluate(self,env):
		return env[self]

class Qstr(Token,str):
	'''
	Quoted string
	'''
	def evaluate(self,env):
		return self

class Int(Token,int):
	def evaluate(self,env):
		return self

class Float(Token,float):
	def evaluate(self,env):
		return self

class Environment(object):
	def __init__(self,parent):
		self.parent = parent
		self.table = dict()
		if not self.parent:
			self.call_stack = []
			self.root = self
		else:
			self.root = parent.root

	def __getitem__(self,k):
		if k in self.table:
			return self.table[k]
		elif self.parent:
			return self.parent[k]
		else:
			raise KeyError(k)

	def __setitem__(self,k,v):
		if k in self.table:
			self.table[k] = v
		elif self.parent:
			self.parent[k] = v
		else:
			raise KeyError(k)

	def declare(self,k,v):
		self.table[k] = v

def parse(s):
	s += '\0'
	t = [ [] ]
	b = [    ]
	l = len(s)
	i = next(k for k in range(l) if not s[k].isspace())
	while s[i] != '\0':
		j = i

		if s[i] == '(':
			b.append(j)
			t.append([])
			i += 1

		elif s[i] == ')':
			i += 1
			start = b.pop()
			value = t.pop()
			end = i
			t[-1].append(Tuple(s,start,end,value))

		else:
			if s[i] == '"':
				i = next(k for k in range(i+1,l) if s[k] == '"' and s[k-1]!='\\') + 1
				t[-1].append(Qstr(s,j,i,eval(s[j:i])))

			else:
				i = next(k for k in range(i,l) if s[k].isspace() or s[k] in '()"\0')

				try:
					t[-1].append(Int(s,j,i,s[j:i]))
				except ValueError:
					try:
						t[-1].append(Float(s,j,i,s[j:i]))
					except ValueError:
						t[-1].append(Str(s,j,i,s[j:i]))

		i = next(k for k in range(i,l) if not s[k].isspace())
	assert len(t) == 1, t
	return t[0]

root_env = Environment(None)

root_env.declare('none',None)
root_env.declare('true',True)
root_env.declare('false',False)

def execute(xs,env = root_env):
	for x in xs:
		x.evaluate(env)

def to_function(f):
	'''
	helper function that turns given python function to act like a function
	'''
	def function(env,*args):
		return f(*[x.evaluate(env) for x in args])
	return function

def to_string(x):
	if x is None:
		x = 'none'
	elif isinstance(x,bool):
		'''
		Something I tripped up on at first, is that
		bool is a subclass of int. So this test has to come first. 
		'''
		x = 'true' if x else 'false'
	elif isinstance(x,(int,float,str)):
		x = str(x)
	elif isinstance(x,tuple):
		x = '(' + ' '.join(map(to_string,x)) + ')'
	elif isinstance(x,Environment):
		x = '<environment>'
	elif callable(x):
		x = '<callable>'
	else:
		raise TypeError(x)
	return x
root_env.declare('str',to_function(to_string))

def print_(x):
	print(to_string(x))
	return x
root_env.declare('print',to_function(print_))

def quote(env,x):
	return x
root_env.declare('quote',quote)

def get_current_environment(env):
	return env
root_env.declare('get-current-environment', get_current_environment)

def make_macro(env,env_name,arg_names,body):
	def macro(ienv,*args):
		if len(arg_names) != len(args):
			raise TypeError('expected %d argument(s), got %d' % (len(arg_names),len(args)))
		nenv = Environment(env)
		nenv.declare(env_name,ienv)
		for name, arg in zip(arg_names,args):
			nenv.declare(name,arg)
		return body.evaluate(nenv)
	return macro
root_env.declare('macro',make_macro)

def declare(env,name,value):
	value = value.evaluate(env)
	env.declare(name,value)
	return value
root_env.declare('declare',declare)

def get_item(xs,i):
	return xs[i]
root_env.declare('get-item',to_function(get_item))

def length(x):
	if isinstance(x,(list,tuple)):
		return len(x)
	else:
		raise TypeError('')
root_env.declare('length',to_function(length))

def while_(env,condition,body):
	while condition.evaluate(env):
		last = body.evaluate(env)
	return last
root_env.declare('while',while_)

def less_than(a,b):
	return a < b
root_env.declare('<',to_function(less_than))

def do(env,expressions):
	for expression in expressions:
		last = expression.evaluate(env)
	return last
root_env.declare('do',do)

def assign(env,x,e):
	if isinstance(x,str):
		env[x] = e.evaluate(env)
	else:
		raise TypeError(x)
root_env.declare('=',assign)

root_env.declare('+',to_function(lambda a, b : a + b))
root_env.declare('-',to_function(lambda a, b : a - b))
root_env.declare('*',to_function(lambda a, b : a * b))
root_env.declare('/',to_function(lambda a, b : a / b))
root_env.declare('//',to_function(lambda a, b : a // b))


s = '''
(declare i 1)
(declare xs (quote (0 1 2 3 4 5 6 7 8 9 10)))

(while (< i 10)
	(do (
		(print (+ "hey! " (str i)))
		(print (get-item xs i))
		(= i (+ i i))
	))
)


'''
execute(parse(s))

