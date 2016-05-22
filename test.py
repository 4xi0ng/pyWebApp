import orm
from models import User, Blog, Comment

def test():
	yield from orm.create_pool(user='root', password='root', database='awesome')
	u = User(name='Test', email='aaa@qq.com', passwd='123456', image='about:blank')
	
	yield from u.save()
	
	for x in test():
		pass