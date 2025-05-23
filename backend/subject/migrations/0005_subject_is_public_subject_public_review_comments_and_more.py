# Generated by Django 5.1.7 on 2025-04-21 04:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subject', '0004_alter_subject_description_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='is_public',
            field=models.BooleanField(default=False, verbose_name='是否申请公开'),
        ),
        migrations.AddField(
            model_name='subject',
            name='public_review_comments',
            field=models.TextField(blank=True, null=True, verbose_name='公开审核意见'),
        ),
        migrations.AddField(
            model_name='subject',
            name='public_reviewer',
            field=models.ForeignKey(blank=True, limit_choices_to={'role': 'ADMIN'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='public_reviewed_subjects', to=settings.AUTH_USER_MODEL, verbose_name='公开审核人'),
        ),
        migrations.AddField(
            model_name='subject',
            name='public_status',
            field=models.CharField(choices=[('NOT_APPLIED', '未申请'), ('PENDING', '待审核'), ('APPROVED', '已通过'), ('REJECTED', '已拒绝')], default='NOT_APPLIED', max_length=20, verbose_name='公开状态'),
        ),
        migrations.CreateModel(
            name='PublicSubject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='课题标题')),
                ('description', models.TextField(verbose_name='课题描述')),
                ('description_file', models.FileField(blank=True, null=True, upload_to='public_subject_files/', verbose_name='课题原始描述文件')),
                ('max_students', models.PositiveIntegerField(default=1, verbose_name='最大学生数量')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='公开时间')),
                ('version', models.PositiveIntegerField(default=1, verbose_name='版本号')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='public_created_subjects', to=settings.AUTH_USER_MODEL, verbose_name='创建者')),
                ('original_subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='public_versions', to='subject.subject', verbose_name='原始课题')),
            ],
            options={
                'verbose_name': '公开课题',
                'verbose_name_plural': '公开课题',
                'ordering': ['-created_at'],
            },
        ),
    ]
