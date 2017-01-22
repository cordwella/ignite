from flask_admin import AdminIndexView, BaseView, expose, form
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask import (current_app, session, flash, redirect, url_for,
                   request, send_from_directory)
from hashids import Hashids
from sqlalchemy.event import listens_for
from wtforms import TextAreaField
import os

from ignite.models import Houses, Markers


file_path = os.path.join(os.path.dirname(__file__), 'static/upload')
try:
    os.mkdir(file_path)
except OSError:
    pass


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('ad_login')

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            flash("You must be logged in to access this feature")
            return redirect(url_for('admin_login', next=request.url))


class QRGenView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

    def gen_zip(self, markers):
        import pyqrcode
        from zipfile import ZipFile
        import io

        # This ensures that it is in the package directory rather than just cwd
        __location__ = self.get_location()
        zipper = ZipFile(os.path.join(__location__, 'markers.zip'), 'w')
        hashid = Hashids(min_length=6, salt=current_app.config['HASHID_KEY'])
        for i in range(0, len(markers)):
            marker = markers[i]
            marker.url = url_for('scan_marker',
                                 scan_id=hashid.encode(marker.id),
                                 _external=True)
            buffer = io.BytesIO()
            qrcode = pyqrcode.create(marker.url)
            qrcode.svg(buffer, scale=5, background="white")
            housename = "nohouse"
            try:
                housename = marker.houses.name
            except:
                pass
            zipper.writestr(str(marker.id) + "-" +
                            marker.name + "-" +
                            housename + ".svg", buffer.getvalue())
        zipper.close()

    @expose('/gen', methods=['POST'])
    def generate_zip(self):
        markers = Markers.query.all()
        self.gen_zip(markers)
        flash("Currently generating .zip in the background, "
              "please wait a few minutes")
        return redirect(url_for('admin.index'))

    @expose('/download', methods=['POST'])
    def download_zip(self):

        try:
            __location__ = self.get_location()
            return send_from_directory(__location__,
                                       'markers.zip',
                                       as_attachment=True)
        except:
            flash("Please generate the .zip first")
            return redirect(url_for('admin.index'))

    def get_location(self):
        import os
        return os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))


class MarkerView(ModelView):
    page_size = 50
    column_searchable_list = ['name', 'batch', 'location']
    list_template = 'admin/marker_list.html'

    @action('set_on', 'Activate',
            'Are you sure you want to activate all of these markers?')
    def action_activate(self, ids):
        try:
            query = Markers.query.filter(Markers.id.in_(ids))

            for marker in query.all():
                marker.in_current_use = 1

            flash("Markers set to active")
            db.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            print(ex)
            flash("Failed to update database")

    @action('set_off', 'Deactivate',
            'Are you sure you want to set all of these makers to inactive?')
    def action_inactivate(self, ids):
        try:
            query = Markers.query.filter(Markers.id.in_(ids))

            for marker in query.all():
                marker.in_current_use = 0

            flash("Markers set to inactive")
            db.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            print(ex)
            flash("Failed to update database")

    @action('hide', 'Set Hidden',
            'Are you sure you want to hide the selected markers from '
            'the torch registry page?')
    def action_hide(self, ids):
        try:
            query = Markers.query.filter(Markers.id.in_(ids))

            for marker in query.all():
                marker.is_hidden = 1

            flash("Markers set to hidden")
            db.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            print(ex)
            flash("Failed to update database")

    @action('show', 'Set Visible',
            'Are you sure you want to include the selected '
            'markers in the torch registry page?')
    def action_make_visble(self, ids):
        try:
            query = Markers.query.filter(Markers.id.in_(ids))

            for marker in query.all():
                marker.is_hidden = 0

            flash("Markers set to hidden")
            db.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            print(ex)
            flash("Failed to update database")

    @expose('/mass')
    def mass_view(self):
        """
            Custom view for mass changing.
        """
        return self.render('admin/marker_mass.html')

    @expose('/mass/can_scan', methods=['POST'])
    def set_all_on(self):

        try:
            for marker in Markers.query.all():
                marker.in_current_use = 1

            flash("Markers set to active")
            db.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            print(ex)
            flash("Failed to update database")

        return redirect(url_for('.mass_view'))

    @expose('/mass/no_scan',  methods=['POST'])
    def set_all_off(self):

        try:
            for marker in Markers.query.all():
                marker.in_current_use = 0

            flash("Markers set to inactive")
            db.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            print(ex)
            flash("Failed to update database")

        return redirect(url_for('.mass_view'))

    @expose('/mass/hide', methods=['POST'])
    def set_all_hidden(self):
        try:
            for marker in Markers.query.all():
                marker.is_hidden = 1

            flash("Markers set to hidden")
            db.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            print(ex)
            flash("Failed to update database")

        return redirect(url_for('.mass_view'))

    @expose('/mass/visble', methods=['POST'])
    def set_all_visible(self):
        try:
            for marker in Markers.query.all():
                marker.is_hidden = 0

            flash("Markers set to hidden")
            db.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            print(ex)
            flash("Failed to update database")

        return redirect(url_for('.mass_view'))


class UserView(ModelView):
    column_exclude_list = ['pwhash']


class APageView(ModelView):
    form_overrides = {
        'content': TextAreaField
    }


class HouseView(ModelView):
    form_overrides = {
        'imagepath': form.FileUploadField
    }

    # Pass additional parameters to 'path' to FileUploadField constructor
    form_args = {
        'imagepath': {
            'label': 'File',
            'base_path': file_path,
            'allow_overwrite': False
        }
    }


@listens_for(Houses, 'after_delete')
def del_image(mapper, connection, target):
    if target.imagepath:
        # Delete image
        try:
            os.remove(op.join(file_path, target.path))
        except OSError:
            pass

        # Delete thumbnail
        try:
            os.remove(op.join(file_path,
                              form.thumbgen_filename(target.path)))
        except OSError:
            pass
