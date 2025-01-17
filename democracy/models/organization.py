from .base import StringIdBaseModel
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields, TranslatableModel

class Organization(StringIdBaseModel):
    name = models.CharField(verbose_name=_('name'), max_length=255, unique=True)
    admin_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='admin_organizations'
    )
    parent = models.ForeignKey('Organization', on_delete=models.SET_NULL,
                               blank=True, null=True, related_name='children')

    class Meta:
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')

    def __str__(self):
        return self.name


class OrganizationLog(models.Model):
    action = models.TextField(verbose_name=_('Action'))
    organization = models.ForeignKey(Organization, verbose_name=_('organization'), 
                    related_name='organization_log', on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        verbose_name=_('time of creation'), default=timezone.now, editable=False, db_index=True
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('action by'),
        null=True, blank=True, related_name="%(class)s_action_by",
        editable=False, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = _('organization log')
        verbose_name_plural = _('organization logs')

    def __str__(self):
        return 'Organization Log'

class ContactPerson(TranslatableModel, StringIdBaseModel):
    organization = models.ForeignKey(Organization, verbose_name=_('organization'), related_name='contact_persons',
                                     blank=True, null=True, on_delete=models.PROTECT)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_('title'), max_length=255),
    )
    name = models.CharField(verbose_name=_('name'), max_length=50)
    phone = models.CharField(verbose_name=_('phone'), max_length=50)
    email = models.EmailField(verbose_name=_('email'))

    class Meta:
        verbose_name = _('contact person')
        verbose_name_plural = _('contact persons')
        ordering = ['name']

    def __str__(self):
        return '%s, %s / %s' % (self.name, self.title, self.organization)



