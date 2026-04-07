import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification(self, user_id, notification_type_code, title, message, link=None):
    """Create a Notification record and optionally send an email."""
    from apps.accounts.models import CustomUser
    from apps.notifications.models import Notification, NotificationPreference, NotificationType

    try:
        user = CustomUser.objects.get(pk=user_id)
        notification_type = NotificationType.objects.filter(code=notification_type_code).first()

        if not notification_type:
            notification_type, _ = NotificationType.objects.get_or_create(
                code=notification_type_code,
                defaults={"name": notification_type_code.replace("_", " ").title()},
            )

        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link or "",
        )

        # Check email preference
        pref = NotificationPreference.objects.filter(
            user=user, notification_type=notification_type
        ).first()

        email_enabled = pref.email_enabled if pref else True

        if email_enabled and user.email:
            try:
                send_mail(
                    subject=title,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.warning("Failed to send email to %s: %s", user.email, e)

        return notification.id

    except Exception as exc:
        logger.error("send_notification failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task
def send_course_enrolled_notification(user_id, course_id):
    """Notify a user that they have been enrolled in a course."""
    from apps.courses.models import Course

    try:
        course = Course.objects.get(pk=course_id)
        send_notification.delay(
            user_id=user_id,
            notification_type_code="course_enrolled",
            title=f"Вы записаны на курс: {course.title}",
            message=f"Вы успешно записались на курс «{course.title}». Удачи в обучении!",
            link=f"/courses/{course.slug}/",
        )
    except Course.DoesNotExist:
        logger.error("send_course_enrolled_notification: course %s not found", course_id)


@shared_task
def send_assignment_due_reminder(assignment_id):
    """Send a due-date reminder to all enrolled students."""
    from apps.assignments.models import Assignment
    from apps.courses.models import Enrollment

    try:
        assignment = Assignment.objects.select_related("activity__section__course").get(pk=assignment_id)
        course = assignment.activity.section.course
        due_date = assignment.activity.due_date

        enrollments = Enrollment.objects.filter(
            course=course, role=Enrollment.Role.STUDENT, is_active=True
        ).values_list("user_id", flat=True)

        due_str = due_date.strftime("%d.%m.%Y %H:%M") if due_date else "не указан"

        for uid in enrollments:
            send_notification.delay(
                user_id=uid,
                notification_type_code="assignment_due",
                title=f"Напоминание: {assignment.activity.title}",
                message=(
                    f"Срок сдачи задания «{assignment.activity.title}» "
                    f"по курсу «{course.title}» — {due_str}."
                ),
                link=f"/courses/{course.slug}/",
            )
    except Assignment.DoesNotExist:
        logger.error("send_assignment_due_reminder: assignment %s not found", assignment_id)


@shared_task
def send_quiz_graded_notification(attempt_id):
    """Notify a student that their quiz attempt has been graded."""
    from apps.quizzes.models import QuizAttempt

    try:
        attempt = QuizAttempt.objects.select_related(
            "quiz__activity__section__course", "user"
        ).get(pk=attempt_id)

        course = attempt.quiz.activity.section.course
        quiz_title = attempt.quiz.activity.title
        passing = attempt.score >= attempt.quiz.passing_grade if attempt.score is not None else False

        send_notification.delay(
            user_id=attempt.user_id,
            notification_type_code="quiz_graded",
            title=f"Тест оценён: {quiz_title}",
            message=(
                f"Ваш результат по тесту «{quiz_title}» — {attempt.score}%. "
                f"{'Тест пройден!' if passing else 'К сожалению, тест не пройден.'}"
            ),
            link=f"/courses/{course.slug}/",
        )
    except QuizAttempt.DoesNotExist:
        logger.error("send_quiz_graded_notification: attempt %s not found", attempt_id)


@shared_task
def send_certificate_issued_notification(certificate_id):
    """Notify a student that a certificate has been issued."""
    from apps.certificates.models import IssuedCertificate

    try:
        cert = IssuedCertificate.objects.select_related("user", "course").get(pk=certificate_id)

        send_notification.delay(
            user_id=cert.user_id,
            notification_type_code="certificate_issued",
            title=f"Сертификат выдан: {cert.course.title}",
            message=(
                f"Поздравляем! Вам выдан сертификат за курс «{cert.course.title}». "
                f"Номер сертификата: {cert.certificate_number}."
            ),
            link=f"/certificates/{cert.certificate_number}/",
        )
    except IssuedCertificate.DoesNotExist:
        logger.error("send_certificate_issued_notification: cert %s not found", certificate_id)
