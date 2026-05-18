# Generated manually

from datetime import timedelta

from django.db import migrations, models


def forwards_fill_competition_times(apps, schema_editor):
    Competition = apps.get_model("competitions", "Competition")
    for c in Competition.objects.all():
        end = c.submission_deadline
        start = c.registration_end
        if start and end and start >= end:
            start = end - timedelta(hours=1)
        c.competition_end = end
        c.competition_start = start
        c.save(update_fields=["competition_start", "competition_end"])


class Migration(migrations.Migration):

    dependencies = [
        ("competitions", "0002_announcement_attachment_alter_announcement_body_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="competition",
            name="competition_start",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="比赛开始时间"
            ),
        ),
        migrations.AddField(
            model_name="competition",
            name="competition_end",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="比赛结束时间"
            ),
        ),
        migrations.RunPython(forwards_fill_competition_times, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="competition",
            name="competition_start",
            field=models.DateTimeField(verbose_name="比赛开始时间"),
        ),
        migrations.AlterField(
            model_name="competition",
            name="competition_end",
            field=models.DateTimeField(verbose_name="比赛结束时间"),
        ),
        migrations.RemoveField(
            model_name="competition",
            name="submission_deadline",
        ),
    ]
