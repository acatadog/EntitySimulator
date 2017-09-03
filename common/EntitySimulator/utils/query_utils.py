# -*- coding: utf-8 -*-

"""
Various data structures used in query construction.
"""
from .tree import Node

from MysqlUtility import process_param

class ExpressionBase(object):
	"""
	sql表达式生成器
	"""
	OPT = b""
	
	def __call__(self, lh, rh):
		return b" ".join((lh, self.OPT, process_param(rh)))

class Expression_exact(ExpressionBase):
	OPT = b"="

class Expression_gt(ExpressionBase):
	OPT = b">"

class Expression_gte(ExpressionBase):
	OPT = b">="

class Expression_lt(ExpressionBase):
	OPT = b"<"

class Expression_lte(ExpressionBase):
	OPT = b"<="


class Expression_iexact(ExpressionBase):
	OPT = b"ILIKE"

	def __call__(self, lh, rh):
		if rh is None:
			return b" ".join((lh, "IS NULL"))
		return b" ".join((lh, self.OPT, process_param(rh)))

class Expression_in(ExpressionBase):
	"""
	xxx IN (1,2,3)
	"""
	OPT = b"IN"

	def __call__(self, lh, rh):
		vs = [ process_param(ve) for ve in rh ]
		rhV = b'(' + b", ".join( vs ) + b')'
		return b" ".join((lh, self.OPT, rhV))

class Expression_isnull(ExpressionBase):
	"""
	xxx IS NULL/xxx IS NOT NULL
	"""
	OPT = (b'IS NOT NULL', b'IS NULL')

	def __call__(self, lh, rh):
		return b" ".join((lh, self.OPT[int(bool(rh))]))

class Expression_range(ExpressionBase):
	"""
	xxx BETWEEN 1 AND 10
	"""
	OPT = (b'BETWEEN %s AND %s')

	def __call__(self, lh, rh):
		f = process_param(rh[0])
		s = process_param(rh[1])
		return b" ".join((lh, b"BETWEEN", f, b"AND", s))


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
		'exact'      : Expression_exact(),
		'iexact'     : Expression_iexact(),
		#'contains'   : b' LIKE BINARY ',
		#'icontains'  : b' LIKE ',
		#'regex'      : b' REGEXP BINARY ',
		#'iregex'     : b' REGEXP ',
		'gt'         : Expression_gt(),
		'gte'        : Expression_gte(),
		'lt'         : Expression_lt(),
		'lte'        : Expression_lte(),
		#'startswith' : b' LIKE BINARY ',
		#'endswith'   : b' LIKE BINARY ',
		#'istartswith': b' LIKE ',
		#'iendswith'  : b' LIKE ',
		'in'         : Expression_in(),
		'isnull'     : Expression_isnull(),
		'range'      : Expression_range(),
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

	def as_sql(self, metaClass):
		"""
		@return: bytes
		"""
		r = []
		for q in self.children:
			if isinstance(q, Q):
				r.append(q.metaClass(metaClass))
			else:
				k, v = q
				sv = k.rsplit("__", 1)
				if len(sv) == 1:
					ops = "exact"
				else:
					ops = sv[1]
				lh = sv[0]
				op = self.operators[ops]
				r.append(op(metaClass.fields[lh].db_column.encode(), v))
		
		c = " %s " % self.connector
		c = c.encode()
		result = c.join(r)
		if self.negated:
			neg = b"NOT"
		else:
			neg = b""
		return neg + b" ( " + result + b" )"




