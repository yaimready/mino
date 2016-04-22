import sys,imp
import logging

from functools import partial
import tornado.ioloop
from tornado.web import RequestHandler
from tornado.options import define,options,parse_command_line

class urlhandler_partial:
    
    def __init__(self,func,*args):
        self._func=func
        self._args=args
        
    def __call__(self,req):
        self._func(req,*self._args)

def load_module(name,folder):
    args=imp.find_module(name,[folder])
    return imp.load_module('mino.%s'%name,*args)

def load_logfiles(logfiles):
    for name,filename in logfiles.items():
        log_handler=logging.FileHandler(filename)
        log_formatter=logging.Formatter('%(asctime)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
        log_handler.setFormatter(log_formatter)
        logging.getLogger(name).addHandler(log_handler)

def load_urlpatterns(urlpatterns):
    handlers=[]
    proxyfunc_map={}
    overloads=[
        'initialize','prepare','on_finish',
        'get','head','post','delete',
        'patch','put','options'
        ]
    for urlpattern in urlpatterns:
        url,urlhandler=urlpattern[:2]
        proxyname=str(urlhandler)
        if proxyname in proxyfunc_map:
            proxyfuncs=proxyfunc_map[proxyname]
        else:
            if isinstance(urlhandler,type):
                proxyfuncs={}
                proxy=urlhandler(*urlpattern[2:])
                for k in overloads:
                    fn=getattr(proxy,k,None)
                    if fn: proxyfuncs[k]=fn
            elif callable(urlhandler):
                proxy=urlhandler_partial(urlhandler,*urlpattern[2:])
                proxyfuncs={'get':proxy,'post':proxy}
            else:
                raise Exception('urlhandler for [%s] is not function or type'%url)
            proxyfunc_map[proxyname]=proxyfuncs
        UrlHandler=type('UrlHandler_%s'%(urlhandler.__name__),(RequestHandler,),{
            '__init__':urlhandler_init_function,
            '_proxyfuncs':proxyfuncs
        })
        handlers.append((url,UrlHandler))
    return handlers

def urlhandler_init_function(self,*args,**kwargs):
    RequestHandler.__init__(self,*args,**kwargs)
    for name,fn in self._proxyfuncs.items():
        setattr(self,name,partial(fn,self))

def start_server(root):
    # load config file
    conf=load_module('conf',root)
    # initialize logfiles
    load_logfiles(conf.app_logfiles)
    # initialize url patterns
    urls=load_module('urls',root)
    urlhandlers=load_urlpatterns(urls.urlpatterns)
    # build appliation object
    application=tornado.web.Application(urlhandlers,**conf.app_settings)
    # build options and parse command line
    for name,args in conf.app_options.items():
        define(name,**args)
    parse_command_line()
    # start server loop
    logging.info('Mino ( based on Tornado ) Running!')
    application.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
