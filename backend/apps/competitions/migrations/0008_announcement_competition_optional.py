from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("competitions", "0007_announcement_attachments"),
    ]

    operations = [
        migrations.AlterField(
            model_name="announcement",
            name="competition",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="announcements",
                to="competitions.competition",
                verbose_name="竞赛",
            ),
        ),
    ]
