# Generated by Django 5.1.2 on 2024-10-13 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0002_rename_channelname_channel'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='channel_picture',
            field=models.ImageField(default='profile_pictures/default.jpg', upload_to='profile_pictures/'),
        ),
    ]