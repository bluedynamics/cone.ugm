from cone.tile import (
    tile,
    Tile,
)
from cone.app.browser.utils import (
    make_url,
    make_query,
)
from cone.ugm.model.interfaces import IUsers
from cone.ugm.browser.batch import ColumnBatch
from cone.ugm.browser.listing import ColumnListing


@tile('leftcolumn', 'templates/left_column.pt',
      interface=IUsers, permission='view')
class UsersLeftColumn(Tile):

    add_label = u"Add User"

    @property
    def add_target(self):
        return make_url(self.request,
                        node=self.model.root['users'],
                        query=make_query(factory=u'user'))


@tile('rightcolumn', interface=IUsers, permission='view')
class UsersRightColumn(Tile):

    def render(self):
        return u'<div class="column right_column">&nbsp;</div>'


@tile('columnlisting', 'templates/column_listing.pt',
      interface=IUsers, permission='view')
class UsersColumnListing(ColumnListing):

    slot = 'leftlisting'
    list_columns = ['name', 'surname', 'email']
    css = 'users'
    batchname = 'leftbatch'

    @property
    def current_id(self):
        return self.request.get('_curr_listing_id')

    @property
    def query_items(self):
        name_attr, surname_attr, email_attr, sort_attr = self.user_attrs
        ret = list()
        try:
            attrlist = [name_attr, surname_attr, email_attr]
            users = self.model.ldap_users
            result = users.search(criteria=None, attrlist=attrlist)
        except Exception, e:
            print 'Query Failed: ' + str(e)
            return []
        for key, attrs in result:
            target = make_url(self.request,
                              node=self.model,
                              resource=key)
            name = self.extract_raw(attrs, name_attr)
            surname = self.extract_raw(attrs, surname_attr)
            email = self.extract_raw(attrs, email_attr)
            sort = self.extract_raw(attrs, sort_attr)
            head = self.itemhead(name, surname, email)
            current = self.current_id == key and True or False

            action_id = 'delete_item'
            action_title = 'Delete User'
            delete_action = self.create_action(
                action_id, True, action_title, target)
            
            item = self.create_item(
                sort, target, head, current, [delete_action])
            ret.append(item)
        return ret
