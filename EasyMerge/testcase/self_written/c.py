import d

class A:
	a= "a"
	def test(self):
		print "aa"

class B:
	b= "b"
	def test(self):
		print "bb"

d.helper(B)

a=A()
a.test()
