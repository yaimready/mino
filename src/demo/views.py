
class DemoHandler(object):

    def __init__(self):
        pass

    def get(self,req):
        req.write('<h1>Hello,World</h1>')
