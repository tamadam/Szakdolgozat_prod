# Generated by Django 3.2.13 on 2022-08-21 14:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Arena',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attacker_health_values', models.TextField(null=True)),
                ('defender_health_values', models.TextField(null=True)),
                ('date_of_fight', models.DateTimeField(auto_now_add=True, verbose_name='date of fight')),
                ('attacker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attacker', to=settings.AUTH_USER_MODEL)),
                ('defender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='defender', to=settings.AUTH_USER_MODEL)),
                ('winner_of_fight', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='winner', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
