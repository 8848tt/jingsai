from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

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
    Team,
    TeamMembership,
    validate_team_size_for_competition,
)
from .services import student_approved_registration_competition_ids

UserModel = get_user_model()


# ── Team ──────────────────────────────────────────────────────────────

class TeamSerializer(serializers.ModelSerializer):
    leader_username = serializers.CharField(source="leader.username", read_only=True)
    approved_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Team
        fields = ("id", "name", "leader", "leader_username", "approved_count", "created_at", "updated_at")
        read_only_fields = ("leader", "leader_username", "approved_count", "created_at", "updated_at")

    def get_approved_count(self, obj):
        return obj.memberships.filter(status=TeamMembership.Status.APPROVED).count()

    def create(self, validated_data):
        request = self.context["request"]
        team = Team.objects.create(leader=request.user, **validated_data)
        TeamMembership.objects.create(team=team, student=request.user, status=TeamMembership.Status.APPROVED)
        return team


class TeamMembershipSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source="student.username", read_only=True)

    class Meta:
        model = TeamMembership
        fields = ("id", "team", "student", "student_username", "status", "joined_at")
        read_only_fields = ("student", "status", "joined_at")

    def create(self, validated_data):
        request = self.context["request"]
        team = validated_data["team"]
        if TeamMembership.objects.filter(team=team, student=request.user).exists():
            raise serializers.ValidationError({"detail": "您已在该队伍中有申请记录。"})
        validated_data["status"] = TeamMembership.Status.PENDING
        return super().create(validated_data)


class TeamMembershipApproveSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMembership
        fields = ("status",)


# ── Competition ───────────────────────────────────────────────────────

class CompetitionSerializer(serializers.ModelSerializer):
    expert_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=UserModel.objects.filter(role=User.Role.EXPERT),
        source="experts",
        required=False,
        write_only=True,
    )
    experts_read = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Competition
        fields = (
            "id",
            "title",
            "description",
            "registration_start",
            "registration_end",
            "competition_start",
            "competition_end",
            "status",
            "max_team_members",
            "reviews_per_submission",
            "created_by",
            "expert_ids",
            "experts_read",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def get_experts_read(self, obj):
        return [{"id": u.id, "username": u.username} for u in obj.experts.all()]

    def validate(self, attrs):
        start = attrs.get("competition_start")
        end = attrs.get("competition_end")
        if self.instance:
            if start is None:
                start = self.instance.competition_start
            if end is None:
                end = self.instance.competition_end
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"competition_end": "比赛结束时间须晚于比赛开始时间。"}
            )
        return attrs

    def validate_reviews_per_submission(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("至少为 1")
        if value is not None and value > 50:
            raise serializers.ValidationError("不能超过 50")
        return value

    def create(self, validated_data):
        from .reviewer_assignment import assign_reviewers_for_competition

        experts = validated_data.pop("experts", [])
        request = self.context["request"]
        comp = Competition.objects.create(created_by=request.user, **validated_data)
        if experts:
            comp.experts.set(experts)
        if comp.status == Competition.Status.REVIEWING:
            assign_reviewers_for_competition(comp)
        return comp

    def update(self, instance, validated_data):
        from .reviewer_assignment import assign_reviewers_for_competition

        old_status = instance.status
        experts = validated_data.pop("experts", None)
        instance = super().update(instance, validated_data)
        if experts is not None:
            instance.experts.set(experts)
        if instance.status == Competition.Status.REVIEWING and old_status != Competition.Status.REVIEWING:
            assign_reviewers_for_competition(instance)
        return instance


# ── Registration ──────────────────────────────────────────────────────

class RegistrationSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)

    class Meta:
        model = Registration
        fields = (
            "id",
            "team",
            "team_name",
            "competition",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "created_at", "updated_at")

    def validate(self, attrs):
        team = attrs.get("team") or getattr(self.instance, "team", None)
        comp = attrs.get("competition") or getattr(self.instance, "competition", None)
        if team and comp:
            validate_team_size_for_competition(team, comp)
        if comp is not None:
            if comp.status not in (
                Competition.Status.PUBLISHED,
                Competition.Status.REGISTERING,
            ):
                raise serializers.ValidationError("仅「报名中」或「进行中」状态的竞赛开放报名。")
            now = timezone.now()
            if not (comp.registration_start <= now <= comp.registration_end):
                raise serializers.ValidationError("当前不在报名时间内。")
        return attrs


class RegistrationAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ("status",)


# ── Submission ────────────────────────────────────────────────────────

class SubmissionAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionAttachment
        fields = ("id", "file", "original_name", "created_at")
        read_only_fields = fields


class SubmissionSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)
    attachments = SubmissionAttachmentSerializer(many=True, read_only=True)
    average_score = serializers.SerializerMethodField(read_only=True)
    review_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Submission
        fields = (
            "id",
            "competition",
            "team",
            "team_name",
            "description",
            "attachments",
            "average_score",
            "review_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "attachments",
            "average_score",
            "review_count",
            "created_at",
            "updated_at",
        )

    def _is_student(self):
        request = self.context.get("request")
        return request and getattr(request.user, "role", None) == "student"

    def get_average_score(self, obj):
        if self._is_student():
            return None
        return getattr(obj, "average_score", None)

    def get_review_count(self, obj):
        if self._is_student():
            return 0
        return getattr(obj, "review_count", 0) or 0


# ── Review ────────────────────────────────────────────────────────────

class ReviewSerializer(serializers.ModelSerializer):
    expert_username = serializers.CharField(source="expert.username", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "expert",
            "expert_username",
            "submission",
            "score",
            "comment",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("expert", "created_at", "updated_at")


# ── Announcement ──────────────────────────────────────────────────────


class AnnouncementAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementAttachment
        fields = ("id", "file", "original_name", "created_at")
        read_only_fields = fields


class AnnouncementSerializer(serializers.ModelSerializer):
    attachments = AnnouncementAttachmentSerializer(many=True, read_only=True)
    is_reminder_unread = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = (
            "id",
            "competition",
            "title",
            "body",
            "attachments",
            "is_published",
            "published_at",
            "remind_scope",
            "is_reminder_unread",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("published_at", "created_at", "updated_at", "attachments", "is_reminder_unread")
        extra_kwargs = {"competition": {"required": False, "allow_null": True}}

    def get_is_reminder_unread(self, obj):
        """学生端：本条是否属于「提醒范围内且尚未打开详情」。"""
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        if not user or not user.is_authenticated or getattr(user, "role", None) != UserModel.Role.STUDENT:
            return False
        if not obj.is_published or obj.remind_scope == Announcement.RemindScope.NONE:
            return False
        ctx = self.context
        key_read = "_announcement_read_ids_for_student"
        if key_read not in ctx:
            ctx[key_read] = set(
                AnnouncementRead.objects.filter(user=user).values_list("announcement_id", flat=True)
            )
        if obj.id in ctx[key_read]:
            return False
        if obj.remind_scope == Announcement.RemindScope.ALL_STUDENTS:
            return True
        if obj.remind_scope == Announcement.RemindScope.COMPETITION_REGISTRANTS:
            if obj.competition_id is None:
                return False
            key_reg = "_announcement_reg_comp_ids_for_student"
            if key_reg not in ctx:
                ctx[key_reg] = student_approved_registration_competition_ids(user)
            return obj.competition_id in ctx[key_reg]
        return False

    def validate(self, attrs):
        is_pub = attrs.get("is_published", getattr(self.instance, "is_published", False))
        if is_pub and not attrs.get("published_at") and not getattr(
            self.instance, "published_at", None
        ):
            attrs["published_at"] = timezone.now()

        inst = self.instance
        comp = attrs.get("competition", inst.competition if inst else None)
        scope = attrs.get(
            "remind_scope",
            inst.remind_scope if inst else Announcement.RemindScope.NONE,
        )
        if scope == Announcement.RemindScope.COMPETITION_REGISTRANTS and comp is None:
            raise serializers.ValidationError(
                {"remind_scope": "选择「本竞赛已报名用户」时必须指定关联竞赛。"}
            )
        return attrs

    def update(self, instance, validated_data):
        old_remind = instance.remind_scope
        instance = super().update(instance, validated_data)
        if old_remind != instance.remind_scope:
            AnnouncementRead.objects.filter(announcement=instance).delete()
        return instance


# ── Expert ────────────────────────────────────────────────────────────

class ExpertUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ("id", "username", "email")
        read_only_fields = fields
