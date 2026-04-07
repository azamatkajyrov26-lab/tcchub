from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.courses.permissions import IsCourseCreatorOrReadOnly

from .models import Assignment, Submission, SubmissionFile
from .serializers import AssignmentSerializer, SubmissionFileSerializer, SubmissionSerializer


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.select_related("activity").all()
    serializer_class = AssignmentSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["activity"]


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["assignment", "status"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager", "teacher", "assistant"):
            return Submission.objects.select_related("user", "graded_by").all()
        return Submission.objects.select_related("user", "graded_by").filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        submission = self.get_object()
        if submission.user != request.user:
            return Response({"detail": "Not your submission."}, status=status.HTTP_403_FORBIDDEN)
        submission.status = Submission.Status.SUBMITTED
        submission.save()
        return Response(SubmissionSerializer(submission).data)

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        if request.user.role not in ("admin", "manager", "teacher", "assistant"):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        submission = self.get_object()
        grade = request.data.get("grade")
        feedback = request.data.get("feedback", "")
        if grade is None:
            return Response({"detail": "Grade is required."}, status=status.HTTP_400_BAD_REQUEST)
        submission.grade = grade
        submission.feedback = feedback
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.status = Submission.Status.GRADED
        submission.save()
        return Response(SubmissionSerializer(submission).data)


class SubmissionFileViewSet(viewsets.ModelViewSet):
    queryset = SubmissionFile.objects.select_related("submission").all()
    serializer_class = SubmissionFileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["submission"]
