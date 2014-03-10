class cA:
	def a(self):
		i = 0
		def b():
			print b.__class__
			#print b.__name__
		print b.__name__

ca = cA()
ca.a()
print ca.a.__name__
