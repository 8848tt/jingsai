# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("competitions", "0003_competition_start_end_remove_submission_deadline"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="competition",
            name="reviews_per_submission",
            field=models.PositiveSmallIntegerField(
                default=1,
                help_text="进入「评审中」后，每份作品从已选专家中随机分配该数量的专家进行评审。",
                verbose_name="每位作品评审次数",
            ),
        ),
        migrations.CreateModel(
            name="SubmissionReviewAssignment",
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
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="分配时间"),
                ),
                (
                    "expert",
                    models.ForeignKey(
                        limit_choices_to={"role": "expert"},
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submission_review_assignments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="评审专家",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review_assignments",
                        to="competitions.submission",
                        verbose_name="作品",
                    ),
                ),
            ],
            options={
                "verbose_name": "作品评审分配",
                "verbose_name_plural": "作品评审分配",
            },
        ),
        migrations.AddConstraint(
            model_name="submissionreviewassignment",
            constraint=models.UniqueConstraint(
                fields=("submission", "expert"),
                name="uniq_review_assignment_submission_expert",
            ),
        ),
    ]
