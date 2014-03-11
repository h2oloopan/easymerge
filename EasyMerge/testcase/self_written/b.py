import os

class T:
	aa = "a"
	def __init__(self):
		self.bb = 1.0
	def test(self):
		pass

class T2:
	aa = "a"
	def __init__(self):
		self.bb = 1.0
	def test(self):
		pass
		

c = T2()

if 5==0:
	print "E"
else:
	print "OK"

print c
print str(c)

def b(c,i=1):
	def cc():
		print "cc here"
	print cc()
	print c
	print str(c)
	if c:	
		return c
	else:
		return None

print 5
print 6
print 7
