from django.contrib import admin

from .models import (
    Announcement,
    AnnouncementAttachment,
    Competition,
    Registration,
    Review,
    Submission,
    SubmissionAttachment,
    Team,
    TeamMembership,
)


class SubmissionAttachmentInline(admin.TabularInline):
    model = SubmissionAttachment
    extra = 0
    readonly_fields = ("created_at",)


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "max_team_members",
        "reviews_per_submission",
        "registration_start",
        "competition_start",
        "competition_end",
    )
    list_filter = ("status",)
    autocomplete_fields = ("experts",)
    inlines = [RegistrationInline, SubmissionInline]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "leader", "created_at")
    list_filter = ("created_at",)


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "team", "student", "status", "joined_at")
    list_filter = ("status", "team")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("id", "team", "competition", "status")
    list_filter = ("status", "competition")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "competition", "team", "updated_at")
    list_filter = ("competition",)
    inlines = [SubmissionAttachmentInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "expert", "submission", "score")
    list_filter = ("submission__competition",)


class AnnouncementAttachmentInline(admin.TabularInline):
    model = AnnouncementAttachment
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "competition", "is_published", "published_at")
    list_filter = ("is_published", "competition")
    inlines = [AnnouncementAttachmentInline]
