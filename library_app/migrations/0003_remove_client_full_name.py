# Generated by Django 4.1.7 on 2024-04-12 07:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library_app', '0002_bookclient_alter_author_full_name_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client',
            name='full_name',
        ),
    ]
