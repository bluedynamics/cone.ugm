from cone.app import cfg
from cone.app import main_hook
from cone.app import register_config
from cone.app import register_entry
from cone.app.security import acl_registry
from cone.ugm import browser
from cone.ugm.model.group import Group
from cone.ugm.model.groups import Groups
from cone.ugm.model.groups import groups_factory
from cone.ugm.model.settings import GeneralSettings
from cone.ugm.model.settings import ugm_cfg
from cone.ugm.model.user import User
from cone.ugm.model.users import Users
from cone.ugm.model.users import users_factory
from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from pyramid.security import Deny
from pyramid.security import Everyone
import logging


logger = logging.getLogger('cone.ugm')

# security
management_permissions = [
    'add', 'edit', 'delete',
]
user_management_permissions = [
    'add_user', 'edit_user', 'delete_user', 'manage_expiration',
]
group_management_permissions = [
    'add_group', 'edit_group', 'delete_group',
]
admin_permissions = [
    'view', 'manage_membership', 'view_portrait',
] + management_permissions \
  + user_management_permissions \
  + group_management_permissions
ugm_default_acl = [
    (Allow, 'role:editor', ['view', 'manage_membership']),
    (Allow, 'role:admin', admin_permissions),
    (Allow, 'role:manager', admin_permissions + ['manage']),
    (Allow, Everyone, ['login']),
    (Deny, Everyone, ALL_PERMISSIONS),
]
ugm_user_acl = [
    (Allow, 'system.Authenticated', ['view_portrait']),
] + ugm_default_acl


# application startup hooks
@main_hook
def initialize_ugm(config, global_config, settings):
    """Initialize UGM.
    """
    # custom UGM styles
    cfg.merged.css.protected.append((browser.static_resources, 'styles.css'))

    # custom UGM javascript
    cfg.merged.js.protected.append((browser.static_resources, 'ugm.js'))

    # UGM general settings
    ugm_cfg.ugm_settings = settings.get('ugm.config', '')
    register_config('ugm_general', GeneralSettings)

    # Localmanager config file location
    ugm_cfg.lm_settings = settings.get('ugm.localmanager_config', '')

    # Users container
    register_entry('users', users_factory)

    # Groups container
    register_entry('groups', groups_factory)

    # register default acl's
    # XXX: define permissions referring users, user, groups respective group only
    acl_registry.register(ugm_user_acl, User, 'user')
    acl_registry.register(ugm_default_acl, Users, 'users')
    acl_registry.register(ugm_default_acl, Group, 'group')
    acl_registry.register(ugm_default_acl, Groups, 'groups')

    # add translation
    config.add_translation_dirs('cone.ugm:locale/')

    # static resources
    config.add_view(browser.static_resources, name='cone.ugm.static')

    # scan browser package
    config.scan(browser)
