def fb(self, a):
	print self.t
	print a
	self.fa(a)

class T:
	t = "t"
	def fa(self,a):
		return fb(self,a)

tT = T()
tT.fa("a")
