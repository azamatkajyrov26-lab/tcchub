import logging
from io import BytesIO

from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from weasyprint import HTML

logger = logging.getLogger(__name__)


def generate_certificate_pdf(issued_certificate):
    """
    Generate a PDF certificate from the HTML template and save it
    to the issued_certificate.pdf_file field.
    """
    student = issued_certificate.user
    course = issued_certificate.course

    context = {
        "student_name": student.get_full_name() or student.email,
        "course_name": course.title,
        "completion_date": issued_certificate.issued_at.strftime("%d.%m.%Y"),
        "certificate_number": str(issued_certificate.certificate_number),
    }

    html_string = render_to_string("certificates/certificate.html", context)

    pdf_buffer = BytesIO()
    HTML(string=html_string).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    filename = f"certificate_{issued_certificate.certificate_number}.pdf"
    issued_certificate.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)

    logger.info(
        "Certificate PDF generated for user=%s course=%s cert=%s",
        student.pk,
        course.pk,
        issued_certificate.certificate_number,
    )

    return issued_certificate
