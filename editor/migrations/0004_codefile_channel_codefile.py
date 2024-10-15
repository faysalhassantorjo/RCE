# Generated by Django 5.1.2 on 2024-10-13 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0003_channel_channel_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='CodeFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='channel',
            name='codefile',
            field=models.ManyToManyField(to='editor.codefile'),
        ),
    ]