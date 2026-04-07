from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsTeacherOrAbove

from .models import Grade, GradeCategory, GradeItem
from .serializers import GradeCategorySerializer, GradeItemSerializer, GradeSerializer


class GradeCategoryViewSet(viewsets.ModelViewSet):
    queryset = GradeCategory.objects.select_related("course", "parent").all()
    serializer_class = GradeCategorySerializer
    permission_classes = [IsTeacherOrAbove]
    filterset_fields = ["course", "parent"]


class GradeItemViewSet(viewsets.ModelViewSet):
    queryset = GradeItem.objects.select_related("course", "category", "activity").all()
    serializer_class = GradeItemSerializer
    permission_classes = [IsTeacherOrAbove]
    filterset_fields = ["course", "category"]


class GradeViewSet(viewsets.ModelViewSet):
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["grade_item", "user", "grade_item__course"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager", "teacher", "assistant"):
            return Grade.objects.select_related("grade_item", "user", "graded_by").all()
        return Grade.objects.select_related("grade_item", "graded_by").filter(user=user)

    def perform_create(self, serializer):
        serializer.save(graded_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(graded_by=self.request.user)
