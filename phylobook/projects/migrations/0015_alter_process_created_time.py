# Generated by Django 3.2.25 on 2024-05-30 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0014_auto_20240529_1953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='created_time',
            field=models.FloatField(null=True),
        ),
    ]
