# Generated by Django 2.2.28 on 2023-03-10 08:34

from django.conf import settings
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('democracy', '0059_add_organization_log'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthMethod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False, verbose_name='time of creation')),
                ('modified_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='time of last modification')),
                ('published', models.BooleanField(db_index=True, default=True, verbose_name='public')),
                ('deleted_at', models.DateTimeField(blank=True, default=None, editable=False, null=True, verbose_name='time of deletion')),
                ('deleted', models.BooleanField(db_index=True, default=False, editable=False, verbose_name='deleted')),
                ('name', models.CharField(default='', max_length=200, verbose_name='name')),
                ('amr', models.CharField(help_text='id of the authentication method', max_length=100, unique=True)),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authmethod_created', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('deleted_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authmethod_deleted', to=settings.AUTH_USER_MODEL, verbose_name='deleted by')),
                ('modified_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authmethod_modified', to=settings.AUTH_USER_MODEL, verbose_name='last modified by')),
            ],
            options={
                'verbose_name': 'Authentication method',
                'verbose_name_plural': 'Authentication methods',
            },
        ),
        migrations.AddField(
            model_name='hearing',
            name='visible_for_auth_methods',
            field=models.ManyToManyField(blank=True, help_text='Only users who use given authentication methods are allowed to see this hearing', related_name='hearings', to='democracy.AuthMethod', verbose_name='Visible for authentication methods'),
        ),
    ]
