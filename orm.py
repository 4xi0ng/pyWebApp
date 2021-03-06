#coding='utf-8'

import asyncio,logging,aiomysql

def log(sql,args=()):
	logging.info('SQL:%S' % sql)
	
#创建连接池
@asyncio.coroutine
def create_pool(loop,**kw):
	logging.info('create database connection pool...')
	global __pool
	__pool = yield from aiomysql.create_pool(
		host = kw.get('host','localhost'),
		port = kw.get('port',3306),
		user = kw['user'],
		password = kw['password'],
		db = kw['db'],
		charset = kw.get('charset','utf-8'),
		autocommit = kw.get('autocommit',True),
		maxsize = kw.get('maxsize',10),
		minsize = kw.get('minsize',1),
		loop = loop)
	
#select参数化查询		
@asyncio.coroutine
def select(sql,args,size=None):
	log(sql,args)
	global __pool
	with (yield from __pool) as conn:
		cur = yield from conn.cursor(aiomysql.DictCursor)
		yield from cur.execute(sql.replace('?','%s'), args or ())
		if size:
			rs = yield from cur.fetchmany(size)
		else:
			rs = yield from cur.fetchall()
		yield from cur.close()
		logging.info('rows returned:%s' % len(rs))
		return rs
		
#insert,update,delete,参数化执行execute
@asyncio.coroutine
def execute(sql,args,autocommit=True):
	log(sql)
	with (yield from __pool) as conn:
		try:
			cur = yield from conn.cursor()
			yield from cur.execute(sql.replace('?','%s'),args)
			affected = cur.rowcount
			yield from cur.close()
		except BaseException as e:
			raise
		return affected
		
class Field(object):
	def __init__(self, name, column_type, primary_key, default):
		self.name = name
		self.column_type = column_type
		self.primary_key = primary_key
		self.default = default	
	def __str__(self):
		return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type,self.name)

class StringField(Field):
	def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
		super().__init__(name, ddl, primary_key, default)
		
class BooleanField(Field):
	def __init__(self, name=None, default=False):
		super().__init__(name, 'boolean', False, default)
		
class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)
		
class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)
		
class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

		
#定义ModelMetaclass元类:
class ModelMetaclass(type):
	'''__new__()方法接收到的参数依次是：
	1.当前准备创建的类的对象；
	2.类的名字；
	3.类继承的父类集合；
	4.类的方法集合。'''

	def __new__(cls, name, bases, attrs):
		if name=='Model':
			return type.__new__(cls, name, bases, attrs)
		tableName = attrs.get('__table__', None) or name
		logging.info('found model: %s (table: %s)' % (name, tableName))
		mappings = dict()
		fields = []
		primaryKey = None
		for k, v in attrs.items():
			if isinstance(v, Field):
				logging.info('found mapping: %s ==> %s' % (k, v))
				mappings[k] = v
				if v.primary_key:
					#主键
					if primaryKey:
						raise StandardError('Duplicate primary key for field: %s' % k)
					primaryKey = k
				else:
					fields.append(k)
		if not primaryKey:
			raise StandardError('primary key not found')
		for k in mappings.keys():
			attrs.pop(k)#从attrs中删除k
		escaped_fields = list(map(lambda f:'`%s`'%f,fields))
		attrs['__mappings__'] = mappings #保存属性和列的映射关系
		attrs['__table__'] = tableName
		attrs['__primary_key__'] = primaryKey #主键属性名
		attrs['__field__'] = fields #除主键以外的属性名
		# 构造默认的SELECT, INSERT, UPDATE和DELETE语句:
		attrs['__select__'] = 'select `%s`,%s from `%s`' % (primaryKey,', '.join(escaped_fields), tableName)
		attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
		attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
		attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
		return type.__new__(cls, name, bases, attrs)
				
class Model(dict, metaclass=ModelMetaclass):
	def __init__(self, **kw):
		super(Model, self).__init__(**kw)
		
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError(r"'Model' object has no attribute '%s'" % key)#r'\tpass'防止转义
	
	def __setattr__(self, key, value):
		self[key] = value

	def getValue(self, key):
		return getattr(self, key, None)
		
	def getValueOrDefault(self, key):
		value = getattr(self, key, None)
		if value is None:
			field  = self.__mappings__[key]
			if field.default is not None:
				value = field.default() if callable(field.default) else field.default
				logging.debug('using default value for %s: %s' % (key, str(value)))
				setattr(self, key, value)
			return value
	
	@classmethod#让所有子类调用class方法
	@asyncio.coroutine
	def findAll(cls, where=None, args=None, **kw):
		pass
			
				
		
		
		
		
		
		
		
		
		
		
		
		
		
	
		