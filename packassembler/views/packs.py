from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from ..form import PackForm
from ..schema import *
from .common import *


class PackViews(ViewBase):

    @view_config(route_name='addpack', renderer='genericform.mak', permission='user')
    def addpack(self):
        post = self.request.params
        form = PackForm(post)

        if 'submit' in post and form.validate():
            try:
                pack = Pack(
                    owner=self.current_user,
                    name=form.name.data,
                    base=form.base.data,
                    rid=slugify(form.name.data)
                ).save()
                return HTTPFound(location=self.request.route_url('viewpack', id=pack.id))
            except NotUniqueError:
                form.name.errors.append('Name or Readable ID Already Exists.')

        return self.return_dict(title="Add Pack", f=form, cancel=self.request.route_url('packlist'))

    @view_config(route_name='clonepack', permission='user')
    def clonepack(self):
        current_pack = self.get_db_object(Pack, perm=False)
        try:
            new_pack = Pack(
                owner=self.current_user,
                name='[{0}] {1}'.format(self.logged_in, current_pack.name),
                mods=current_pack.mods,
                rid=self.logged_in + '-' + current_pack.rid).save()
        except NotUniqueError:
            self.request.flash_error('Already Cloned!')
            return HTTPFound(self.request.route_url('viewpack', id=current_pack.id))

        self.request.flash(current_pack.name + ' cloned successfully.')
        return HTTPFound(self.request.route_url('viewpack', id=new_pack.id))

    @view_config(route_name='editpack', renderer='genericform.mak', permission='user')
    def editpack(self):
        pack = self.get_db_object(Pack)
        post = self.request.params
        form = PackForm(post, pack)

        if 'submit' in post and form.validate():
            pack.name = form.name.data
            pack.base = form.base.data
            try:
                pack.save()

                self.request.flash('Changes saved.')
                return HTTPFound(self.request.route_url('viewpack', id=pack.id))

            except NotUniqueError:
                form.name.errors.append('A pack with that name already exists.')

        return self.return_dict(title="Edit Pack", f=form, cancel=self.request.route_url('viewpack', id=pack.id))

    @view_config(route_name='packlist', renderer='packlist.mak')
    def packlist(self):
        post = self.request.params

        if 'q' in post:
            packs = Pack.objects(name__icontains=post['q'])
        else:
            packs = Pack.objects

        return self.return_dict(title="Packs", packs=packs)

    @view_config(route_name='deletepack', permission='user')
    def deletepack(self):
        pack = self.get_db_object(Pack)
        pack.delete()

        self.request.flash(pack.name + ' deleted successfully.')
        return HTTPFound(self.request.route_url('packlist'))

    @view_config(route_name='viewpack', renderer='viewpack.mak')
    def viewpack(self):
        pack = self.get_db_object(Pack, perm=False)

        return self.return_dict(
            title=pack.name, pack=pack,
            perm=self.has_perm(pack),
            packs=self.get_add_pack_data()
        )

    @view_config(route_name='viewpack', request_method='GET', accept='application/json', xhr=True)
    def viewpack_json(self):
        pack = self.get_db_object(Pack, perm=False)

        return Response(pack.to_json(), content_type='application/json')

    @view_config(route_name='mcuxmlpack')
    def mcuxmlpack(self):
        pack = self.get_db_object(Pack, perm=False)

        if pack.builds:
            return HTTPFound(self.request.route_url('mcuxml', id=pack.builds[-1].id))
        else:
            return Response('No builds available.')

    @view_config(route_name='downloadpack')
    def downloadpack(self):
        pack = self.get_db_object(Pack, perm=False)

        if pack.builds:
            return HTTPFound(self.request.route_url('downloadbuild', id=pack.builds[-1].id))
        else:
            return Response('No builds available.')

    @view_config(route_name='addpackmod', permission='user')
    def addpackmod(self):
        post = self.request.params

        if self.pack_perm():
            Pack.objects(id=self.request.matchdict['id']).update_one(
                add_to_set__mods=post.getall('mods'))

            self.request.flash('Mod(s) added successfully.')
            return HTTPFound(self.request.route_url('viewpack', id=self.request.matchdict['id']))
        else:
            return HTTPForbidden()

    @view_config(route_name='removepackmod', permission='user')
    def removepackmod(self):
        if self.pack_perm():
            Pack.objects(id=self.request.matchdict['id']).update_one(
                pull_all__mods=self.request.params.getall('mods'))

            self.request.flash('Mod(s) removed successfully.')
            return HTTPFound(self.request.route_url('viewpack', id=self.request.matchdict['id']))
        else:
            return HTTPForbidden()

    @view_config(route_name='addbasepack', permission='user')
    def addbasepack(self):
        post = self.request.params

        if self.pack_perm():
            Pack.objects(id=self.request.matchdict['id']).update_one(
                add_to_set__bases=[x for x in post.getall('bases') if x != self.request.matchdict['id']])
            return HTTPFound(self.request.route_url('viewpack', id=self.request.matchdict['id']))
        else:
            return HTTPForbidden()

    @view_config(route_name='removebasepack', permission='user')
    def removebasepack(self):
        if self.pack_perm():
            Pack.objects(id=self.request.matchdict['id']).update_one(
                pull_all__bases=self.request.params.getall('bases'))
            return HTTPFound(self.request.route_url('viewpack', id=self.request.matchdict['id']))
        else:
            return HTTPForbidden()

    def pack_perm(self):
        return self.has_perm(Pack.objects(id=self.request.matchdict['id']).only('owner').first())
