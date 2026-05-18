import os

from django.core.files.base import ContentFile
from django.db import migrations, models
import django.db.models.deletion


def copy_legacy_announcement_files(apps, schema_editor):
    Announcement = apps.get_model("competitions", "Announcement")
    AnnouncementAttachment = apps.get_model("competitions", "AnnouncementAttachment")
    for ann in Announcement.objects.all():
        f = getattr(ann, "attachment", None)
        if not f or not getattr(f, "name", None):
            continue
        try:
            f.open("rb")
            data = f.read()
            f.close()
            base = os.path.basename(f.name) or "attachment"
            row = AnnouncementAttachment(announcement=ann, original_name=base[:255])
            row.file.save(base, ContentFile(data), save=True)
        except Exception:
            continue


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0006_competition_status_registering"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnnouncementAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="announcements/%Y/%m/", verbose_name="文件")),
                ("original_name", models.CharField(blank=True, max_length=255, verbose_name="原始文件名")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="上传时间")),
                (
                    "announcement",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="competitions.announcement",
                        verbose_name="公告",
                    ),
                ),
            ],
            options={
                "verbose_name": "公告附件",
                "verbose_name_plural": "公告附件",
                "ordering": ["id"],
            },
        ),
        migrations.RunPython(copy_legacy_announcement_files, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="announcement",
            name="attachment",
        ),
    ]
