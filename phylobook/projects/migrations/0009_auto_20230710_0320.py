# Generated by Django 3.2.20 on 2023-07-10 03:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0008_auto_20230705_1801'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lineage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(max_length=256)),
                ('lineage_name', models.CharField(max_length=256)),
            ],
            options={
                'verbose_name_plural': 'Lineages',
                'unique_together': {('color', 'lineage_name')},
            },
        ),
        migrations.CreateModel(
            name='TreeLineage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lineage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.lineage')),
                ('tree', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.tree')),
            ],
            options={
                'unique_together': {('tree', 'lineage')},
            },
        ),
        migrations.AddField(
            model_name='tree',
            name='lineages',
            field=models.ManyToManyField(blank=True, related_name='trees', through='projects.TreeLineage', to='projects.Lineage'),
        ),
    ]