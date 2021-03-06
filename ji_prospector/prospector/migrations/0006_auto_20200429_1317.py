# Generated by Django 3.0.2 on 2020-04-29 13:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prospector', '0005_auto_20200406_1957'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('new_todo_state', models.CharField(choices=[('0_done', 'Tâche terminée'), ('1_doing', 'Tâche en cours'), ('2_pro_waits_contact', 'Pro attend sur contact'), ('3_pro_waits_presidence', 'Pro attend sur présidence'), ('4_pro_waits_treasury', 'Pro attend sur trésorerie'), ('5_contact_waits_pro', 'Contact attend sur pro')], max_length=32)),
                ('date', models.DateTimeField(auto_now=True)),
            ],
            options={
                'get_latest_by': 'date',
            },
        ),
        migrations.AddField(
            model_name='task',
            name='todo_state_logged',
            field=models.BooleanField(default=True),
        ),
        migrations.DeleteModel(
            name='EmailAddress',
        ),
        migrations.AddField(
            model_name='tasklog',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prospector.Task'),
        ),
    ]
