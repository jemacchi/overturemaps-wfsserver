# Generated by Django 3.2.25 on 2024-08-06 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('overturemaps_wfsserver_app', '0002_bboxrequestbuildingmodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='overturemapssourcemodel',
            name='dataset',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='overturemapssourcemodel',
            name='record_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]