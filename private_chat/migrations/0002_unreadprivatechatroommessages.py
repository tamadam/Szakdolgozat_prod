# Generated by Django 3.2.13 on 2022-08-07 13:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('private_chat', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnreadPrivateChatRoomMessages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unread_messages_count', models.IntegerField(default=0)),
                ('recent_message', models.CharField(blank=True, max_length=200, null=True)),
                ('sending_time', models.DateTimeField()),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='private_chat.privatechatroom')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
