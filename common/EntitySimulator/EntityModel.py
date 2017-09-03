# -*- coding: utf-8 -*-

"""
"""
import functools, inspect

import MysqlUtility

from .Fields import FieldInteger
from .Query import QuerySet


class ModelBase(type):
	"""
	Metaclass for all models.
	"""
	def __new__(cls, name, bases, attrs):
		"""
		"""
		super_new = super(ModelBase, cls).__new__

		# Also ensure initialization is only performed for subclasses of Model
		# (excluding Model class itself).
		parents = [b for b in bases if isinstance(b, ModelBase)]
		if not parents:
			return super_new(cls, name, bases, attrs)

		# Create the class.
		module = attrs.pop('__module__')
		new_attrs = {'__module__': module}
		classcell = attrs.pop('__classcell__', None)
		if classcell is not None:
			new_attrs['__classcell__'] = classcell
		new_class = super_new(cls, name, bases, new_attrs)
		attr_meta = attrs.pop('Meta', None)
		if not attr_meta:
			meta = getattr(new_class, 'Meta', None)
		else:
			meta = attr_meta
		base_meta = getattr(new_class, '_meta', None)

		# 初始化meta
		_meta = meta()
		_meta.concrete_model = None  # 这个对象是哪个EntityModel类的（由内部自动注入）
		_meta.primary_key  = ""      # 主键字段，指向Fields.Field.db_column
		_meta.primary_name = ""      # 主键名，指向fields中的key
		_meta.fields = {}            # 表字段声明
		
		new_class.add_to_class('_meta', _meta)


		# Add all attributes to the class.
		for obj_name, obj in attrs.items():
			new_class.add_to_class(obj_name, obj)

		new_class._meta.concrete_model = new_class
		new_class.objects = QuerySet(new_class)

		return new_class

	def add_to_class(cls, name, value):
		# We should call the contribute_to_class method only if it's bound
		if not inspect.isclass(value) and hasattr(value, 'contribute_to_class'):
			value.contribute_to_class(cls, name)
		else:
			setattr(cls, name, value)




class EntityModel(metaclass = ModelBase):
	"""
	"""
	# entity meta data
	class Meta:
		# -----------------------
		# 内部自动填充的参数
		# -----------------------
		concrete_model = None  # 这个对象是哪个EntityModel类的（由内部自动注入）
		primary_key  = ""      # 主键字段，指向Fields.Field.db_column
		primary_name = ""      # 主键名，指向fields中的key

		# key = attr name; value = instance of Field
		# example:
		# from .Fields import INT32, UNICODE, FLOAT
		# { "id" : INT32( "id", primary_key = True ), "name" : UNICODE( "sm_name" ), "speed" : FLOAT( "sm_speed" ) }
		fields = {}            # 表字段声明

		# -----------------------
		# 需要使用者自己填充的参数
		# -----------------------
		db_table = ""          # 数据库表名


	#_meta = None  # 指向Meta实例的变量，创建类型内部自动注入



	def __init__( self, *args, **kwargs ):
		"""
		"""
		vsD = dict(args)
		vsD.update(kwargs)
		# 初始化字段
		for k, v in self._meta.fields.items():
			if k not in vsD:
				setattr( self, k, v.default_value() )
			else:
				vv = vsD.pop(k)
				setattr( self, k, vv )
		
		# 把剩余的不属于字段的内容作为普通属性放入
		self.__dict__.update(vsD)



	@classmethod
	def get_field_def( cls, attrName ):
		"""
		"""
		return cls._meta.fields[attrName]

	@classmethod
	def get_field_column( cls, attrName ):
		"""
		"""
		return cls._meta.fields[attrName].db_column

	def get_primary_key_value( self ):
		"""
		"""
		return getattr( self, self._meta.primary_name )

	def deleteFromDB( self, callback = None ):
		"""
		从服务器中把与自己有关的数据删除
		"""
		assert self._meta.primary_key, "primary key not set!"
		self.objects.delete( callback, (self._meta.primary_name, self.get_primary_key_value()) )

	def writeToDB( self, callback = None, forceInsert = False ):
		"""
		把当前所有数据写入到数据库中。
		注意：如果self.databaseID是无效的值，那么将会出现异常
		@param forceInsert: 是否不管主键值存不存在都强行插入一条新数据
		@param callback: This optional argument is a callable object that will be called when the response from the database is received. 
		It takes two arguments. The first is a boolean indicating success or failure and the second is the instance of EntityModel or inherit.
			def callback(success, entModel):
				pass
		"""
		d = {}
		for k, t in self._meta.fields.items():
			d[k] = self.__dict__[k]
		
		d.pop(self._meta.primary_key, None)
		if self.get_primary_key_value() and not forceInsert:  # 主键已经有值了，且不强行插入数据，则只能是更新
			qs = self.objects.filter((self._meta.primary_name, self.get_primary_key_value()))
			qs.update(functools.partial(self._write_to_db_update_callback, callback), **d)
		else:							 # 主键无值，直接插入新数据
			self.objects.insert(functools.partial(self._write_to_db_insert_callback, callback), **d)

	def _write_to_db_update_callback(self, callback, success, rows):
		"""
		"""
		if callable( callback ):
			callback(success, self)

	def _write_to_db_insert_callback(self, callback, success, insertid):
		"""
		"""
		if success and isinstance(self._meta.fields[self._meta.primary_name], FieldInteger):
			setattr( self, self._meta.primary_name, insertid )

		if callable( callback ):
			callback(success, self)