import sys
import logging

from functools import partial
import tornado.ioloop
from tornado.web import RequestHandler,StaticFileHandler
from tornado.options import define,options,parse_command_line

class urlhandler_partial:
    
    def __init__(self,func,*args):
        self._func=func
        self._args=args
        
    def __call__(self,req,*args):
        print(self,args)
        self._func(req,*self._args)

def load_module(name,folder,imp):
    args=imp.find_module(name,[folder])
    if isinstance(args,tuple):
        return imp.load_module('mino.%s'%name,*args)
    else:
        return imp.load_module(name)

def load_logfiles(logfiles):
    for name,filename in logfiles.items():
        log_handler=logging.FileHandler(filename)
        log_formatter=logging.Formatter('%(asctime)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
        log_handler.setFormatter(log_formatter)
        logging.getLogger(name).addHandler(log_handler)

def load_staticpaths(staticpaths):
    handlers=[]
    for url,path in staticpaths.items():
        handlers.append((url,StaticFileHandler,{'path':path}))
    return handlers

def load_urlpatterns(urlpatterns):
    handlers=[]
    proxy_map={}
    overloads=[
        'initialize','prepare','on_finish',
        'get','head','post','delete',
        'patch','put','options'
        ]
    sn=0
    for urlpattern in urlpatterns:
        url,urlhandler=urlpattern[:2]
        proxyname=str(urlhandler)
        if isinstance(urlhandler,type):
            proxyfuncs={}
            if proxyname in proxy_map:
                proxy=proxy_map[proxyname]
            else:
                proxy=urlhandler()
                proxy_map[proxyname]=proxy
            for k in overloads:
                fn=getattr(proxy,k,None)
                if fn:
                    proxyfuncs[k]=urlhandler_partial(fn,*urlpattern[2:])
        elif callable(urlhandler):
            proxy=urlhandler_partial(urlhandler,*urlpattern[2:])
            proxyfuncs={'get':proxy,'post':proxy}
        else:
            raise Exception('urlhandler for [%s] is not function or type'%url)
        UrlHandler=type('UrlHandler_%d'%sn,(RequestHandler,),{
            '__init__':urlhandler_init_function,
            '_proxyfuncs':proxyfuncs
        })
        handlers.append((url,UrlHandler))
        sn+=1
    return handlers

def urlhandler_init_function(self,*args,**kwargs):
    RequestHandler.__init__(self,*args,**kwargs)
    for name,fn in self._proxyfuncs.items():
        setattr(self,name,partial(fn,self))

def start_server(root,imp):
    # load config file
    conf=load_module('conf',root,imp)
    # initialize logfiles
    load_logfiles(conf.app_logfiles)
    # initialize url patterns
    urls=load_module('urls',root,imp)
    urlhandlers=load_urlpatterns(urls.urlpatterns)
    urlhandlers+=load_staticpaths(conf.app_staticpaths)
    # build appliation object
    application=tornado.web.Application(urlhandlers,**conf.app_settings)
    # build options and parse command line
    for name,args in conf.app_options.items():
        define(name,**args)
    parse_command_line()
    # start server loop
    logging.getLogger('mino').info('Mino ( based on Tornado ) Running @ Port %d!'%(options.port))
    application.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
