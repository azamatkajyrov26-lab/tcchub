# TCC HUB LMS — Architecture

## System Overview

```
                          ┌─────────────┐
                          │   Browser    │
                          └──────┬───────┘
                                 │ :80
                          ┌──────▼───────┐
                          │    Nginx     │
                          │  (reverse    │
                          │   proxy)     │
                          └──┬───────┬───┘
                   /api/     │       │    /
                   /admin/   │       │
                   /static/  │       │
                   /media/   │       │
               ┌─────────▼──┐  ┌──▼──────────┐
               │   Django    │  │   Next.js    │
               │   Backend   │  │   Frontend   │
               │   :8000     │  │   :3000      │
               └──┬──────┬───┘  └─────────────┘
                  │      │
          ┌───────▼┐  ┌──▼───────┐
          │ Postgres│  │  Redis   │
          │  :5432  │  │  :6379   │
          └────────┘  └──┬───────┘
                         │
               ┌─────────▼──────────┐
               │  Celery Worker(s)  │
               │  Celery Beat       │
               └────────────────────┘
```

## Tech Stack

### Backend
| Component          | Technology                          |
|--------------------|-------------------------------------|
| Language           | Python 3.12                         |
| Framework          | Django 5.1                          |
| REST API           | Django REST Framework 3.15          |
| Authentication     | SimpleJWT (access + refresh tokens) |
| Task Queue         | Celery 5.4 + Redis                  |
| Scheduler          | Celery Beat (django-celery-beat)    |
| Database           | PostgreSQL 16                       |
| Cache / Broker     | Redis 7                             |
| API Docs           | drf-spectacular (OpenAPI 3)         |
| PDF Generation     | WeasyPrint                          |
| WSGI Server        | Gunicorn                            |
| File Handling      | Pillow (images), Django storage     |

### Frontend
| Component          | Technology                          |
|--------------------|-------------------------------------|
| Language           | TypeScript 5.3                      |
| Framework          | Next.js 14.1 (App Router)          |
| UI Library         | React 18                            |
| Styling            | Tailwind CSS 3.4                    |
| State Management   | Zustand 4.5                         |
| Forms              | React Hook Form + Zod              |
| HTTP Client        | Axios                               |
| Animations         | Framer Motion                       |
| Charts             | Recharts                            |
| i18n               | next-intl (ru, kk, en)             |
| UI Components      | Headless UI, Heroicons              |
| Notifications      | react-hot-toast                     |

### Infrastructure
| Component          | Technology                          |
|--------------------|-------------------------------------|
| Reverse Proxy      | Nginx                               |
| Containerization   | Docker + Docker Compose             |
| Database           | PostgreSQL 16 Alpine                |
| Cache              | Redis 7 Alpine                      |

## Database Schema Overview

```
accounts
├── User (id, email, username, first_name, last_name, role, avatar, phone,
│         language, timezone, is_active, created_at)
└── Role: student | teacher | assistant | manager | coursecreator | admin

courses
├── Category (id, name, slug, description, parent, order)
├── Course (id, title, slug, description, category, cover_image,
│           language, is_published, created_by, created_at)
├── Enrollment (id, user, course, role, enrolled_at, completed_at, progress)
├── Section (id, course, title, order)
└── Activity (id, section, type, title, content, order, is_visible)

content
├── Resource (id, activity, file, url, type)  # PDF, video, link, folder
└── H5PContent (id, activity, json_content)

quizzes
├── Quiz (id, activity, time_limit, max_attempts, passing_score, shuffle)
├── Question (id, quiz, type, text, points, order)
├── Answer (id, question, text, is_correct, order)
└── Attempt (id, quiz, user, score, started_at, finished_at, answers_json)

assignments
├── Assignment (id, activity, due_date, max_score, allow_late, instructions)
├── Submission (id, assignment, user, file, text, submitted_at, is_late)
└── SubmissionGrade (id, submission, grader, score, feedback, graded_at)

grades
├── GradeItem (id, course, activity, max_score, weight)
└── Grade (id, grade_item, user, score, graded_at)

forums
├── Forum (id, course, title, type)  # announcement | discussion
├── Discussion (id, forum, author, title, pinned, created_at)
└── Post (id, discussion, author, parent, content, created_at, updated_at)

messaging
├── Conversation (id, participants, created_at)
└── Message (id, conversation, sender, content, read_at, created_at)

notifications
└── Notification (id, user, type, title, message, is_read, data_json, created_at)

calendar
└── Event (id, course, user, title, description, event_type, start, end)

certificates
└── Certificate (id, user, course, template, issued_at, uuid)

badges
├── Badge (id, name, description, image, criteria_json, course)
└── UserBadge (id, user, badge, awarded_at)

analytics
├── CourseAnalytics (id, course, date, enrollments, completions, avg_score)
└── UserActivityLog (id, user, action, object_type, object_id, timestamp)

landing
├── HeroSection (id, title, subtitle, cta_text, cta_link, image)
├── Partner (id, name, logo, url, order)
├── Testimonial (id, author, role, content, avatar, order)
└── Advantage (id, title, description, icon, order)
```

## API Structure

All API endpoints live under `/api/v1/`. Authentication uses JWT tokens (access + refresh).

```
/api/v1/
├── auth/           # register, login, token refresh, password reset
├── users/          # user CRUD, profile, avatar upload
├── courses/        # course CRUD, catalog, search
├── enrollments/    # enroll, unenroll, progress
├── sections/       # course section CRUD
├── activities/     # section activity CRUD
├── quizzes/        # quiz CRUD, questions, attempts
├── assignments/    # assignment CRUD, submissions
├── grades/         # grade book, grade items
├── forums/         # forum CRUD, discussions, posts
├── messages/       # conversations, messages
├── notifications/  # list, mark read, preferences
├── calendar/       # events CRUD
├── certificates/   # issue, download, verify
├── badges/         # badge definitions, user badges
├── analytics/      # course stats, user activity
└── landing/        # hero, partners, testimonials, advantages
```

## Authentication Flow

```
1. Registration
   POST /api/v1/auth/register/ → { email, password, first_name, last_name }
   ← 201 { user, access, refresh }

2. Login
   POST /api/v1/auth/login/ → { email, password }
   ← 200 { access, refresh }

3. Access Protected Resource
   GET /api/v1/courses/
   Headers: Authorization: Bearer <access_token>

4. Token Refresh
   POST /api/v1/auth/token/refresh/ → { refresh }
   ← 200 { access }

5. Password Reset
   POST /api/v1/auth/password-reset/ → { email }
   ← 200 (email sent with reset link)
   POST /api/v1/auth/password-reset/confirm/ → { token, new_password }
   ← 200
```

- Access tokens expire in 30 minutes (configurable)
- Refresh tokens expire in 7 days (configurable)
- Role-based permissions enforce access control per endpoint

## File Storage Strategy

| File Type       | Location          | Max Size | Formats              |
|-----------------|-------------------|----------|----------------------|
| User avatars    | /media/avatars/   | 5 MB     | jpg, png, webp       |
| Course covers   | /media/courses/   | 10 MB    | jpg, png, webp       |
| Resources       | /media/resources/ | 50 MB    | pdf, docx, mp4, etc. |
| Submissions     | /media/submissions/| 50 MB   | pdf, docx, zip       |
| Certificates    | /media/certificates/| generated| PDF (WeasyPrint)    |
| Badge images    | /media/badges/    | 2 MB     | png, svg             |

- Static files (CSS, JS, admin assets) are collected to `/app/static/` and served by Nginx
- Media files are stored in Docker volume `media_data`
- For production at scale, consider migrating to S3-compatible storage

## Deployment Architecture

### Development
```
localhost:80 → Nginx → Frontend (:3000) + Backend (:8000)
                       PostgreSQL (:5432) + Redis (:6379)
```

### Production (recommended)
```
DNS (tcchub.kz) → Load Balancer / CDN
    → Nginx (TLS termination)
        → Frontend container(s)
        → Backend container(s)
        → PostgreSQL (managed / RDS)
        → Redis (managed / ElastiCache)
        → Celery Worker(s)
        → Celery Beat (single instance)
    → S3 / MinIO (media storage)
```

### Key considerations
- Celery Beat must run as a **single instance** to avoid duplicate scheduled tasks
- PostgreSQL should use connection pooling (PgBouncer) in production
- Redis is used for both Celery broker and Django cache
- Set `DEBUG=0` and configure `ALLOWED_HOSTS` in production
- Use managed database services when possible for automatic backups
- Enable HTTPS via Certbot or cloud load balancer
