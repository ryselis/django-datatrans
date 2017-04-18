# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='FieldWordCount',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('total_words', models.IntegerField(default=0)),
                ('valid', models.BooleanField(default=False)),
                ('field', models.CharField(db_index=True, max_length=64)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='KeyValue',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('object_id', models.PositiveIntegerField(null=True, default=None)),
                ('field', models.CharField(max_length=255)),
                ('language', models.CharField(db_index=True, choices=[('lt', 'Lithuanian'), ('en', 'English'), ('ru', 'Russian')], max_length=5)),
                ('value', models.TextField(blank=True)),
                ('edited', models.BooleanField(default=False)),
                ('fuzzy', models.BooleanField(default=False)),
                ('digest', models.CharField(db_index=True, max_length=40)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(null=True, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ModelWordCount',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('total_words', models.IntegerField(default=0)),
                ('valid', models.BooleanField(default=False)),
                ('content_type', models.OneToOneField(to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='keyvalue',
            unique_together=set([('language', 'content_type', 'field', 'object_id', 'digest')]),
        ),
        migrations.AlterUniqueTogether(
            name='fieldwordcount',
            unique_together=set([('content_type', 'field')]),
        ),
    ]
