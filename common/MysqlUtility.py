# -*- coding: utf-8 -*-

"""
这些代码节选自：
# MySQL Connector/Python - MySQL driver written in Python.
# Copyright (c) 2009, 2013, Oracle and/or its affiliates. All rights reserved.

"""
import re

from mysql.connector.conversion import (MySQLConverterBase, MySQLConverter)

RE_PY_PARAM = re.compile(b'(%s)')

g_converter = MySQLConverter( "utf8", True )



class _ParamSubstitutor(object):
	"""
	Substitutes parameters into SQL statement.
	"""
	def __init__(self, params):
		self.params = params
		self.index = 0

	def __call__(self, matchobj):
		index = self.index
		self.index += 1
		return self.params[index]

	@property
	def remaining(self):
		"""Returns number of parameters remaining to be substituted"""
		return len(self.params) - self.index

def process_params_dict( params ):
	"""Process query parameters given as dictionary"""
	res = {}
	for key, value in list(params.items()):
		conv = value
		conv = g_converter.to_mysql(conv)
		conv = g_converter.escape(conv)
		conv = g_converter.quote(conv)
		res["%({})s".format(key).encode()] = conv
	return res

def process_params( params ):
	"""Process query parameters."""
	res = params

	res = [g_converter.to_mysql(i) for i in res]
	res = [g_converter.escape(i) for i in res]
	res = [g_converter.quote(i) for i in res]
	return tuple(res)

def process_param( param ):
	"""Process query parameter."""
	res = param

	res = g_converter.to_mysql(res)
	res = g_converter.escape(res)
	res = g_converter.quote(res)
	return res


def makeSafeSql(operation, params = None):
	"""convert the given operation and parames to safe sql command.

	For example, getting all rows where id is 5:
	  makeSafeSql("SELECT * FROM t1 WHERE id = %s", (5,))

	@return: bytes; 返回处理过后的sql语句
	"""
	if not operation:
		return

	stmt = ''

	if not isinstance(operation, bytes):
		stmt = operation.encode("utf-8")
	else:
		stmt = operation

	if params is not None:
		if isinstance(params, dict):
			for key, value in process_params_dict(params).items():
				stmt = stmt.replace(key, value, 1)
		elif isinstance(params, (list, tuple)):
			psub = _ParamSubstitutor(process_params(params))
			stmt = RE_PY_PARAM.sub(psub, stmt)
			if psub.remaining != 0:
				raise Exception("Not all parameters were used in the SQL statement")

	return stmt
