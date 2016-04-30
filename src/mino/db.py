from sqlalchemy.ext.declarative import declarative_base

Model=declarative_base()

session_map={}

def get_session(name='default'):
    if name not in session_map:
        raise Exception('session [%s] not in session map'%name)
    _,session_factory=session_map[name]
    return session_factory()

def setup_models(name='default'):
    if name not in session_map:
        raise Exception('session [%s] not in session map'%name)
    engine,_=session_map[name]
    Model.metadata.create_all(engine)
