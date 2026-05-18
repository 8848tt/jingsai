from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnnouncementViewSet,
    CompetitionViewSet,
    ExpertListViewSet,
    RegistrationViewSet,
    ReviewViewSet,
    SubmissionViewSet,
    TeamMembershipViewSet,
    TeamViewSet,
)

router = DefaultRouter()
router.register("competitions", CompetitionViewSet, basename="competition")
router.register("registrations", RegistrationViewSet, basename="registration")
router.register("submissions", SubmissionViewSet, basename="submission")
router.register("reviews", ReviewViewSet, basename="review")
router.register("announcements", AnnouncementViewSet, basename="announcement")
router.register("experts", ExpertListViewSet, basename="expert")
router.register("teams", TeamViewSet, basename="team")
router.register("memberships", TeamMembershipViewSet, basename="membership")

urlpatterns = [
    path("", include(router.urls)),
]
