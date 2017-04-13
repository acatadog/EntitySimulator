# -*- coding: utf-8 -*-

"""
"""
import functools

from KBEDebug import *

from MysqlUtility import process_param

class Field( object ):
	"""
	表字段定义
	"""
	def __init__(self, db_column = None, primary_key = False, default = None):
		"""
		"""
		self.model = None     # EntityModel实例，由self.contribute_to_class()注入
		self.db_column = db_column	  # 数据库字段名
		self.attrname = None  # 在self.model中的属性名
		self.primary_key = primary_key
		self.default = default

	def __str__(self):
		"""
		Return "model_label.field_name" for fields attached to
		models.
		"""
		if not hasattr(self, 'model') or not self.model:
			return super(Field, self).__str__()
		return '%s.%s(%s)' % (self.model._meta.table_name, self.attrname, self.db_column)

	def __repr__(self):
		"""
		Displays the module, class and name of the field.
		"""
		path = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
		name = getattr(self, 'name', None)
		if name is not None:
			return '<%s: %s>' % (path, name)
		return '<%s>' % path

	def set_attributes_from_name(self, attrname):
		assert self.attrname is None, "self.attrname = '%s', new '%s'" % (self.attrname, attrname)
		self.attrname = attrname
		if not self.db_column:
			self.db_column = attrname

	def contribute_to_class(self, cls, name):
		"""
		Register the field with the model class it belongs to.

		If private_only is True, a separate instance of this field will be
		created for every subclass of cls, even if cls is not an abstract
		model.
		"""
		self.set_attributes_from_name(name)
		self.model = cls
		cls._meta.fields[name] = self
		#setattr(cls, name, self.default_value()) # 不应该为类模块设置初始化值，这是__init__()的事情
		if self.primary_key:
			assert not cls._meta.primary_key, "can't has more than one primary key. current = '%s', new = '%s'" % (cls._meta.primary_key, self.db_column)
			cls._meta.primary_key = self.db_column
			cls._meta.primary_name = self.attrname

	def default_value(self):
		"""
		返回默认值
		"""
		return self.default

	def to_python(self, value):
		"""
		把来自数据库的数据转換成python的数据
		"""
		raise NotImplementedError

	def to_db(self, value):
		"""
		把python类型的数据转換为数据库的数据
		"""
		raise NotImplementedError


class FieldInteger( Field ):
	"""
	整数类型
	"""
	def to_python(self, value):
		"""
		把来自数据库的数据转換成python的数据
		"""
		return int(value) if value else 0

	def default_value(self):
		"""
		返回默认值
		"""
		return self.default if self.default else 0

	def to_db(self, value):
		"""
		把python类型的数据转換为数据库的数据
		"""
		return process_param(int(value))

class FieldFloat( Field ):
	"""
	浮点数类型
	"""
	def to_python(self, value):
		"""
		把来自数据库的数据转換成python的数据
		"""
		return float(value) if value else 0

	def default_value(self):
		"""
		返回默认值
		"""
		return self.default if self.default else 0.0

	def to_db(self, value):
		"""
		把python类型的数据转換为数据库的数据
		"""
		return process_param(float(value))

class FieldUnicode( Field ):
	"""
	unicode类型
	"""
	def __init__(self, db_column = None, encoding = 'utf-8', **kw):
		"""
		"""
		Field.__init__(self, db_column, **kw)
		self.encoding = encoding   # 字符编码

	def default_value(self):
		"""
		返回默认值
		"""
		return self.default if self.default else ""

	def to_python(self, value):
		"""
		把来自数据库的数据转換成python的数据
		"""
		return value.decode( self.encoding ) if value else ""

	def to_db(self, value):
		"""
		把python类型的数据转換为数据库的数据
		"""
		return process_param(str(value))

class FieldBytes( Field ):
	"""
	bytes类型——二进制数据，也可以认为是c++中的char[]
	"""
	def to_python(self, value):
		"""
		把来自数据库的数据转換成python的数据
		"""
		return value if value is not None else bytes()

	def default_value(self):
		"""
		返回默认值
		"""
		return self.default if self.default else b""

	def to_db(self, value):
		"""
		把python类型的数据转換为数据库的数据
		"""
		return process_param(bytes(value))


class FieldFixedArray( Field ):
	"""
	数组类型
	"""
	def __init__(self, datatype = None, **kw):
		"""
		@param datatype: Field，继承于Field的类实例
						 例如：FieldFixedArray("prices", INT8(None))
		"""
		Field.__init__(self, **kw)
		self.datatype = datatype

	def default_value(self):
		"""
		返回默认值
		"""
		return self.default if self.default else list()

class FieldFixedTuple( Field ):
	"""
	数组类型
	"""
	def __init__(self, datatype = None, **kw):
		"""
		@param datatype: Field，继承于Field的类实例
						 例如：FieldFixedTuple("prices", INT8(None))
		"""
		Field.__init__(self, **kw)
		self.datatype = datatype

	def default_value(self):
		"""
		返回默认值
		"""
		return self.default if self.default else tuple()

class FieldFixedDict( Field ):
	"""
	数组类型
	"""
	def __init__(self, datatypedict, **kw):
		"""
		@param datatypedict: dict like as { "key" : Field, ... }
		"""
		Field.__init__(self, **kw)
		self.datatypedict = dict(datatypedict)

	def default_value(self):
		"""
		返回默认值
		"""
		if self.default:
			return self.default
			
		r = {}
		for k, v in self.datatypedict.items():
			r[k] = v.default_value()
		return r

	def to_db(self, value):
		"""
		把python类型的数据转換为数据库的数据
		"""
		r = {}
		for k, v in self.datatypedict.items():
			if k in value:
				r[k] = v.to_db(value[k])
			else:
				r[k] = process_param(v.to_db(v.default_value()))
		return r





INT8       = FieldInteger
UINT8      = FieldInteger
INT16      = FieldInteger
UINT16     = FieldInteger
INT32      = FieldInteger
UINT32     = FieldInteger
INT64      = FieldInteger
UINT64     = FieldInteger
UNICODE    = FieldUnicode
BLOB       = FieldBytes
FLOAT      = FieldFloat
DOUBLE     = FieldFloat
#ARRAY      = FieldFixedArray  # un-support
#TUPLE      = FieldFixedTuple  # un-support
#FIXED_DICT = FieldFixedDict   # un-support


