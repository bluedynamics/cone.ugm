from cone.app import compat
from cone.app.browser.utils import make_url
from cone.app.ugm import ugm_backend
from cone.ugm.utils import general_settings
from pyramid.i18n import get_localizer
from pyramid.i18n import TranslationStringFactory
from yafowil.base import ExtractionError
from yafowil.base import factory
from yafowil.base import UNSET
from yafowil.common import ascii_extractor


_ = TranslationStringFactory('cone.ugm')


###############################################################################
# Form helper functions
###############################################################################

def default_required_message(request, label):
    localizer = get_localizer(request)
    return _(
        'no_field_value_defined',
        default='No ${field} defined',
        mapping={'field': localizer.translate(_(label, default=label))}
    )


###############################################################################
# Form field factory basics
###############################################################################

def default_form_field_factory(form, label, value, required=False):
    """Default form field factory.

    A form field factory is a callable which gets passed the form tile instance,
    a label and the preset value of a form field, and returns a widget created
    by the yafowil factory.

    The default factory creates a simple text field with no validation
    or whatsoever.

    :param form: The form tile instance.
    :param label: The form field label.
    :param value: The field preset value.
    :return: ``yafowil.base.Widget`` instance created by
        ``yafowil.base.factory``.
    """
    if required and isinstance(required, bool):
        required = default_required_message(form.request, label)
    return factory(
        'field:label:error:text',
        value=value,
        props={
            'label': label,
            'required': required
        })


class FormFieldFactoryProxy(object):
    """Proxy object for form field factories.

    Provides a ``__call__`` function which acts as proxy for the concrete
    form field factory callable. Additionally holds ``attr`` attribute,
    which defines the target attribute name of the principal node.
    """

    def __init__(self, factory, attr):
        """Create form field factory proxy.

        :param factory: The form field factory proxy callable.
        :param attr: The target attribute name on the principal node.
        """
        self.factory = factory
        self.attr = attr

    def __call__(self, form, label, value):
        """Call proxied form field factory proxy callable.

        :param form: The form tile instance.
        :param label: The form field label.
        :param value: The field preset value.
        :return: ``yafowil.base.Widget`` instance created by
            ``yafowil.base.factory``.
        """
        return self.factory(form, label, value)


###############################################################################
# Form field factory registries
###############################################################################

SCOPE_USER = 'user'
SCOPE_GROUP = 'group'
BACKEND_ALL = '__all_backends__'


class _form_field(object):
    """Abstract form field factory registry and decorator.
    """

    scope = None
    """Registration scope."""

    registry = {
        SCOPE_USER: {},
        SCOPE_GROUP: {}
    }
    """Form field factory and attribute name registry by scope and UGM backend
    name.
    """

    def __init__(self, field, attr=None, backend=BACKEND_ALL):
        """Initialize decorator by attribute name and backend name.

        :param field: The form field name.
        :param attr: The target attribute name on the principal node.
        :param backend: UGM backend name the form field factory is valid for.
        """
        assert self.scope
        self.field = field
        self.attr = attr
        self.backend = backend

    def __call__(self, factory):
        """Decorator call. Register the form field factory.

        :param factory: The form field factory callable.
        :return: The form field factory callable.
        """
        scope_reg = self.registry[self.scope]
        backend_reg = scope_reg.setdefault(self.backend, {})
        backend_reg[self.field] = (factory, self.attr)
        return factory

    @classmethod
    def factory(cls, field, backend=BACKEND_ALL):
        """Lookup form field factory by field name and backend name.

        :param field: The form field name.
        :param backend: UGM backend name the form field factory is valid for.
        :return: ``FormFieldFactoryProxy`` wrapping the principal node attribute
            name and the form field factory callable.
        """
        assert cls.scope
        scope_reg = cls.registry[cls.scope]
        for backend_name in (backend, BACKEND_ALL):
            backend_reg = scope_reg.setdefault(backend_name, {})
            entry = backend_reg.get(field)
            if entry:
                return FormFieldFactoryProxy(*entry)
        return FormFieldFactoryProxy(default_form_field_factory, None)


class user_field(_form_field):
    """Form field factory registry and decorator for user principal form.
    """
    scope = SCOPE_USER


class group_field(_form_field):
    """Form field factory registry and decorator for group principal form.
    """
    scope = SCOPE_GROUP


###############################################################################
# Principal ID form field factories
###############################################################################

class PrincipalExistsExtractor(object):
    """Abstract application model aware yafowil extractor checking whether
    principal ID already exists.
    """

    def __init__(self, model):
        self.model = model

    def __call__(self, widget, data):
        """Check whether principal with ID already exists and raise
        extraction error if so.
        """
        principal_id = data.extracted
        if principal_id is UNSET:
            return principal_id
        try:
            self.model.parent.backend[principal_id]
            raise ExtractionError(self.error_message(principal_id))
        except KeyError:
            return data.extracted

    def error_message(self, principal_id):
        raise NotImplementedError(
            'Abstract ``PrincipalExistsExtractor```does '
            'not implement ``error_message``'
        )


class UserExistsExtractor(PrincipalExistsExtractor):
    """Yafowil extractor checking whether user ID already exists.
    """

    def error_message(self, principal_id):
        return _(
            'user_already_exists',
            default="User ${principal_id} already exists.",
            mapping={'principal_id': principal_id}
        )


class GroupExistsExtractor(PrincipalExistsExtractor):
    """Yafowil extractor checking whether group ID already exists.
    """

    def error_message(self, principal_id):
        return _(
            'group_already_exists',
            default="Group ${principal_id} already exists.",
            mapping={'principal_id': principal_id}
        )


class PrincipalIdFieldFactory(object):
    """Principal ID field factory.

    Creates a form widget which validates an input only contains ASCII
    characters and principal not exists. If edit form, field is not editable.
    """

    def __init__(self, principal_exists_extractor):
        self.principal_exists_extractor = principal_exists_extractor

    def __call__(self, form, label, value):
        return factory(
            'field:*ascii:*exists:label:error:text',
            value=value,
            props={
                'label': label,
                'required': default_required_message(form.request, label),
                'ascii': True
            },
            custom={
                'ascii': {
                    'extractors': [ascii_extractor]
                },
                'exists': {
                    'extractors': [self.principal_exists_extractor(form.model)]
                }
            },
            mode='edit' if form.action_resource == 'add' else 'display'
        )


# register user ID field factory
user_id_field_factory = user_field('id')(
    PrincipalIdFieldFactory(UserExistsExtractor)
)

# register group ID field factory
group_id_field_factory = group_field('id')(
    PrincipalIdFieldFactory(GroupExistsExtractor)
)


###############################################################################
# Login name form field factory
###############################################################################

class LoginNameExtractor(object):
    """Application model aware yafowil extractor checking whether optional
    login name is valid.
    """

    def __init__(self, model, login_attr):
        self.model = model
        self.login_attr = login_attr

    def __call__(self, widget, data):
        """Check whether user login name already exists and raise
        extraction error if so.
        """
        login = data.extracted
        if not login:
            return login
        res = self.model.parent.backend.search(criteria={
            self.login_attr: login
        })
        # no entries found with same login attribute set.
        if not res:
            return login
        # unchanged login attribute of current user
        if len(res) == 1 and res[0] == self.model.name:
            return login
        message = _(
            'user_login_not_unique',
            default='User login ${login} not unique.',
            mapping={'login': data.extracted}
        )
        raise ExtractionError(message)


@user_field('login')
def login_name_field_factory(form, label, value):
    settings = general_settings(form.model).attrs
    id_attr = settings.users_reserved_attrs['id']
    login_attr = settings.users_reserved_attrs['login']
    return factory(
        'field:label:error:*login:text',
        value=value,
        props={
            'label': label
        },
        custom={
            'login': {
                'extractors': [LoginNameExtractor(form.model, login_attr)]
            }
        },
        mode='skip' if id_attr == login_attr else 'edit'
    )


###############################################################################
# Password form field factory
###############################################################################

@user_field('password')
def password_field_factory(form, label, value):
    return factory(
        'field:label:error:password',
        value=value,
        props={
            'label': label,
            'required': default_required_message(form.request, label),
            'minlength': 6,
            'ascii': True
        })


###############################################################################
# Email form field factory
###############################################################################

@user_field('email')
def email_field_factory(form, label, value):
    return factory(
        'field:label:error:email',
        value=value,
        props={
            'label': label
        })


###############################################################################
# Principal form
###############################################################################

class PrincipalForm(object):
    form_name = None

    @property
    def reserved_attrs(self):
        raise NotImplementedError(
            'Abstract principal form does not implement ``reserved_attrs``'
        )

    @property
    def form_attrmap(self):
        raise NotImplementedError(
            'Abstract principal form does not implement ``form_attrmap``'
        )

    @property
    def field_factory_registry(self):
        raise NotImplementedError(
            'Abstract principal form does not '
            'implement ``field_factory_registry``'
        )

    def prepare(self):
        model = self.model
        request = self.request
        scope = self.action_resource
        self.form = form = factory(
            u'form',
            name=self.form_name,
            props={
                'action': make_url(request, node=model, resource=scope),
            })
        registry = self.field_factory_registry
        localizer = get_localizer(request)
        backend_name = ugm_backend.name
        # add reserved form fields
        for attr_name in self.reserved_attrs.keys():
            field_factory = registry.factory(attr_name, backend=backend_name)
            label = localizer.translate(_(attr_name, default=attr_name))
            value = model.attrs.get(attr_name, UNSET)
            form[attr_name] = field_factory(self, label, value)
        # add custom form fields
        form_attrmap = self.form_attrmap
        if not form_attrmap:
            return
        for attr_name, label in form_attrmap.items():
            field_factory = registry.factory(attr_name, backend=backend_name)
            value = model.attrs.get(attr_name, UNSET)
            form[attr_name] = field_factory(self, label, value)
        # add form actions
        form['save'] = factory(
            'submit',
            props={
                'action': 'save',
                'expression': True,
                'handler': self.save,
                'next': self.next,
                'label': _('save', default='Save')
            })
        if scope == 'add':
            form['cancel'] = factory(
                'submit',
                props={
                    'action': 'cancel',
                    'expression': True,
                    'handler': None,
                    'next': self.next,
                    'label': _('cancel', default='Cancel'),
                    'skip': True
                })
