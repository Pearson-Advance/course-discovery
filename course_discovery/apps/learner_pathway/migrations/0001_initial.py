# Generated by Django 3.2.8 on 2021-11-26 13:17

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LearnerPathway',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('name', models.CharField(help_text='Pathway name', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='LearnerPathwayStep',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('pathway', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='learner_pathway.learnerpathway')),
            ],
        ),
    ]