import os
#将此文件放在web根目录下运行
l = ['backup','conf','dist','www','ios','LICENSE']
www = ['static','templates']
for i in l:
	os.mkdir(i)
for i in www:
	os.mkdir('www/%s' % i)
