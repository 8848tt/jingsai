from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("competitions", "0008_announcement_competition_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="announcement",
            name="remind_scope",
            field=models.CharField(
                choices=[
                    ("none", "不提醒"),
                    ("all_students", "提醒全体学生"),
                    ("competition_registrants", "提醒本竞赛已报名学生"),
                ],
                default="none",
                max_length=40,
                verbose_name="红点提醒范围",
            ),
        ),
        migrations.CreateModel(
            name="AnnouncementRead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("read_at", models.DateTimeField(auto_now_add=True, verbose_name="已读时间")),
                (
                    "announcement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reads",
                        to="competitions.announcement",
                        verbose_name="公告",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="announcement_reads",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "公告已读",
                "verbose_name_plural": "公告已读",
            },
        ),
        migrations.AddConstraint(
            model_name="announcementread",
            constraint=models.UniqueConstraint(
                fields=("user", "announcement"),
                name="uniq_announcementread_user_announcement",
            ),
        ),
    ]
