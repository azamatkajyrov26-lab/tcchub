"""
Management command to seed the TCC Hub database with course data
parsed from the Moodle instance at tcchub.kz.

Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.courses.models import Category, Course, Section, Enrollment
from apps.content.models import Activity
from apps.quizzes.models import Quiz, Question, Answer
from apps.landing.models import (
    HeroSection,
    Metric,
    Partner,
    Testimonial,
    Advantage,
    ContactInfo,
)
from apps.notifications.models import NotificationType

User = get_user_model()


# ---------------------------------------------------------------------------
# Data constants
# ---------------------------------------------------------------------------

CATEGORIES = [
    {"name": "Логистика с нуля", "slug": "logistika-s-nulya", "order": 1},
    {
        "name": "Логистика с нуля. Навигация входа в профессию",
        "slug": "logistika-navigaciya",
        "order": 2,
    },
    {"name": "Логистика для продвинутых", "slug": "logistika-prodvinutyh", "order": 3},
    {"name": "Логистика с нуля (общая)", "slug": "logistika-obshchaya", "order": 4},
]

SECTIONS_BASIC = [
    ("Модуль 1: Введение в логистику", "Основные понятия, история и роль логистики в мировой экономике.", 2),
    ("Модуль 2: Море и глобальная логистика", "Морские перевозки, контейнерная логистика, основные порты.", 4),
    ("Модуль 3: Договорная база и международные правила перевозки", "INCOTERMS, договоры перевозки, CMR, коносаменты.", 4),
    ("Модуль 4: Сухопутная логистика: авто/ЖД", "Автомобильные и железнодорожные перевозки, маршрутизация.", 4),
    ("Модуль 5: Авиационная логистика", "Воздушные перевозки, грузовые авиакомпании, IATA.", 4),
    ("Модуль 6: Склады: управление запасами", "Складская логистика, WMS-системы, управление запасами.", 4),
    ("Модуль 7: Карьерный успех в логистике", "Построение карьеры, навыки, сертификации в логистике.", 2),
]

SECTIONS_NAV = [
    ("Модуль 1: Введение в логистику", "Основные понятия и роль логистики."),
    ("Модуль 2: Сухопутная логистика", "Автомобильные и железнодорожные перевозки."),
    ("Модуль 3: Авиационная логистика", "Воздушные грузоперевозки и регулирование."),
    ("Модуль 4: Морская логистика", "Морские перевозки и контейнерная логистика."),
    ("Модуль 5: Договоры и INCOTERMS", "Международные правила и договорная база."),
    ("Модуль 6: Склады и запасы", "Складская логистика и управление запасами."),
    ("Модуль 7: Карьера в логистике", "Построение карьеры в сфере логистики."),
]

SECTIONS_ADV_1 = [
    ("Модуль 1: Эффективное управление цепями поставок (SCM)", "Supply chain management, стратегическое планирование."),
    ("Модуль 2: Перевозка опасных грузов", "ADR, IMDG, классификация опасных грузов."),
    ("Модуль 3: Бизнес-законодательство в логистике", "Правовое регулирование логистической деятельности."),
    ("Модуль 4: Финансовый менеджмент в логистике", "Бюджетирование, ценообразование, финансовый анализ."),
    ("Модуль 5: Управление запасами и складская логистика", "Продвинутые методы управления запасами."),
    ("Модуль 6: Управление проектами в логистике (PMI)", "Методологии PMI, Agile в логистических проектах."),
    ("Модуль 7: Таможенное регулирование и международная торговля", "Таможенные процедуры, ВЭД, ТН ВЭД."),
    ("Модуль 8: Логистика в условиях санкций и геополитики", "Адаптация логистических цепочек к санкционным режимам."),
]

SECTIONS_ADV_3 = [
    ("Модуль 1: Геополитика и BRI", "Belt and Road Initiative, геополитические аспекты логистики."),
    ("Модуль 2: Эффективное управление цепями поставок (SCM)", "Supply chain management, стратегическое планирование."),
    ("Модуль 3: Перевозка опасных грузов", "ADR, IMDG, классификация опасных грузов."),
    ("Модуль 4: Управление проектами в логистике (PMI)", "Методологии PMI, Agile в логистических проектах."),
    ("Модуль 5: Бизнес-законодательство в логистике", "Правовое регулирование логистической деятельности."),
    ("Модуль 6: Логистика в условиях санкций и геополитики", "Адаптация логистических цепочек к санкционным режимам."),
    ("Модуль 7: Финансовый менеджмент в логистике", "Бюджетирование, ценообразование, финансовый анализ."),
    ("Модуль 8: Управление запасами и складская логистика", "Продвинутые методы управления запасами."),
    ("Модуль 9: Таможенное регулирование и международная торговля", "Таможенные процедуры, ВЭД, ТН ВЭД."),
]

# Activities per module topic keyword -> list of (title, type)
ACTIVITIES_MAP = {
    "Введение в логистику": [
        ("Видеолекция: Что такое логистика?", "folder"),
        ("Презентация: История логистики", "resource"),
        ("Тест: Основы логистики", "quiz"),
    ],
    "Море и глобальная логистика": [
        ("Видеолекция: Морские перевозки", "folder"),
        ("Презентация: Контейнерная логистика", "resource"),
        ("Задание: Анализ морского маршрута", "assignment"),
        ("Тест: Морская логистика", "quiz"),
    ],
    "Договорная база": [
        ("Видеолекция: INCOTERMS 2020", "folder"),
        ("Документ: Шаблоны договоров", "resource"),
        ("Задание: Составление договора перевозки", "assignment"),
        ("Тест: Договоры и INCOTERMS", "quiz"),
    ],
    "Договоры и INCOTERMS": [
        ("Видеолекция: INCOTERMS 2020", "folder"),
        ("Документ: Шаблоны договоров", "resource"),
        ("Задание: Составление договора перевозки", "assignment"),
        ("Тест: Договоры и INCOTERMS", "quiz"),
    ],
    "Сухопутная логистика": [
        ("Видеолекция: Авто и ЖД перевозки", "folder"),
        ("Презентация: Маршрутизация грузов", "resource"),
        ("Задание: Расчёт стоимости перевозки", "assignment"),
        ("Тест: Сухопутные перевозки", "quiz"),
    ],
    "Авиационная логистика": [
        ("Видеолекция: Воздушные перевозки", "folder"),
        ("Презентация: IATA и авиаперевозки", "resource"),
        ("Тест: Авиалогистика", "quiz"),
    ],
    "Морская логистика": [
        ("Видеолекция: Морские перевозки", "folder"),
        ("Презентация: Контейнерная логистика", "resource"),
        ("Задание: Анализ морского маршрута", "assignment"),
        ("Тест: Морская логистика", "quiz"),
    ],
    "Склады": [
        ("Видеолекция: Управление складом", "folder"),
        ("Презентация: WMS-системы", "resource"),
        ("Задание: Оптимизация складских процессов", "assignment"),
        ("Тест: Складская логистика", "quiz"),
    ],
    "Склады и запасы": [
        ("Видеолекция: Управление складом", "folder"),
        ("Презентация: WMS-системы", "resource"),
        ("Задание: Оптимизация складских процессов", "assignment"),
        ("Тест: Складская логистика", "quiz"),
    ],
    "Карьер": [
        ("Видеолекция: Построение карьеры", "folder"),
        ("Презентация: Навыки логиста", "resource"),
        ("Задание: Составление резюме логиста", "assignment"),
    ],
    "SCM": [
        ("Видеолекция: Supply Chain Management", "folder"),
        ("Презентация: Стратегии SCM", "resource"),
        ("Задание: Анализ цепи поставок", "assignment"),
        ("Тест: Управление цепями поставок", "quiz"),
    ],
    "опасных грузов": [
        ("Видеолекция: Классификация опасных грузов", "folder"),
        ("Документ: ADR/IMDG регламенты", "resource"),
        ("Задание: Маркировка опасного груза", "assignment"),
        ("Тест: Перевозка опасных грузов", "quiz"),
    ],
    "Бизнес-законодательство": [
        ("Видеолекция: Правовые основы логистики", "folder"),
        ("Документ: Нормативные акты", "resource"),
        ("Задание: Правовой анализ кейса", "assignment"),
        ("Тест: Бизнес-законодательство", "quiz"),
    ],
    "Финансовый менеджмент": [
        ("Видеолекция: Финансы в логистике", "folder"),
        ("Презентация: Бюджетирование", "resource"),
        ("Задание: Финансовый план проекта", "assignment"),
        ("Тест: Финансовый менеджмент", "quiz"),
    ],
    "Управление запасами": [
        ("Видеолекция: Методы управления запасами", "folder"),
        ("Презентация: ABC/XYZ анализ", "resource"),
        ("Задание: Расчёт оптимального запаса", "assignment"),
        ("Тест: Управление запасами", "quiz"),
    ],
    "PMI": [
        ("Видеолекция: Управление проектами", "folder"),
        ("Презентация: Agile и Waterfall", "resource"),
        ("Задание: Разработка плана проекта", "assignment"),
        ("Тест: Управление проектами", "quiz"),
    ],
    "Таможенное регулирование": [
        ("Видеолекция: Таможенные процедуры", "folder"),
        ("Документ: ТН ВЭД коды", "resource"),
        ("Задание: Оформление таможенной декларации", "assignment"),
        ("Тест: Таможенное регулирование", "quiz"),
    ],
    "санкций и геополитики": [
        ("Видеолекция: Логистика и санкции", "folder"),
        ("Презентация: Альтернативные маршруты", "resource"),
        ("Задание: Анализ санкционных рисков", "assignment"),
        ("Тест: Геополитические риски", "quiz"),
    ],
    "Геополитика и BRI": [
        ("Видеолекция: Belt and Road Initiative", "folder"),
        ("Презентация: Транскаспийский коридор", "resource"),
        ("Задание: Анализ маршрутов BRI", "assignment"),
        ("Тест: Геополитика и BRI", "quiz"),
    ],
}

FINAL_TEST_QUESTIONS = [
    {
        "text": "Что означает термин INCOTERMS?",
        "type": "multiple_choice",
        "answers": [
            ("Международные правила толкования торговых терминов", True),
            ("Международная конвенция о таможенных процедурах", False),
            ("Стандарты качества транспортных услуг", False),
            ("Кодекс международных перевозчиков", False),
        ],
    },
    {
        "text": "Какой вид транспорта обеспечивает наибольший объём мировой торговли?",
        "type": "multiple_choice",
        "answers": [
            ("Автомобильный", False),
            ("Железнодорожный", False),
            ("Морской", True),
            ("Авиационный", False),
        ],
    },
    {
        "text": "TEU — это стандартная единица измерения в контейнерных перевозках.",
        "type": "true_false",
        "answers": [
            ("Верно", True),
            ("Неверно", False),
        ],
    },
    {
        "text": "Что такое SCM?",
        "type": "multiple_choice",
        "answers": [
            ("Supply Chain Management — управление цепями поставок", True),
            ("Standard Container Measurement — стандартное измерение контейнеров", False),
            ("Shipping Customs Module — модуль таможенной отправки", False),
            ("Security Compliance Manual — руководство по безопасности", False),
        ],
    },
    {
        "text": "WMS — это система управления складом.",
        "type": "true_false",
        "answers": [
            ("Верно", True),
            ("Неверно", False),
        ],
    },
    {
        "text": "Какой документ сопровождает груз при международных автоперевозках?",
        "type": "multiple_choice",
        "answers": [
            ("CMR-накладная", True),
            ("Коносамент", False),
            ("Авианакладная AWB", False),
            ("Инвойс", False),
        ],
    },
    {
        "text": "IATA — это международная ассоциация воздушного транспорта.",
        "type": "true_false",
        "answers": [
            ("Верно", True),
            ("Неверно", False),
        ],
    },
    {
        "text": "Какой INCOTERMS термин означает, что продавец несёт все расходы до порта назначения?",
        "type": "multiple_choice",
        "answers": [
            ("EXW", False),
            ("CIF", True),
            ("FCA", False),
            ("FOB", False),
        ],
    },
    {
        "text": "Опасные грузы классифицируются по системе ADR только для автомобильных перевозок.",
        "type": "true_false",
        "answers": [
            ("Верно", True),
            ("Неверно", False),
        ],
    },
    {
        "text": "Какой метод анализа запасов делит товары на категории A, B, C?",
        "type": "multiple_choice",
        "answers": [
            ("FIFO-анализ", False),
            ("ABC-анализ", True),
            ("XYZ-анализ", False),
            ("Парето-анализ", False),
        ],
    },
]

NOTIFICATION_TYPES = [
    ("course_enrolled", "Зачисление на курс", "Уведомление о зачислении на курс", "course"),
    ("course_completed", "Завершение курса", "Уведомление о завершении курса", "course"),
    ("assignment_due", "Срок задания", "Напоминание о приближающемся сроке задания", "assignment"),
    ("assignment_graded", "Оценка задания", "Уведомление об оценке задания", "assignment"),
    ("quiz_available", "Доступен тест", "Уведомление о доступном тесте", "quiz"),
    ("quiz_graded", "Оценка теста", "Уведомление об оценке теста", "quiz"),
    ("forum_reply", "Ответ на форуме", "Уведомление об ответе на форуме", "forum"),
    ("message_received", "Новое сообщение", "Уведомление о новом сообщении", "message"),
    ("certificate_issued", "Выдан сертификат", "Уведомление о выдаче сертификата", "certificate"),
    ("badge_earned", "Получен бейдж", "Уведомление о получении бейджа", "badge"),
]

METRICS = [
    ("Лидеры к 2028", "5000+", "Подготовка 5000+ лидеров отрасли к 2028 году"),
    ("Специалисты к 2027", "2000+", "Обучение 2000+ специалистов к 2027 году"),
    ("Партнёры B2B/B2G", "15+", "Более 15 партнёров в сегментах B2B и B2G"),
    ("Аналитические проекты", "10-15", "Реализация 10-15 аналитических проектов"),
    ("Цифровые решения", "3-5", "Разработка 3-5 цифровых решений"),
    ("Международные форумы", "8+", "Участие в 8+ международных форумах"),
]

PARTNERS = [
    "NSRN",
    "PetroCouncil",
    "EUCA Alliance",
    "АУНГ",
    "DKU",
    "Ясави",
    "APEC Petrotechnic",
    "Satbayev University",
]

TESTIMONIALS = [
    {
        "author_name": "Марат Кенжебаев",
        "author_role": "Логист, ТОО «КазТрансОйл»",
        "content": (
            "Курс «Логистика с нуля» дал мне прочную базу для старта карьеры. "
            "Особенно полезными были модули по INCOTERMS и морской логистике. "
            "Преподаватели — практики с реальным опытом, что делает обучение "
            "максимально приближенным к реальным задачам."
        ),
    },
    {
        "author_name": "Алия Нурланова",
        "author_role": "Менеджер ВЭД, TransCaspian Cargo",
        "content": (
            "Продвинутый курс помог мне систематизировать знания по таможенному "
            "регулированию и управлению цепями поставок. После обучения я получила "
            "повышение и теперь руковожу отделом ВЭД. Рекомендую всем, кто хочет "
            "расти в профессии!"
        ),
    },
    {
        "author_name": "Тимур Ахметжанов",
        "author_role": "Экспедитор, Maersk Kazakhstan",
        "content": (
            "Отличная программа! Модуль по перевозке опасных грузов и санкционной "
            "логистике оказался невероятно актуальным. Нетворкинг с другими "
            "студентами помог мне найти новых партнёров для бизнеса."
        ),
    },
]

ADVANTAGES = [
    {
        "title": "Авторская методология TCC Hub",
        "description": "Уникальная программа обучения, разработанная экспертами TransCaspian Cargo на основе 20+ лет опыта в международной логистике.",
        "icon": "methodology",
    },
    {
        "title": "Чат-поддержка кураторов",
        "description": "Персональный куратор на связи 24/7 — ответы на вопросы, помощь с заданиями и мотивация на протяжении всего курса.",
        "icon": "support",
    },
    {
        "title": "Нетворкинг в профессиональном сообществе",
        "description": "Доступ к закрытому сообществу логистов, регулярные встречи и обмен опытом с ведущими специалистами отрасли.",
        "icon": "networking",
    },
    {
        "title": "20+ экспертов с опытом 20+ лет",
        "description": "Курсы ведут действующие руководители логистических компаний, таможенные брокеры и международные эксперты.",
        "icon": "experts",
    },
]


class Command(BaseCommand):
    help = "Seed the database with course data from Moodle (tcchub.kz)"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _ok(self, msg):
        self.stdout.write(self.style.SUCCESS(f"  ✓ {msg}"))

    def _info(self, msg):
        self.stdout.write(self.style.NOTICE(f"  → {msg}"))

    def _header(self, msg):
        self.stdout.write(self.style.MIGRATE_HEADING(f"\n{'='*60}\n{msg}\n{'='*60}"))

    # ------------------------------------------------------------------
    # activities helpers
    # ------------------------------------------------------------------

    def _get_activities_for_section(self, section_title):
        """Return a list of (title, activity_type) for a section title."""
        for keyword, activities in ACTIVITIES_MAP.items():
            if keyword in section_title:
                return activities
        # fallback
        return [
            ("Видеолекция", "folder"),
            ("Материалы модуля", "resource"),
        ]

    def _create_activities(self, section):
        activities = self._get_activities_for_section(section.title)
        for order, (title, atype) in enumerate(activities, 1):
            Activity.objects.get_or_create(
                section=section,
                title=title,
                defaults={
                    "activity_type": atype,
                    "order": order,
                    "completion_type": "automatic" if atype == "quiz" else "manual",
                },
            )

    def _create_final_test(self, section, quiz_title="Итоговый тест"):
        """Create a quiz activity with sample questions for a final test section."""
        activity, _ = Activity.objects.get_or_create(
            section=section,
            title=quiz_title,
            defaults={
                "activity_type": "quiz",
                "order": 1,
                "completion_type": "automatic",
            },
        )
        quiz, created = Quiz.objects.get_or_create(
            activity=activity,
            defaults={
                "time_limit": 60,
                "max_attempts": 2,
                "passing_grade": 70,
                "shuffle_questions": True,
                "show_results": True,
            },
        )
        if created:
            for q_order, q_data in enumerate(FINAL_TEST_QUESTIONS, 1):
                question, _ = Question.objects.get_or_create(
                    quiz=quiz,
                    order=q_order,
                    defaults={
                        "text": q_data["text"],
                        "question_type": q_data["type"],
                        "points": 1,
                    },
                )
                for a_order, (a_text, a_correct) in enumerate(q_data["answers"], 1):
                    Answer.objects.get_or_create(
                        question=question,
                        order=a_order,
                        defaults={
                            "text": a_text,
                            "is_correct": a_correct,
                        },
                    )
        return quiz

    # ------------------------------------------------------------------
    # section builders
    # ------------------------------------------------------------------

    def _create_sections_basic(self, course, with_final_test=True):
        for order, (title, desc, _hours) in enumerate(SECTIONS_BASIC, 1):
            section, _ = Section.objects.get_or_create(
                course=course,
                title=title,
                defaults={"description": desc, "order": order},
            )
            self._create_activities(section)

        if with_final_test:
            section, _ = Section.objects.get_or_create(
                course=course,
                title="Итоговый тест",
                defaults={"description": "Итоговое тестирование по курсу.", "order": len(SECTIONS_BASIC) + 1},
            )
            self._create_final_test(section)

    def _create_sections_nav(self, course):
        for order, (title, desc) in enumerate(SECTIONS_NAV, 1):
            section, _ = Section.objects.get_or_create(
                course=course,
                title=title,
                defaults={"description": desc, "order": order},
            )
            self._create_activities(section)

    def _create_sections_adv(self, course, sections_list, with_final_test_title=None):
        for order, (title, desc) in enumerate(sections_list, 1):
            section, _ = Section.objects.get_or_create(
                course=course,
                title=title,
                defaults={"description": desc, "order": order},
            )
            self._create_activities(section)

        if with_final_test_title:
            section, _ = Section.objects.get_or_create(
                course=course,
                title=with_final_test_title,
                defaults={
                    "description": "Итоговое тестирование по курсу.",
                    "order": len(sections_list) + 1,
                },
            )
            self._create_final_test(section, quiz_title=with_final_test_title)

    # ------------------------------------------------------------------
    # main
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        self._header("1. Creating categories")
        cats = {}
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={"name": cat_data["name"], "order": cat_data["order"]},
            )
            cats[cat_data["slug"]] = cat
            self._ok(f"{'Created' if created else 'Exists'}: {cat.name}")

        # ------------------------------------------------------------------
        self._header("2. Creating users")
        admin_user = User.objects.filter(role="admin").first()
        if not admin_user:
            admin_user = User.objects.first()
        if not admin_user:
            admin_user, _ = User.objects.get_or_create(
                email="admin@tcchub.kz",
                defaults={
                    "username": "admin",
                    "first_name": "Админ",
                    "last_name": "Системы",
                    "role": "admin",
                    "is_staff": True,
                    "is_superuser": True,
                },
            )
            admin_user.set_password("Admin123!")
            admin_user.save()

        teacher, created = User.objects.get_or_create(
            email="teacher@tcchub.kz",
            defaults={
                "username": "teacher",
                "first_name": "Рустем",
                "last_name": "Бисалиев",
                "role": "teacher",
            },
        )
        if created:
            teacher.set_password("Teacher123!")
            teacher.save()
        self._ok(f"{'Created' if created else 'Exists'}: {teacher.get_full_name()} (teacher)")

        student1, created = User.objects.get_or_create(
            email="student1@tcchub.kz",
            defaults={
                "username": "student1",
                "first_name": "Айдана",
                "last_name": "Сериккызы",
                "role": "student",
            },
        )
        if created:
            student1.set_password("Student123!")
            student1.save()
        self._ok(f"{'Created' if created else 'Exists'}: {student1.get_full_name()} (student)")

        student2, created = User.objects.get_or_create(
            email="student2@tcchub.kz",
            defaults={
                "username": "student2",
                "first_name": "Данияр",
                "last_name": "Ахметов",
                "role": "student",
            },
        )
        if created:
            student2.set_password("Student123!")
            student2.save()
        self._ok(f"{'Created' if created else 'Exists'}: {student2.get_full_name()} (student)")

        # ------------------------------------------------------------------
        self._header("3. Creating courses and sections")

        courses = []

        # Course 1-4: Логистика с нуля, потоки 1-4
        for potok in range(1, 5):
            slug = f"logistika-s-nulya-potok-{potok}"
            course, created = Course.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": f"Логистика с нуля — {potok} поток",
                    "description": f"Базовый курс по логистике, {potok}-й поток. 24 часа обучения.",
                    "short_description": "Базовый курс по международной логистике для начинающих.",
                    "category": cats["logistika-s-nulya"],
                    "duration_hours": 24,
                    "is_published": True,
                    "created_by": teacher,
                    "format": "topics",
                },
            )
            courses.append(course)
            self._ok(f"{'Created' if created else 'Exists'}: {course.title}")
            self._create_sections_basic(course, with_final_test=(potok <= 2))

        # Course 5: Навигация, 5 поток
        course5, created = Course.objects.get_or_create(
            slug="logistika-navigaciya-potok-5",
            defaults={
                "title": "Логистика с нуля. Навигация входа в профессию — 5 поток",
                "description": "Навигационный курс для входа в профессию логиста, 5-й поток.",
                "short_description": "Навигация входа в профессию логиста.",
                "category": cats["logistika-navigaciya"],
                "duration_hours": 24,
                "is_published": True,
                "created_by": teacher,
                "format": "topics",
            },
        )
        courses.append(course5)
        self._ok(f"{'Created' if created else 'Exists'}: {course5.title}")
        self._create_sections_nav(course5)

        # Course 6-7: Логистика для продвинутых, потоки 1-2
        for potok in range(1, 3):
            slug = f"logistika-prodvinutyh-potok-{potok}"
            course, created = Course.objects.get_or_create(
                slug=slug,
                defaults={
                    "title": f"Логистика для продвинутых — {potok} поток",
                    "description": f"Продвинутый курс по логистике, {potok}-й поток. 120 часов обучения.",
                    "short_description": "Продвинутый курс для опытных специалистов логистики.",
                    "category": cats["logistika-prodvinutyh"],
                    "duration_hours": 120,
                    "is_published": True,
                    "created_by": teacher,
                    "format": "topics",
                },
            )
            courses.append(course)
            self._ok(f"{'Created' if created else 'Exists'}: {course.title}")
            self._create_sections_adv(course, SECTIONS_ADV_1, with_final_test_title="Итоговый тест")

        # Course 8: Логистика для продвинутых, 3 поток (different structure)
        course8, created = Course.objects.get_or_create(
            slug="logistika-prodvinutyh-potok-3",
            defaults={
                "title": "Логистика для продвинутых — 3 поток",
                "description": "Продвинутый курс по логистике, 3-й поток. 120 часов обучения.",
                "short_description": "Продвинутый курс для опытных специалистов логистики.",
                "category": cats["logistika-prodvinutyh"],
                "duration_hours": 120,
                "is_published": True,
                "created_by": teacher,
                "format": "topics",
            },
        )
        courses.append(course8)
        self._ok(f"{'Created' if created else 'Exists'}: {course8.title}")
        self._create_sections_adv(course8, SECTIONS_ADV_3, with_final_test_title="Итоговое тестирование")

        # ------------------------------------------------------------------
        self._header("4. Enrolling users")

        # Teacher enrolled in all courses
        for course in courses:
            _, created = Enrollment.objects.get_or_create(
                user=teacher,
                course=course,
                defaults={"role": "teacher"},
            )
            if created:
                self._ok(f"Teacher enrolled in: {course.title}")

        # Students in first 2 courses
        for student in [student1, student2]:
            for course in courses[:2]:
                _, created = Enrollment.objects.get_or_create(
                    user=student,
                    course=course,
                    defaults={"role": "student"},
                )
                if created:
                    self._ok(f"{student.get_full_name()} enrolled in: {course.title}")

        # ------------------------------------------------------------------
        self._header("5. Creating notification types")

        for code, name, description, category in NOTIFICATION_TYPES:
            _, created = NotificationType.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": description,
                    "category": category,
                },
            )
            self._ok(f"{'Created' if created else 'Exists'}: {name}")

        # ------------------------------------------------------------------
        self._header("6. Creating landing page data")

        # Hero section
        _, created = HeroSection.objects.get_or_create(
            title="Развивайте карьеру в логистике",
            defaults={
                "subtitle": (
                    "Корпоративная LMS для профессионального роста. "
                    "Курсы по международной логистике, таможенному делу "
                    "и управлению цепочками поставок."
                ),
                "cta_text": "Начать обучение",
                "is_active": True,
            },
        )
        self._ok(f"{'Created' if created else 'Exists'}: HeroSection")

        # Metrics
        for order, (label, value, description) in enumerate(METRICS, 1):
            _, created = Metric.objects.get_or_create(
                label=label,
                defaults={"value": value, "description": description, "order": order},
            )
            self._ok(f"{'Created' if created else 'Exists'}: Metric — {label}")

        # Partners (logo field is required but we use a placeholder path)
        for order, name in enumerate(PARTNERS, 1):
            _, created = Partner.objects.get_or_create(
                name=name,
                defaults={"order": order, "logo": f"landing/partners/{name.lower().replace(' ', '_')}.png"},
            )
            self._ok(f"{'Created' if created else 'Exists'}: Partner — {name}")

        # Testimonials
        for order, t_data in enumerate(TESTIMONIALS, 1):
            _, created = Testimonial.objects.get_or_create(
                author_name=t_data["author_name"],
                defaults={
                    "author_role": t_data["author_role"],
                    "content": t_data["content"],
                    "order": order,
                },
            )
            self._ok(f"{'Created' if created else 'Exists'}: Testimonial — {t_data['author_name']}")

        # Advantages
        for order, adv in enumerate(ADVANTAGES, 1):
            _, created = Advantage.objects.get_or_create(
                title=adv["title"],
                defaults={
                    "description": adv["description"],
                    "icon": adv["icon"],
                    "order": order,
                },
            )
            self._ok(f"{'Created' if created else 'Exists'}: Advantage — {adv['title']}")

        # Contact info
        _, created = ContactInfo.objects.get_or_create(
            email="info@tc-cargo.kz",
            defaults={
                "address": "Атырау, пр. Студенческий 52",
                "phone": "+7 (771) 054-48-98",
                "whatsapp": "+77710544898",
                "linkedin": "https://linkedin.com/company/transcaspian-cargo",
                "instagram": "https://instagram.com/tc_cargo",
            },
        )
        self._ok(f"{'Created' if created else 'Exists'}: ContactInfo")

        # ------------------------------------------------------------------
        self._header("Done!")
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeded: {Category.objects.count()} categories, "
                f"{Course.objects.count()} courses, "
                f"{Section.objects.count()} sections, "
                f"{Activity.objects.count()} activities, "
                f"{Quiz.objects.count()} quizzes, "
                f"{Question.objects.count()} questions, "
                f"{User.objects.count()} users, "
                f"{Enrollment.objects.count()} enrollments"
            )
        )
