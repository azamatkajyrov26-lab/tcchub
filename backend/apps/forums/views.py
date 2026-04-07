from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.courses.permissions import IsCourseCreatorOrReadOnly

from .models import Discussion, Forum, Post
from .serializers import (
    DiscussionDetailSerializer,
    DiscussionSerializer,
    ForumSerializer,
    PostSerializer,
)


class ForumViewSet(viewsets.ModelViewSet):
    queryset = Forum.objects.select_related("activity").all()
    serializer_class = ForumSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["activity", "forum_type"]


class DiscussionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filterset_fields = ["forum", "pinned", "locked"]
    search_fields = ["title"]

    def get_queryset(self):
        return Discussion.objects.select_related("user", "forum").all()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DiscussionDetailSerializer
        return DiscussionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PostSerializer
    filterset_fields = ["discussion", "user"]

    def get_queryset(self):
        return Post.objects.select_related("user", "discussion").filter(parent__isnull=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
