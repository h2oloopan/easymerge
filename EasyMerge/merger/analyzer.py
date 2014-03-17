import merger


class Analyzer():
    def analyze(self, path):
        print 'Analyzing ' + path + '...'
        return merger.main(path, 10, 4)
