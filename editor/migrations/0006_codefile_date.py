# Generated by Django 5.1.2 on 2024-10-14 06:26

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0005_codefile_channel_alter_channel_codefile'),
    ]

    operations = [
        migrations.AddField(
            model_name='codefile',
            name='date',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now),
        ),
    ]
