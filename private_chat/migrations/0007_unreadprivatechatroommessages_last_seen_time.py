# Generated by Django 3.2.13 on 2022-10-06 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('private_chat', '0006_remove_unreadprivatechatroommessages_last_seen_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='unreadprivatechatroommessages',
            name='last_seen_time',
            field=models.DateTimeField(null=True),
        ),
    ]
