# Generated by Django 3.0.2 on 2020-04-29 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prospector', '0007_tasklog_old_todo_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='todo_state_logged',
            field=models.BooleanField(default=False),
        ),
    ]
