
def log(obj: object, *args, **kwargs):
    obj_cls = obj.__class__.__name__
    print(f'[{obj_cls}]', *args)
