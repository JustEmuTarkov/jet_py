class SingletonMeta(type):
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, '__instance'):
            setattr(cls, '__instance', super().__call__(*args, **kwargs))

        return getattr(cls, '__instance')


class NotFoundError(Exception):
    pass
