from cone.app.browser.utils import make_query
from cone.app.browser.utils import make_url
from cone.tile import Tile
from cone.tile import tile
from cone.ugm.browser.listing import PrincipalsListing
from cone.ugm.model.users import Users
from pyramid.i18n import TranslationStringFactory
from pyramid.security import has_permission
import logging


logger = logging.getLogger('cone.ugm')
_ = TranslationStringFactory('cone.ugm')


@tile('leftcolumn', 'templates/left_column.pt',
      interface=Users, permission='view')
class UsersLeftColumn(Tile):
    add_label = _('add_user', default='Add User')

    @property
    def add_target(self):
        return make_url(
            self.request,
            node=self.model.root['users'],
            query=make_query(factory=u'user')
        )

    @property
    def can_add(self):
        return has_permission('add_user', self.model, self.request)


@tile('rightcolumn', interface=Users, permission='view')
class UsersRightColumn(Tile):

    def render(self):
        return u'<div class="column right_column col-md-6">&nbsp;</div>'


@tile('columnlisting', 'templates/column_listing.pt',
      interface=Users, permission='view')
class UsersColumnListing(PrincipalsListing):
    slot = 'leftlisting'
    list_columns = PrincipalsListing.user_list_columns
    listing_attrs = PrincipalsListing.user_attrs
    listing_criteria = PrincipalsListing.user_listing_criteria
    sort_attr = PrincipalsListing.user_default_sort_column
    css = 'users'
    batchname = 'leftbatch'
    delete_label = _('delete_user', default='Delete User')
    delete_permission = 'delete_user'

    @property
    def current_id(self):
        return getattr(self.request, '_curr_listing_id', None)
