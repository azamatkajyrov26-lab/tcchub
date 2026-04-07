from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.courses.permissions import IsCourseCreatorOrReadOnly

from .models import Activity, ActivityCompletion, Folder, FolderFile, Resource
from .serializers import (
    ActivityCompletionSerializer,
    ActivitySerializer,
    FolderFileSerializer,
    FolderSerializer,
    ResourceSerializer,
)


class ActivityViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitySerializer
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["section", "activity_type", "is_visible"]
    search_fields = ["title"]
    ordering_fields = ["order", "title"]

    def get_queryset(self):
        return Activity.objects.select_related("resource", "folder").all()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        activity = self.get_object()
        completion, created = ActivityCompletion.objects.get_or_create(
            user=request.user, activity=activity,
            defaults={"completed": True, "completed_at": timezone.now()},
        )
        if not created and not completion.completed:
            completion.completed = True
            completion.completed_at = timezone.now()
            completion.save()
        return Response(ActivityCompletionSerializer(completion).data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def my_completions(self, request):
        """Return all completions for the current user in a given course."""
        course_id = request.query_params.get("course_id")
        if not course_id:
            return Response(
                {"detail": "Query parameter 'course_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        completions = ActivityCompletion.objects.filter(
            user=request.user,
            activity__section__course_id=course_id,
        ).select_related("activity")

        serializer = ActivityCompletionSerializer(completions, many=True)
        return Response(serializer.data)


class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.select_related("activity").all()
    serializer_class = ResourceSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]


class FolderViewSet(viewsets.ModelViewSet):
    queryset = Folder.objects.prefetch_related("files").all()
    serializer_class = FolderSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]


class FolderFileViewSet(viewsets.ModelViewSet):
    queryset = FolderFile.objects.select_related("folder").all()
    serializer_class = FolderFileSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["folder"]


class ActivityCompletionViewSet(viewsets.ModelViewSet):
    serializer_class = ActivityCompletionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["activity", "completed"]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return ActivityCompletion.objects.filter(user=self.request.user)
