# Generated by Django 3.2.13 on 2022-09-14 10:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0014_teamjoinrequest'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='teamjoinrequest',
            options={'ordering': ['request_date']},
        ),
    ]
