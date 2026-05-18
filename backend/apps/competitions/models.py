from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=255, verbose_name="队伍名称")
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teams_led",
        verbose_name="队长",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "队伍"
        verbose_name_plural = "队伍"

    def __str__(self) -> str:
        return self.name


class TeamMembership(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已拒绝"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships", verbose_name="队伍")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
        verbose_name="学生",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="状态",
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "student"],
                name="uniq_membership_team_student",
            )
        ]
        verbose_name = "队伍成员"
        verbose_name_plural = "队伍成员"

    def __str__(self) -> str:
        return f"{self.student_id} in {self.team_id}"


def validate_team_size_for_competition(team, competition):
    max_limit = competition.max_team_members
    approved_count = team.memberships.filter(
        status=TeamMembership.Status.APPROVED
    ).count()
    if approved_count == 0:
        raise ValidationError("队伍至少需要有 1 名已通过成员。")
    if max_limit is not None and approved_count > max_limit:
        raise ValidationError(f"队伍人数 ({approved_count}) 超过竞赛限制 ({max_limit})。")


def validate_expert(user):
    from apps.accounts.models import User

    if user.role != User.Role.EXPERT:
        raise ValidationError("仅专家用户可担任评委。")


class Competition(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        REGISTERING = "registering", "报名中"
        PUBLISHED = "published", "进行中"
        REGISTRATION_CLOSED = "registration_closed", "报名已截止"
        REVIEWING = "reviewing", "评审中"
        FINISHED = "finished", "已结束"

    title = models.CharField(max_length=255, verbose_name="标题")
    description = models.TextField(blank=True, verbose_name="描述")
    registration_start = models.DateTimeField(verbose_name="报名开始时间")
    registration_end = models.DateTimeField(verbose_name="报名截止时间")
    competition_start = models.DateTimeField(verbose_name="比赛开始时间")
    competition_end = models.DateTimeField(verbose_name="比赛结束时间")
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name="状态",
    )
    max_team_members = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name="队伍人数上限",
    )
    reviews_per_submission = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="每位作品评审次数",
        help_text="进入「评审中」后，每份作品从已选专家中随机分配该数量的专家进行评审。",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="competitions_created",
        verbose_name="创建者",
    )
    experts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assigned_competitions",
        blank=True,
        limit_choices_to={"role": "expert"},
        verbose_name="评审专家",
        help_text="",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "竞赛"
        verbose_name_plural = "竞赛"

    def __str__(self) -> str:
        return self.title


class Registration(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待审核"
        APPROVED = "approved", "已通过"
        REJECTED = "rejected", "已拒绝"

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name="队伍",
    )
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name="竞赛",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="状态",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "competition"],
                name="uniq_registration_team_competition",
            )
        ]
        verbose_name = "报名"
        verbose_name_plural = "报名"

    def __str__(self) -> str:
        return f"{self.team_id} -> {self.competition_id}"


class Submission(models.Model):
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="竞赛",
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="队伍",
    )
    description = models.TextField(blank=True, verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["competition", "team"],
                name="uniq_submission_competition_team",
            )
        ]
        ordering = ["-updated_at"]
        verbose_name = "作品提交"
        verbose_name_plural = "作品提交"

    def __str__(self) -> str:
        return f"{self.competition_id} / {self.team_id}"


class SubmissionAttachment(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="作品",
    )
    file = models.FileField(upload_to="submissions/%Y/%m/", verbose_name="文件")
    original_name = models.CharField(max_length=255, blank=True, verbose_name="原始文件名")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    class Meta:
        ordering = ["id"]
        verbose_name = "作品附件"
        verbose_name_plural = "作品附件"

    def __str__(self) -> str:
        return f"{self.submission_id}: {self.original_name or self.file.name}"


class SubmissionReviewAssignment(models.Model):
    """某作品由哪位专家评审（随机分配，用于限制打分权限与列表可见范围）。"""

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="review_assignments",
        verbose_name="作品",
    )
    expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submission_review_assignments",
        limit_choices_to={"role": "expert"},
        verbose_name="评审专家",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="分配时间")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "expert"],
                name="uniq_review_assignment_submission_expert",
            )
        ]
        verbose_name = "作品评审分配"
        verbose_name_plural = "作品评审分配"

    def __str__(self) -> str:
        return f"{self.submission_id} -> {self.expert_id}"


class Review(models.Model):
    expert = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        limit_choices_to={"role": "expert"},
        verbose_name="专家",
    )
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="作品",
    )
    score = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="分数")
    comment = models.TextField(blank=True, verbose_name="评语")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["expert", "submission"],
                name="uniq_review_expert_submission",
            )
        ]
        ordering = ["-updated_at"]
        verbose_name = "评审"
        verbose_name_plural = "评审"

    def clean(self):
        super().clean()
        validate_expert(self.expert)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Announcement(models.Model):
    class RemindScope(models.TextChoices):
        NONE = "none", "不提醒"
        ALL_STUDENTS = "all_students", "提醒全体学生"
        COMPETITION_REGISTRANTS = "competition_registrants", "提醒本竞赛已报名学生"

    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name="announcements",
        verbose_name="竞赛",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255, verbose_name="标题")
    body = models.TextField(verbose_name="正文")
    is_published = models.BooleanField(default=False, verbose_name="是否发布")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="发布时间")
    remind_scope = models.CharField(
        max_length=40,
        choices=RemindScope.choices,
        default=RemindScope.NONE,
        verbose_name="红点提醒范围",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "公告"
        verbose_name_plural = "公告"

    def __str__(self) -> str:
        return self.title


class AnnouncementRead(models.Model):
    """学生打开公告详情后写入，用于未读红点统计。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="announcement_reads",
        verbose_name="用户",
    )
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="reads",
        verbose_name="公告",
    )
    read_at = models.DateTimeField(auto_now_add=True, verbose_name="已读时间")

    class Meta:
        verbose_name = "公告已读"
        verbose_name_plural = "公告已读"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "announcement"),
                name="uniq_announcementread_user_announcement",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.announcement_id}"


class AnnouncementAttachment(models.Model):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="公告",
    )
    file = models.FileField(upload_to="announcements/%Y/%m/", verbose_name="文件")
    original_name = models.CharField(max_length=255, blank=True, verbose_name="原始文件名")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    class Meta:
        ordering = ["id"]
        verbose_name = "公告附件"
        verbose_name_plural = "公告附件"

    def __str__(self) -> str:
        return f"{self.announcement_id}: {self.original_name or self.file.name}"
