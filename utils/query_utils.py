# -*- coding: utf-8 -*-

"""
Various data structures used in query construction.
"""
from .tree import Node

from MysqlUtility import process_param



class Q(Node):
	"""
	Encapsulates filters as objects that can then be combined logically (using
	`&` and `|`).
	"""
	# Connection types
	AND = 'AND'
	OR = 'OR'
	default = AND

	operators = {
		'exact'      : b' = ',
		'iexact'     : b' LIKE ',
		'contains'   : b' LIKE BINARY ',
		'icontains'  : b' LIKE ',
		'regex'      : b' REGEXP BINARY ',
		'iregex'     : b' REGEXP ',
		'gt'         : b' > ',
		'gte'        : b' >= ',
		'lt'         : b' < ',
		'lte'        : b' <= ',
		'startswith' : b' LIKE BINARY ',
		'endswith'   : b' LIKE BINARY ',
		'istartswith': b' LIKE ',
		'iendswith'  : b' LIKE ',
		'in'         : b' IN ',
	}

	def __init__(self, *args, **kwargs):
		super(Q, self).__init__(children = list(args) + list(kwargs.items()))

	def _combine(self, other, conn):
		if not isinstance(other, Q):
			raise TypeError(other)
		obj = type(self)()
		obj.connector = conn
		obj.add(self, conn)
		obj.add(other, conn)
		return obj

	def __or__(self, other):
		return self._combine(other, self.OR)

	def __and__(self, other):
		return self._combine(other, self.AND)

	def __invert__(self):
		obj = type(self)()
		obj.add(self, self.AND)
		obj.negate()
		return obj

	def as_sql(self, primary_key = ""):
		"""
		@return: bytes
		"""
		r = []
		for q in self.children:
			if isinstance(q, Q):
				r.append(q.as_sql(primary_key))
			else:
				k, v = q
				sv = k.rsplit("__", 1)
				if len(sv) == 1:
					ops = "exact"
				else:
					ops = sv[1]
				lh = sv[0].encode() if sv[0] != primary_key else primary_key.encode()
				op = self.operators[ops]
				if ops == "in":
					vs = [ process_param(ve) for ve in v ]
					rh = b", ".join( vs )
					rh = b'(' + rh + b')'
				else:
					rh = process_param(v)
				r.append(lh + op + rh)
		
		c = " %s " % self.connector
		c = c.encode()
		result = c.join(r)
		if self.negated:
			neg = b"NOT"
		else:
			neg = b""
		return neg + b" ( " + result + b" )"




