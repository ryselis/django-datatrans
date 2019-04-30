from django.contrib.auth import get_permission_codename
from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.contenttypes.models import ContentType

from datatrans3 import utils
from datatrans3.models import KeyValue
from datatrans3.utils import count_model_words

def can_translate(user):
    if not user.is_authenticated:
        return False
    elif user.is_superuser:
        return True
    else:
        permission_name = getattr(settings, 'DATATRANS3_PERMISSION', None)
        if permission_name:
            opts = KeyValue._meta
            return user.has_perm("%s.%s" % (opts.app_label, get_permission_codename(permission_name, opts)))
        else:
            return user.is_staff


def _get_model_slug(model):
    ct = ContentType.objects.get_for_model(model)
    return u'%s.%s' % (ct.app_label, ct.model)


def _get_model_entry(slug):
    app_label, model_slug = slug.split('.')

    try:
        ct = ContentType.objects.get(app_label=app_label, model=model_slug)
    except ContentType.DoesNotExist:
        raise Http404(u'Content type not found.')

    model_class = ct.model_class()
    registry = utils.get_registry()
    if not model_class in registry:
        raise Http404(u'No registered model found for given query.')

    return model_class


def _get_model_stats(model, filter=lambda x: x):
    default_lang = utils.get_default_language()
    registry = utils.get_registry()
    keyvalues = filter(KeyValue.objects.for_model(model, registry[model].values()).exclude(language=default_lang).exclude(value=""))
    total = keyvalues.count()
    done = keyvalues.filter(edited=True, fuzzy=False).count()
    return (round(done * 100 / total if total > 0 else 0, 2), done, total)


@user_passes_test(can_translate, settings.LOGIN_URL)
def model_list(request):
    """
    Shows an overview of models to translate, along with the fields, languages
    and progress information.
    The context structure is defined as follows:

    context = {'models': [{'languages': [('nl', 'NL', (<percent_done>, <todo>, <total>)), ('fr', 'FR', (<percent_done>, <todo>, <total>))],
                           'field_names': [u'description'],
                           'stats': (75, 15, 20),
                           'slug': u'flags_app.flag',
                           'model_name': u'flag'}]}
    """
    registry = utils.get_registry()

    default_lang = utils.get_default_language()
    languages = [l for l in settings.DATATRANS3_LANGUAGES if l[0] != default_lang]

    models = [{'slug': _get_model_slug(model),
               'model_name': u'%s' % model._meta.verbose_name,
               'field_names': [u'%s' % f.verbose_name for f in registry[model].values()],
               'stats': _get_model_stats(model),
               'words': count_model_words(model),
               'languages': [
                    (
                        l[0],
                        l[1],
                        _get_model_stats(
                            model,
                            filter=lambda x: x.filter(language=l[0])
                        ),
                    )
                    for l in languages
                ],
               } for model in registry]

    total_words = sum(m['words'] for m in models)
    context = {'models': models, 'words': total_words, 'request': request, 'user': request.user}

    return render_to_response('datatrans/model_list.html',
                              context)


def commit_translations(request):
    translations = [
        (KeyValue.objects.get(pk=int(k.split('_')[1])), v)
        for k, v in request.POST.items() if 'translation_' in k]
    for keyvalue, translation in translations:
        empty = 'empty_%d' % keyvalue.pk in request.POST
        ignore = 'ignore_%d' % keyvalue.pk in request.POST
        if translation != '' or empty or ignore:
            if keyvalue.value != translation:
                if not ignore:
                    keyvalue.value = translation
                keyvalue.fuzzy = False
            if ignore:
                keyvalue.fuzzy = False
            keyvalue.edited = True
            keyvalue.save()


def get_context_object(model, fields, language, default_lang, object):
    object_item = {}
    object_item['name'] = str(object)
    object_item['id'] = object.id
    object_item['fields'] = object_fields = []
    for field in fields.values():
        key = model.objects.filter(pk=object.pk).values(field.name)[0][field.name]
        original = KeyValue.objects.get_keyvalue(key, default_lang, object, field.name)
        translation = KeyValue.objects.get_keyvalue(key, language, object, field.name)
        object_fields.append({
            'name': field.name,
            'verbose_name': str(field.verbose_name),
            'original': original,
            'translation': translation
        })
    return object_item


def needs_translation(model, fields, language, object):
    for field in fields.values():
        key = model.objects.filter(pk=object.pk).values(field.name)[0][field.name]
        translation = KeyValue.objects.get_keyvalue(key, language)
        if not translation.edited:
            return True
    return False


def editor(request, model, language, objects):
    registry = utils.get_registry()
    fields = registry[model]

    default_lang = utils.get_default_language()
    model_name = u'%s' % model._meta.verbose_name

    first_unedited_translation = None
    object_list = []
    for object in objects:
        context_object = get_context_object(
            model, fields, language, default_lang, object)
        object_list.append(context_object)

        if first_unedited_translation is None:
            for field in context_object['fields']:
                tr = field['translation']
                if not tr.edited:
                    first_unedited_translation = tr
                    break
    main_page_url = reverse('datatrans_model_list')
    context = {'model': model_name,
               'objects': object_list,
               'original_language': default_lang,
               'other_language': language,
               'progress': _get_model_stats(
                   model, lambda x: x.filter(language=language)),
               'first_unedited': first_unedited_translation,
               'translation_main_page_url': main_page_url,
               'request': request}

    return render(request,
        'datatrans/model_detail.html', context)


def selector(request, model, language, objects):
    fields = utils.get_registry()[model]
    for object in objects:
        if needs_translation(model, fields, language, object):
            object.todo = True
    context = {
        'model': model.__name__,
        'objects': objects
    }
    return render_to_response(
        'datatrans/object_list.html', context)


@user_passes_test(can_translate, settings.LOGIN_URL)
def object_detail(request, slug, language, object_id):
    if request.method == 'POST':
        commit_translations(request)
        return HttpResponseRedirect('.')

    model = _get_model_entry(slug)
    objects = model.objects.filter(id=int(object_id))

    return editor(request, model, language, objects)


@user_passes_test(can_translate, settings.LOGIN_URL)
def model_detail(request, slug, language):
    '''
    The context structure is defined as follows:

    context = {'model': '<name of model>',
               'objects': [{'name': '<name of object>',
                            'fields': [{
                                'name': '<name of field>',
                                'original': '<kv>',
                                'translation': '<kv>'
                            ]}],
             }
    '''

    if request.method == 'POST':
        commit_translations(request)
        return HttpResponseRedirect('.')

    model = _get_model_entry(slug)
    meta = utils.get_meta()[model]
    objects = model.objects.all()
    if getattr(meta, 'one_form_per_object', False):
        return selector(request, model, language, objects)
    else:
        return editor(request, model, language, objects)


@user_passes_test(can_translate, settings.LOGIN_URL)
def make_messages(request):
    utils.make_messages()
    return HttpResponseRedirect(reverse('datatrans_model_list'))


@user_passes_test(can_translate, settings.LOGIN_URL)
def obsolete_list(request):
    from django.db.models import Q

    default_lang = utils.get_default_language()
    all_obsoletes = utils.find_obsoletes().order_by('digest')
    obsoletes = all_obsoletes.filter(Q(edited=True) | Q(language=default_lang))

    if request.method == 'POST':
        all_obsoletes.delete()
        return HttpResponseRedirect(reverse('datatrans_obsolete_list'))

    context = {'obsoletes': obsoletes}
    return render_to_response('datatrans/obsolete_list.html', context)
