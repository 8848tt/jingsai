"""随机将作品分配给竞赛专家中的若干位（每位作品评审次数）。"""

import random

from django.db import transaction

from .models import Competition, SubmissionReviewAssignment


def assign_reviewers_for_submission(submission):
    """为单份作品写入/刷新评审分配（竞赛须为「评审中」）。"""
    comp = submission.competition
    if comp.status != Competition.Status.REVIEWING:
        return
    experts = list(comp.experts.all())
    with transaction.atomic():
        SubmissionReviewAssignment.objects.filter(submission=submission).delete()
        if not experts:
            return
        n = min(max(comp.reviews_per_submission, 1), len(experts))
        chosen = random.sample(experts, n)
        SubmissionReviewAssignment.objects.bulk_create(
            [SubmissionReviewAssignment(submission=submission, expert=e) for e in chosen]
        )


def assign_reviewers_for_competition(competition):
    """为竞赛下所有作品批量分配评审（进入评审中时调用）。"""
    for sub in competition.submissions.all():
        assign_reviewers_for_submission(sub)
