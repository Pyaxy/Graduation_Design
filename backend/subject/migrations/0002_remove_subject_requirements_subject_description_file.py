# Generated by Django 5.1.7 on 2025-04-08 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subject', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subject',
            name='requirements',
        ),
        migrations.AddField(
            model_name='subject',
            name='description_file',
            field=models.FileField(blank=True, null=True, upload_to='subject_files/', verbose_name='课题原始描述文件'),
        ),
    ]
