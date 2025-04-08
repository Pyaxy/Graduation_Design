# Generated by Django 5.1.7 on 2025-04-08 06:18

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='课题标题')),
                ('description', models.TextField(verbose_name='课题描述')),
                ('requirements', models.TextField(blank=True, null=True, verbose_name='课题要求')),
                ('max_students', models.PositiveIntegerField(default=1, verbose_name='最大学生数量')),
                ('status', models.CharField(choices=[('PENDING', '待审核'), ('APPROVED', '已通过'), ('REJECTED', '已拒绝')], default='PENDING', max_length=20, verbose_name='审核状态')),
                ('review_comments', models.TextField(blank=True, null=True, verbose_name='审核意见')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('creator', models.ForeignKey(limit_choices_to={'role': 'TEACHER'}, on_delete=django.db.models.deletion.CASCADE, related_name='created_subjects', to=settings.AUTH_USER_MODEL, verbose_name='创建者')),
                ('reviewer', models.ForeignKey(blank=True, limit_choices_to={'role': 'ADMIN'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_subjects', to=settings.AUTH_USER_MODEL, verbose_name='审核人')),
            ],
            options={
                'verbose_name': '课题',
                'verbose_name_plural': '课题',
                'ordering': ['-created_at'],
            },
        ),
    ]
