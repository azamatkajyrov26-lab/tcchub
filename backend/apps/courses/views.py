from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.content.models import Activity, ActivityCompletion

from .models import Category, Course, Enrollment, Section
from .permissions import IsCourseCreatorOrReadOnly
from .serializers import (
    CategorySerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    EnrollmentSerializer,
    SectionSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(parent__isnull=True).prefetch_related("children")
    serializer_class = CategorySerializer
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["parent"]
    search_fields = ["name"]
    lookup_field = "slug"


class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCourseCreatorOrReadOnly]
    filterset_fields = ["category", "is_published", "enrollment_type", "format"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "title"]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Course.objects.select_related("category", "created_by")
        if self.request.user.is_authenticated and self.request.user.role in ("admin", "manager"):
            return qs
        return qs.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, slug=None):
        course = self.get_object()
        if course.enrollment_type == Course.EnrollmentType.CLOSED:
            return Response(
                {"detail": "Enrollment is closed."}, status=status.HTTP_403_FORBIDDEN
            )
        if course.enrollment_type == Course.EnrollmentType.KEY:
            key = request.data.get("enrollment_key", "")
            if key != course.enrollment_key:
                return Response(
                    {"detail": "Invalid enrollment key."}, status=status.HTTP_400_BAD_REQUEST
                )
        if course.max_students and course.enrollments.filter(is_active=True).count() >= course.max_students:
            return Response(
                {"detail": "Course is full."}, status=status.HTTP_400_BAD_REQUEST
            )
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user, course=course, defaults={"role": Enrollment.Role.STUDENT}
        )
        if not created:
            return Response({"detail": "Already enrolled."}, status=status.HTTP_400_BAD_REQUEST)

        # Send enrollment notification asynchronously
        from apps.notifications.tasks import send_course_enrolled_notification

        send_course_enrolled_notification.delay(request.user.id, course.id)

        return Response(EnrollmentSerializer(enrollment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def progress(self, request, slug=None):
        """Calculate course progress for the current user."""
        course = self.get_object()
        sections = course.sections.prefetch_related("activities").all()

        all_activity_ids = []
        section_breakdown = []

        for section in sections:
            activities = list(section.activities.values_list("id", flat=True))
            all_activity_ids.extend(activities)

            completed_ids = set(
                ActivityCompletion.objects.filter(
                    user=request.user,
                    activity_id__in=activities,
                    completed=True,
                ).values_list("activity_id", flat=True)
            )

            total = len(activities)
            completed = len(completed_ids)
            section_breakdown.append({
                "section_id": section.id,
                "section_title": section.title,
                "total_activities": total,
                "completed_activities": completed,
                "percentage": round((completed / total) * 100, 2) if total else 0,
            })

        total_activities = len(all_activity_ids)
        total_completed = ActivityCompletion.objects.filter(
            user=request.user,
            activity_id__in=all_activity_ids,
            completed=True,
        ).count()

        return Response({
            "course": course.slug,
            "total_activities": total_activities,
            "completed_activities": total_completed,
            "percentage": round((total_completed / total_activities) * 100, 2) if total_activities else 0,
            "sections": section_breakdown,
        })

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def search(self, request):
        """Search courses by title and description."""
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"detail": "Query parameter 'q' is required."}, status=status.HTTP_400_BAD_REQUEST)

        courses = Course.objects.filter(
            Q(title__icontains=q) | Q(description__icontains=q),
            is_published=True,
        ).select_related("category", "created_by")[:20]

        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def unenroll(self, request, slug=None):
        course = self.get_object()
        deleted, _ = Enrollment.objects.filter(user=request.user, course=course).delete()
        if not deleted:
            return Response({"detail": "Not enrolled."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Unenrolled."}, status=status.HTTP_200_OK)


class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer
    permission_classes = [IsCourseCreatorOrReadOnly]

    def get_queryset(self):
        return Section.objects.filter(course__slug=self.kwargs.get("course_slug"))

    def perform_create(self, serializer):
        course = Course.objects.get(slug=self.kwargs["course_slug"])
        serializer.save(course=course)


class EnrollmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["course", "role", "is_active"]

    def get_queryset(self):
        user = self.request.user
        if user.role in ("admin", "manager"):
            return Enrollment.objects.select_related("user", "course").all()
        return Enrollment.objects.select_related("user", "course").filter(user=user)
