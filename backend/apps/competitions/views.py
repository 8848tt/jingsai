from django.db import IntegrityError, models
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User

from .models import (
    Announcement,
    AnnouncementAttachment,
    AnnouncementRead,
    Competition,
    Registration,
    Review,
    Submission,
    SubmissionAttachment,
    SubmissionReviewAssignment,
    Team,
    TeamMembership,
)
from .permissions import IsAdminUser, IsExpertUser, IsStudentUser, IsTeamLeader, IsTeamMember, _is_admin, _is_expert, _is_student
from .serializers import (
    AnnouncementSerializer,
    CompetitionSerializer,
    ExpertUserSerializer,
    RegistrationAdminSerializer,
    RegistrationSerializer,
    ReviewSerializer,
    SubmissionSerializer,
    TeamMembershipApproveSerializer,
    TeamMembershipSerializer,
    TeamSerializer,
)


def _user_team_ids(user):
    """Return a queryset of Team ids where the user is leader or approved member."""
    return Team.objects.filter(
        Q(leader=user) | Q(memberships__student=user, memberships__status=TeamMembership.Status.APPROVED)
    ).values("id")


# ── Team ──────────────────────────────────────────────────────────────

class TeamViewSet(viewsets.ModelViewSet):
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsStudentUser()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsStudentUser(), IsTeamLeader()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Team.objects.prefetch_related("memberships").all()
        if _is_admin(user):
            return qs
        if _is_student(user) and self.request.query_params.get("all") == "1":
            return qs
        return qs.filter(
            Q(leader=user) | Q(memberships__student=user, memberships__status=TeamMembership.Status.APPROVED)
        ).distinct()


# ── TeamMembership ────────────────────────────────────────────────────

class TeamMembershipViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ("partial_update", "update"):
            return TeamMembershipApproveSerializer
        return TeamMembershipSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsStudentUser()]
        if self.action in ("partial_update", "update", "destroy"):
            return [IsAuthenticated(), IsStudentUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = TeamMembership.objects.select_related("team", "student").all()
        team_id = self.request.query_params.get("team")
        if team_id:
            qs = qs.filter(team_id=team_id)
        if _is_admin(user):
            return qs
        return qs.filter(Q(team__leader=user) | Q(student=user)).distinct()

    def perform_create(self, serializer):
        try:
            serializer.save(student=self.request.user)
        except IntegrityError as e:
            raise ValidationError({"detail": "您已在该队伍中有申请记录。"}) from e

    def perform_update(self, serializer):
        team = serializer.instance.team
        perm = IsTeamLeader()
        if not perm.has_object_permission(self.request, self, team):
            raise PermissionDenied("仅队长可审核成员。")
        serializer.save()

    def perform_destroy(self, instance):
        if _is_admin(self.request.user):
            return super().perform_destroy(instance)
        team = instance.team
        if team.leader_id != self.request.user.id:
            raise PermissionDenied("仅队长可移出队员。")
        if instance.student_id == team.leader_id:
            raise ValidationError({"detail": "不能移出队长；请使用「删除队伍」解散队伍。"})
        super().perform_destroy(instance)


# ── Competition ───────────────────────────────────────────────────────

class CompetitionViewSet(viewsets.ModelViewSet):
    serializer_class = CompetitionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = Competition.objects.all()
        if _is_admin(user):
            return qs
        if _is_expert(user):
            return qs.filter(experts=user).distinct()
        return qs.exclude(status=Competition.Status.DRAFT)


# ── Registration ──────────────────────────────────────────────────────

class RegistrationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Registration.objects.select_related("team", "competition").all()

    def get_serializer_class(self):
        if self.action in ("partial_update", "update") and _is_admin(self.request.user):
            return RegistrationAdminSerializer
        return RegistrationSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsStudentUser()]
        if self.action in ("partial_update", "update", "destroy"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        competition_id = self.request.query_params.get("competition")
        if competition_id:
            qs = qs.filter(competition_id=competition_id)
        if _is_admin(user):
            return qs
        if _is_student(user):
            return qs.filter(team_id__in=_user_team_ids(user))
        if _is_expert(user):
            return qs.filter(competition__experts=user)
        return qs.none()

    def perform_create(self, serializer):
        team = serializer.validated_data["team"]
        is_approved = team.memberships.filter(
            student=self.request.user, status=TeamMembership.Status.APPROVED
        ).exists()
        if not is_approved and team.leader_id != self.request.user.id:
            raise PermissionDenied("只有队伍的已通过成员可报名。")
        try:
            serializer.save()
        except IntegrityError as e:
            raise ValidationError({"detail": "该队伍已报名该竞赛。"}) from e


# ── Submission ────────────────────────────────────────────────────────

class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Submission.objects.select_related("competition", "team").prefetch_related("attachments")

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .annotate(
                average_score=Avg("reviews__score"),
                review_count=Count("reviews", distinct=True),
            )
        )
        user = self.request.user
        competition_id = self.request.query_params.get("competition")
        if competition_id:
            qs = qs.filter(competition_id=competition_id)
        if _is_admin(user):
            return qs
        if _is_student(user):
            return qs.filter(team_id__in=_user_team_ids(user))
        if _is_expert(user):
            qs = qs.filter(competition__status=Competition.Status.REVIEWING)
            comp_ids_with_assign = set(
                SubmissionReviewAssignment.objects.values_list(
                    "submission__competition_id", flat=True
                ).distinct()
            )
            assigned_q = Q(
                pk__in=SubmissionReviewAssignment.objects.filter(expert=user).values_list(
                    "submission_id", flat=True
                )
            )
            legacy_q = Q(competition__experts=user) & ~Q(competition_id__in=comp_ids_with_assign)
            return qs.filter(assigned_q | legacy_q).distinct()
        return qs.none()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [IsAuthenticated(), IsStudentUser()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def _assert_can_submit(self, team, competition):
        if competition.status not in (
            Competition.Status.PUBLISHED,
            Competition.Status.REGISTRATION_CLOSED,
        ):
            raise ValidationError("当前竞赛状态不允许提交作品。")
        if timezone.now() > competition.competition_end:
            raise ValidationError("已超过比赛结束时间，无法提交或修改作品。")
        ok = Registration.objects.filter(
            team=team,
            competition=competition,
            status=Registration.Status.APPROVED,
        ).exists()
        if not ok:
            raise ValidationError("队伍需已通过报名审核后方可提交。")

    def _check_team_member(self, team):
        if team.leader_id == self.request.user.id:
            return
        if not team.memberships.filter(
            student=self.request.user, status=TeamMembership.Status.APPROVED
        ).exists():
            raise PermissionDenied("只有队伍成员可提交作品。")

    def _sync_submission_attachments(self, submission):
        raw = self.request.POST.get("delete_attachment_ids") or self.request.data.get(
            "delete_attachment_ids"
        )
        if raw:
            for part in str(raw).split(","):
                part = part.strip()
                if part.isdigit():
                    SubmissionAttachment.objects.filter(
                        pk=int(part), submission=submission
                    ).delete()
        for f in self.request.FILES.getlist("attachments"):
            SubmissionAttachment.objects.create(
                submission=submission,
                file=f,
                original_name=(f.name or "")[:255],
            )

    def perform_create(self, serializer):
        team = serializer.validated_data["team"]
        self._check_team_member(team)
        competition = serializer.validated_data["competition"]
        self._assert_can_submit(team, competition)
        try:
            submission = serializer.save()
        except IntegrityError as e:
            raise ValidationError({"detail": "该队伍已提交过作品，请使用更新接口修改。"}) from e
        self._sync_submission_attachments(submission)
        if submission.competition.status == Competition.Status.REVIEWING:
            from .reviewer_assignment import assign_reviewers_for_submission

            assign_reviewers_for_submission(submission)

    def perform_update(self, serializer):
        team = serializer.instance.team
        self._check_team_member(team)
        competition = serializer.instance.competition
        self._assert_can_submit(team, competition)
        submission = serializer.save()
        self._sync_submission_attachments(submission)


# ── Review ────────────────────────────────────────────────────────────

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.select_related("expert", "submission", "submission__competition").all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [IsAuthenticated(), IsExpertUser()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        competition_id = self.request.query_params.get("competition")
        submission_id = self.request.query_params.get("submission")
        if competition_id:
            qs = qs.filter(submission__competition_id=competition_id)
        if submission_id:
            qs = qs.filter(submission_id=submission_id)
        if _is_admin(user):
            return qs
        if _is_expert(user):
            return qs.filter(expert=user)
        return qs.none()

    def perform_create(self, serializer):
        submission = serializer.validated_data["submission"]
        comp = submission.competition
        if SubmissionReviewAssignment.objects.filter(submission__competition=comp).exists():
            if not SubmissionReviewAssignment.objects.filter(
                submission=submission, expert=self.request.user
            ).exists():
                raise PermissionDenied("您未被分配为该作品的评审专家。")
        elif self.request.user not in comp.experts.all():
            raise PermissionDenied("您未被分配为该竞赛的评审专家。")
        if comp.status != Competition.Status.REVIEWING:
            raise ValidationError("仅在「评审中」阶段可进行打分。")
        try:
            serializer.save(expert=self.request.user)
        except IntegrityError as e:
            raise ValidationError(
                {"detail": "您已对该作品提交过评分，请使用更新接口修改。"}
            ) from e

    def perform_update(self, serializer):
        if serializer.instance.expert_id != self.request.user.id:
            raise PermissionDenied()
        comp = serializer.instance.submission.competition
        if comp.status != Competition.Status.REVIEWING:
            raise ValidationError("仅在「评审中」阶段可修改评分。")
        serializer.save()


# ── Announcement ──────────────────────────────────────────────────────

class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    queryset = Announcement.objects.select_related("competition").prefetch_related("attachments").all()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdminUser()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        competition_id = self.request.query_params.get("competition")
        if competition_id:
            try:
                cid = int(competition_id)
            except (TypeError, ValueError):
                cid = None
            if cid is not None:
                qs = qs.filter(competition_id=cid)
        if _is_admin(user):
            return qs
        # 学生端：同一竞赛的公告相邻，组内按发布时间从新到旧
        return qs.filter(is_published=True).order_by(
            models.F("competition_id").asc(nulls_last=True),
            "-published_at",
            "-created_at",
        )

    def _sync_announcement_attachments(self, announcement):
        raw = self.request.POST.get("delete_attachment_ids") or self.request.data.get(
            "delete_attachment_ids"
        )
        if raw:
            for part in str(raw).split(","):
                part = part.strip()
                if part.isdigit():
                    AnnouncementAttachment.objects.filter(
                        pk=int(part), announcement=announcement
                    ).delete()
        for f in self.request.FILES.getlist("attachments"):
            AnnouncementAttachment.objects.create(
                announcement=announcement,
                file=f,
                original_name=(f.name or "")[:255],
            )

    def perform_create(self, serializer):
        ann = serializer.save()
        self._sync_announcement_attachments(ann)

    def perform_update(self, serializer):
        ann = serializer.save()
        self._sync_announcement_attachments(ann)

    @action(detail=True, methods=["post"], url_path="mark_read")
    def mark_read(self, request, pk=None):
        if not _is_student(request.user):
            raise PermissionDenied("仅学生可标记已读。")
        announcement = self.get_object()
        AnnouncementRead.objects.get_or_create(user=request.user, announcement=announcement)
        return Response({"ok": True}, status=status.HTTP_200_OK)


class ExpertListViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExpertUserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = User.objects.filter(role=User.Role.EXPERT).order_by("id")
