# Generated manually

import os

import django.db.models.deletion
from django.db import migrations, models


def forwards_copy_attachments(apps, schema_editor):
    Submission = apps.get_model("competitions", "Submission")
    SubmissionAttachment = apps.get_model("competitions", "SubmissionAttachment")
    for s in Submission.objects.all():
        f = s.attachment
        if not f or not getattr(f, "name", None):
            continue
        base = os.path.basename(f.name) or "file"
        SubmissionAttachment.objects.create(
            submission=s,
            file=f,
            original_name=base[:255],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("competitions", "0004_reviews_per_submission_and_assignment"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubmissionAttachment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "file",
                    models.FileField(upload_to="submissions/%Y/%m/", verbose_name="文件"),
                ),
                (
                    "original_name",
                    models.CharField(blank=True, max_length=255, verbose_name="原始文件名"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="上传时间"),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="competitions.submission",
                        verbose_name="作品",
                    ),
                ),
            ],
            options={
                "verbose_name": "作品附件",
                "verbose_name_plural": "作品附件",
                "ordering": ["id"],
            },
        ),
        migrations.RunPython(forwards_copy_attachments, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="submission",
            name="work_url",
        ),
        migrations.RemoveField(
            model_name="submission",
            name="attachment",
        ),
    ]
