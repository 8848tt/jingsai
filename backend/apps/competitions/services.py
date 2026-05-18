"""业务辅助函数，避免 apps 间循环引用。"""

from django.db.models import Exists, OuterRef, Q

from apps.accounts.models import User

from .models import Announcement, AnnouncementRead, Registration, Team, TeamMembership


def student_approved_registration_competition_ids(user):
    """学生所在队伍对哪些竞赛有已通过报名（竞赛 id 集合）。"""
    if not user.is_authenticated or getattr(user, "role", None) != User.Role.STUDENT:
        return frozenset()
    team_ids = (
        Team.objects.filter(
            Q(leader=user)
            | Q(memberships__student=user, memberships__status=TeamMembership.Status.APPROVED)
        )
        .distinct()
        .values_list("id", flat=True)
    )
    team_id_list = list(team_ids)
    if not team_id_list:
        return frozenset()
    return frozenset(
        Registration.objects.filter(
            team_id__in=team_id_list,
            status=Registration.Status.APPROVED,
        )
        .values_list("competition_id", flat=True)
        .distinct()
    )


def count_unread_announcement_for_student(user) -> int:
    """学生侧栏「公告」红点：已发布且开启提醒、且当前用户属目标受众、且未标记已读。"""
    if not user.is_authenticated or getattr(user, "role", None) != User.Role.STUDENT:
        return 0

    reg_competition_ids = student_approved_registration_competition_ids(user)

    scope_all = Q(remind_scope=Announcement.RemindScope.ALL_STUDENTS)
    scope_reg = Q(
        remind_scope=Announcement.RemindScope.COMPETITION_REGISTRANTS,
        competition_id__in=reg_competition_ids,
    )
    ann_qs = Announcement.objects.filter(is_published=True).filter(scope_all | scope_reg)
    read_sub = AnnouncementRead.objects.filter(announcement_id=OuterRef("pk"), user=user)
    return ann_qs.annotate(_read=Exists(read_sub)).filter(_read=False).count()
