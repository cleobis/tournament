from django.contrib.auth.models import User, Permission
from django.db import models

class RightsSupport(models.Model):
    """Container for permissions that aren't attached to models.

    https://stackoverflow.com/questions/13932774/how-can-i-use-django-permissions-without-defining-a-content-type-or-model
    """

    class Meta:

        managed = False  # No database table creation or deletion operations \
                         # will be performed for this model.

        permissions = (
            ('view', '=> Read only access'),
            ('edit', '=> Edit non-administrative data'),
            ('admin', '=> Edit all data'),
        )
    
    
    @staticmethod
    def create_view_user():
        """Returns a new user with view permissions. Used primarily for test cases."""
        
        user = User.objects.create_user('view', password='view')
        user.user_permissions.add(Permission.objects.get(content_type__app_label='accounts', codename='view'))
        user.save()
        
        return user
    
    
    @staticmethod
    def create_edit_user():
        """Returns a new user with view and edit permissions. Used primarily for test cases."""
        
        user = User.objects.create_user('edit', password='edit')
        user.user_permissions.add(Permission.objects.get(content_type__app_label='accounts', codename='view'))
        user.user_permissions.add(Permission.objects.get(content_type__app_label='accounts', codename='edit'))
        user.save()
        
        return user
    
    
    @staticmethod
    def create_admin_user():
        """Returns a new user with view, edit, and admin permissions. Used primarily for test cases."""
        
        user = User.objects.create_user('admin', password='admin')
        user.user_permissions.add(Permission.objects.get(content_type__app_label='accounts', codename='view'))
        user.user_permissions.add(Permission.objects.get(content_type__app_label='accounts', codename='edit'))
        user.user_permissions.add(Permission.objects.get(content_type__app_label='accounts', codename='admin'))
        user.save()
        
        return user
