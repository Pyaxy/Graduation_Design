from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_pdf_file(value):
    """验证文件是否为允许的格式"""
    allowed_extensions = ['.pdf', '.docx', '.doc', '.txt', '.md']
    if not value.name.endswith(tuple(allowed_extensions)):
        raise ValidationError(
            _('只允许上传PDF、DOCX、DOC格式的文件'),
            params={'value': value},
        ) 

def validate_file_size(value):
    """验证文件大小"""
    limit = 10 * 1024 * 1024  # 10MB
    if value.size > limit:
        raise ValidationError(
            _('文件大小不能超过10MB'),
            params={'value': value},
        )