from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "学生"
        ADMIN = "admin", "管理员"
        EXPERT = "expert", "专家"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
        verbose_name="角色",
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"
