# Generated by Django 5.1.2 on 2024-10-18 08:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0007_codefile_file_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DMRoom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('participant', models.ManyToManyField(to='editor.userprofile')),
            ],
        ),
        migrations.CreateModel(
            name='RoomMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_seen', models.BooleanField(default=False)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='editor.dmroom')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='editor.userprofile')),
            ],
        ),
        migrations.CreateModel(
            name='ReadStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_statuses', to='editor.userprofile')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='read_statuses', to='editor.roommessage')),
            ],
        ),
    ]
