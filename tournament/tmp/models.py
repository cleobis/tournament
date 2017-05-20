from django.db import models

from address.models import AddressField
from phonenumber_field.modelfields import PhoneNumberField

from django.core.urlresolvers import reverse


# Create your models here.
class MyAddress(models.Model):
    address1 = AddressField()
    phone_number = PhoneNumberField()
    
    def get_absolute_url(self):
        return reverse('edit-address', kwargs={'pk': self.pk})