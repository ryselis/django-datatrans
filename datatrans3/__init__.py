from importlib import import_module

VERSION = (0, 0, 12)


def get_version():
    if len(VERSION) > 3 and VERSION[3] != 'final':
        return '%s.%s.%s %s' % (VERSION[0], VERSION[1], VERSION[2], VERSION[3])
    else:
        return '%s.%s.%s' % (VERSION[0], VERSION[1], VERSION[2])


__version__ = get_version()


def autodiscover():
    """
    Same principle as for importing the admin modules with autodiscover() from django.contrib.admin
    """
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        try:
            import_module('%s.datatranslation' % app)
        except ImportError:
            pass
