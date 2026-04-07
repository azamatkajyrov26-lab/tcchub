# TCC HUB LMS — API Reference

Base URL: `/api/v1/`

Authentication: JWT Bearer token in `Authorization` header, unless marked as **Public**.

Pagination: `?page=1&page_size=20` (default 20, max 100).

Filtering: `?search=`, `?ordering=`, plus model-specific filters.

---

## Auth (`/api/v1/auth/`)

| Method | Endpoint                        | Auth     | Description                     |
|--------|---------------------------------|----------|---------------------------------|
| POST   | `/auth/register/`               | Public   | Register new user               |
| POST   | `/auth/login/`                  | Public   | Obtain access + refresh tokens  |
| POST   | `/auth/token/refresh/`          | Public   | Refresh access token            |
| POST   | `/auth/password-reset/`         | Public   | Request password reset email    |
| POST   | `/auth/password-reset/confirm/` | Public   | Confirm password reset          |
| POST   | `/auth/change-password/`        | Required | Change current user password    |
| POST   | `/auth/logout/`                 | Required | Blacklist refresh token         |

### Register
```
POST /api/v1/auth/register/
{
  "email": "user@example.com",
  "username": "user1",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "language": "ru"
}
→ 201 { "user": {...}, "access": "...", "refresh": "..." }
```

### Login
```
POST /api/v1/auth/login/
{ "email": "user@example.com", "password": "SecurePass123!" }
→ 200 { "access": "...", "refresh": "..." }
```

---

## Users (`/api/v1/users/`)

| Method | Endpoint              | Auth     | Permission          | Description             |
|--------|-----------------------|----------|---------------------|-------------------------|
| GET    | `/users/`             | Required | Admin/Manager       | List all users          |
| POST   | `/users/`             | Required | Admin               | Create user             |
| GET    | `/users/{id}/`        | Required | Owner/Admin         | Get user detail         |
| PATCH  | `/users/{id}/`        | Required | Owner/Admin         | Update user             |
| DELETE | `/users/{id}/`        | Required | Admin               | Deactivate user         |
| GET    | `/users/me/`          | Required | Any                 | Get current user        |
| PATCH  | `/users/me/`          | Required | Any                 | Update current user     |
| POST   | `/users/me/avatar/`   | Required | Any                 | Upload avatar           |
| GET    | `/users/{id}/courses/`| Required | Owner/Admin         | List user's courses     |

---

## Courses (`/api/v1/courses/`)

| Method | Endpoint                        | Auth     | Permission              | Description               |
|--------|---------------------------------|----------|-------------------------|---------------------------|
| GET    | `/courses/`                     | Public   | —                       | List published courses    |
| POST   | `/courses/`                     | Required | Teacher/Admin           | Create course             |
| GET    | `/courses/{id}/`                | Public   | —                       | Course detail             |
| PATCH  | `/courses/{id}/`                | Required | Owner/Admin             | Update course             |
| DELETE | `/courses/{id}/`                | Required | Owner/Admin             | Delete course             |
| GET    | `/courses/categories/`          | Public   | —                       | List categories           |
| POST   | `/courses/categories/`          | Required | Admin                   | Create category           |
| PATCH  | `/courses/categories/{id}/`     | Required | Admin                   | Update category           |
| DELETE | `/courses/categories/{id}/`     | Required | Admin                   | Delete category           |

Filter: `?category=`, `?search=`, `?language=`, `?ordering=created_at`

---

## Enrollments (`/api/v1/enrollments/`)

| Method | Endpoint                         | Auth     | Permission        | Description               |
|--------|----------------------------------|----------|-------------------|---------------------------|
| GET    | `/enrollments/`                  | Required | Admin/Teacher     | List all enrollments       |
| POST   | `/enrollments/`                  | Required | Any               | Enroll in course           |
| GET    | `/enrollments/{id}/`             | Required | Owner/Admin       | Enrollment detail          |
| DELETE | `/enrollments/{id}/`             | Required | Owner/Admin       | Unenroll                   |
| GET    | `/enrollments/my/`               | Required | Any               | Current user enrollments   |
| PATCH  | `/enrollments/{id}/progress/`    | Required | System            | Update progress            |

```
POST /api/v1/enrollments/
{ "course": 1 }
→ 201 { "id": 1, "course": 1, "user": 5, "role": "student", "progress": 0, "enrolled_at": "..." }
```

---

## Sections (`/api/v1/courses/{course_id}/sections/`)

| Method | Endpoint                           | Auth     | Permission     | Description        |
|--------|------------------------------------|----------|----------------|--------------------|
| GET    | `/courses/{cid}/sections/`         | Required | Enrolled       | List sections      |
| POST   | `/courses/{cid}/sections/`         | Required | Teacher/Admin  | Create section     |
| GET    | `/courses/{cid}/sections/{id}/`    | Required | Enrolled       | Section detail     |
| PATCH  | `/courses/{cid}/sections/{id}/`    | Required | Teacher/Admin  | Update section     |
| DELETE | `/courses/{cid}/sections/{id}/`    | Required | Teacher/Admin  | Delete section     |
| POST   | `/courses/{cid}/sections/reorder/` | Required | Teacher/Admin  | Reorder sections   |

---

## Activities (`/api/v1/sections/{section_id}/activities/`)

| Method | Endpoint                                | Auth     | Permission     | Description         |
|--------|-----------------------------------------|----------|----------------|---------------------|
| GET    | `/sections/{sid}/activities/`           | Required | Enrolled       | List activities     |
| POST   | `/sections/{sid}/activities/`           | Required | Teacher/Admin  | Create activity     |
| GET    | `/sections/{sid}/activities/{id}/`      | Required | Enrolled       | Activity detail     |
| PATCH  | `/sections/{sid}/activities/{id}/`      | Required | Teacher/Admin  | Update activity     |
| DELETE | `/sections/{sid}/activities/{id}/`      | Required | Teacher/Admin  | Delete activity     |
| POST   | `/sections/{sid}/activities/reorder/`   | Required | Teacher/Admin  | Reorder activities  |

Activity types: `resource`, `quiz`, `assignment`, `forum`, `folder`, `url`, `glossary`

---

## Quizzes (`/api/v1/quizzes/`)

| Method | Endpoint                              | Auth     | Permission       | Description             |
|--------|---------------------------------------|----------|------------------|-------------------------|
| GET    | `/quizzes/{id}/`                      | Required | Enrolled         | Quiz detail             |
| PATCH  | `/quizzes/{id}/`                      | Required | Teacher/Admin    | Update quiz settings    |
| GET    | `/quizzes/{id}/questions/`            | Required | Enrolled         | List questions          |
| POST   | `/quizzes/{id}/questions/`            | Required | Teacher/Admin    | Add question            |
| PATCH  | `/quizzes/{id}/questions/{qid}/`      | Required | Teacher/Admin    | Update question         |
| DELETE | `/quizzes/{id}/questions/{qid}/`      | Required | Teacher/Admin    | Delete question         |
| POST   | `/quizzes/{id}/attempts/`             | Required | Student          | Start attempt           |
| GET    | `/quizzes/{id}/attempts/`             | Required | Enrolled         | List user attempts      |
| POST   | `/quizzes/{id}/attempts/{aid}/submit/`| Required | Student          | Submit attempt          |
| GET    | `/quizzes/{id}/attempts/{aid}/`       | Required | Owner/Teacher    | Attempt result          |

### Start Attempt
```
POST /api/v1/quizzes/3/attempts/
→ 201 { "id": 1, "quiz": 3, "started_at": "...", "questions": [...] }
```

### Submit Attempt
```
POST /api/v1/quizzes/3/attempts/1/submit/
{
  "answers": [
    { "question": 1, "selected_answers": [3] },
    { "question": 2, "text_answer": "Supply chain management..." }
  ]
}
→ 200 { "id": 1, "score": 85, "passed": true, "finished_at": "..." }
```

---

## Assignments (`/api/v1/assignments/`)

| Method | Endpoint                                    | Auth     | Permission      | Description           |
|--------|---------------------------------------------|----------|-----------------|-----------------------|
| GET    | `/assignments/{id}/`                        | Required | Enrolled        | Assignment detail     |
| PATCH  | `/assignments/{id}/`                        | Required | Teacher/Admin   | Update assignment     |
| GET    | `/assignments/{id}/submissions/`            | Required | Teacher/Admin   | List all submissions  |
| POST   | `/assignments/{id}/submissions/`            | Required | Student         | Submit work           |
| GET    | `/assignments/{id}/submissions/{sid}/`      | Required | Owner/Teacher   | Submission detail     |
| PATCH  | `/assignments/{id}/submissions/{sid}/grade/`| Required | Teacher/Admin   | Grade submission      |

### Submit Work
```
POST /api/v1/assignments/5/submissions/
Content-Type: multipart/form-data
{ "file": <file>, "text": "My analysis of..." }
→ 201 { "id": 1, "submitted_at": "...", "is_late": false }
```

### Grade Submission
```
PATCH /api/v1/assignments/5/submissions/1/grade/
{ "score": 90, "feedback": "Excellent analysis." }
→ 200 { "score": 90, "feedback": "...", "graded_at": "..." }
```

---

## Grades (`/api/v1/grades/`)

| Method | Endpoint                              | Auth     | Permission       | Description               |
|--------|---------------------------------------|----------|------------------|---------------------------|
| GET    | `/grades/courses/{cid}/`              | Required | Teacher/Admin    | Full gradebook for course |
| GET    | `/grades/courses/{cid}/users/{uid}/`  | Required | Owner/Teacher    | User grades for course    |
| GET    | `/grades/my/`                         | Required | Any              | Current user all grades   |
| PATCH  | `/grades/{id}/`                       | Required | Teacher/Admin    | Override a grade          |

---

## Forums (`/api/v1/forums/`)

| Method | Endpoint                                      | Auth     | Permission      | Description          |
|--------|-----------------------------------------------|----------|-----------------|----------------------|
| GET    | `/forums/`                                    | Required | Enrolled        | List forums          |
| GET    | `/forums/{id}/`                               | Required | Enrolled        | Forum detail         |
| GET    | `/forums/{id}/discussions/`                   | Required | Enrolled        | List discussions     |
| POST   | `/forums/{id}/discussions/`                   | Required | Enrolled        | Create discussion    |
| GET    | `/forums/{id}/discussions/{did}/`             | Required | Enrolled        | Discussion detail    |
| PATCH  | `/forums/{id}/discussions/{did}/`             | Required | Owner/Teacher   | Update discussion    |
| DELETE | `/forums/{id}/discussions/{did}/`             | Required | Owner/Teacher   | Delete discussion    |
| GET    | `/forums/{id}/discussions/{did}/posts/`       | Required | Enrolled        | List posts           |
| POST   | `/forums/{id}/discussions/{did}/posts/`       | Required | Enrolled        | Reply to discussion  |
| PATCH  | `/forums/{id}/discussions/{did}/posts/{pid}/` | Required | Owner/Teacher   | Edit post            |
| DELETE | `/forums/{id}/discussions/{did}/posts/{pid}/` | Required | Owner/Teacher   | Delete post          |

Filter discussions: `?pinned=true`, `?search=`, `?ordering=-created_at`

---

## Messages (`/api/v1/messages/`)

| Method | Endpoint                                | Auth     | Permission | Description              |
|--------|-----------------------------------------|----------|------------|--------------------------|
| GET    | `/messages/conversations/`              | Required | Any        | List conversations       |
| POST   | `/messages/conversations/`              | Required | Any        | Start conversation       |
| GET    | `/messages/conversations/{id}/`         | Required | Participant| Conversation messages    |
| POST   | `/messages/conversations/{id}/`         | Required | Participant| Send message             |
| PATCH  | `/messages/conversations/{id}/read/`    | Required | Participant| Mark as read             |
| GET    | `/messages/unread-count/`               | Required | Any        | Unread message count     |

---

## Notifications (`/api/v1/notifications/`)

| Method | Endpoint                           | Auth     | Permission | Description               |
|--------|------------------------------------|----------|------------|---------------------------|
| GET    | `/notifications/`                  | Required | Any        | List notifications        |
| PATCH  | `/notifications/{id}/read/`        | Required | Owner      | Mark as read              |
| POST   | `/notifications/read-all/`         | Required | Any        | Mark all as read          |
| GET    | `/notifications/unread-count/`     | Required | Any        | Unread count              |
| GET    | `/notifications/preferences/`      | Required | Any        | Get notification prefs    |
| PATCH  | `/notifications/preferences/`      | Required | Any        | Update notification prefs |

Notification types: `assignment_due`, `assignment_graded`, `quiz_available`, `course_completed`, `forum_reply`, `new_message`, `enrollment_confirmed`, `certificate_issued`, `badge_awarded`, `system`

---

## Calendar (`/api/v1/calendar/`)

| Method | Endpoint              | Auth     | Permission     | Description         |
|--------|-----------------------|----------|----------------|---------------------|
| GET    | `/calendar/events/`   | Required | Any            | List events         |
| POST   | `/calendar/events/`   | Required | Teacher/Admin  | Create event        |
| GET    | `/calendar/events/{id}/`| Required | Enrolled      | Event detail        |
| PATCH  | `/calendar/events/{id}/`| Required | Teacher/Admin | Update event        |
| DELETE | `/calendar/events/{id}/`| Required | Teacher/Admin | Delete event        |

Filter: `?start_date=`, `?end_date=`, `?course=`, `?event_type=`

---

## Certificates (`/api/v1/certificates/`)

| Method | Endpoint                        | Auth     | Permission     | Description              |
|--------|---------------------------------|----------|----------------|--------------------------|
| GET    | `/certificates/`                | Required | Any            | List user certificates   |
| POST   | `/certificates/issue/`          | Required | System/Teacher | Issue certificate        |
| GET    | `/certificates/{id}/`           | Required | Owner          | Certificate detail       |
| GET    | `/certificates/{id}/download/`  | Required | Owner          | Download PDF             |
| GET    | `/certificates/verify/{uuid}/`  | Public   | —              | Verify certificate       |

---

## Badges (`/api/v1/badges/`)

| Method | Endpoint                     | Auth     | Permission    | Description            |
|--------|------------------------------|----------|---------------|------------------------|
| GET    | `/badges/`                   | Required | Any           | List all badges        |
| POST   | `/badges/`                   | Required | Admin         | Create badge           |
| GET    | `/badges/{id}/`              | Required | Any           | Badge detail           |
| PATCH  | `/badges/{id}/`              | Required | Admin         | Update badge           |
| DELETE | `/badges/{id}/`              | Required | Admin         | Delete badge           |
| GET    | `/badges/my/`                | Required | Any           | Current user badges    |
| POST   | `/badges/{id}/award/`        | Required | Teacher/Admin | Award badge to user    |

---

## Analytics (`/api/v1/analytics/`)

| Method | Endpoint                                | Auth     | Permission     | Description                  |
|--------|-----------------------------------------|----------|----------------|------------------------------|
| GET    | `/analytics/courses/{cid}/`             | Required | Teacher/Admin  | Course analytics dashboard   |
| GET    | `/analytics/courses/{cid}/enrollments/` | Required | Teacher/Admin  | Enrollment trends            |
| GET    | `/analytics/courses/{cid}/completion/`  | Required | Teacher/Admin  | Completion rates             |
| GET    | `/analytics/courses/{cid}/grades/`      | Required | Teacher/Admin  | Grade distribution           |
| GET    | `/analytics/users/{uid}/activity/`      | Required | Owner/Admin    | User activity log            |
| GET    | `/analytics/overview/`                  | Required | Admin          | Platform-wide stats          |

---

## Landing Page (`/api/v1/landing/`)

All landing endpoints are **Public** (read) and **Admin** (write).

| Method | Endpoint                    | Auth     | Permission | Description           |
|--------|-----------------------------|----------|------------|-----------------------|
| GET    | `/landing/hero/`            | Public   | —          | Hero section data     |
| PATCH  | `/landing/hero/`            | Required | Admin      | Update hero section   |
| GET    | `/landing/partners/`        | Public   | —          | List partners         |
| POST   | `/landing/partners/`        | Required | Admin      | Add partner           |
| PATCH  | `/landing/partners/{id}/`   | Required | Admin      | Update partner        |
| DELETE | `/landing/partners/{id}/`   | Required | Admin      | Remove partner        |
| GET    | `/landing/testimonials/`    | Public   | —          | List testimonials     |
| POST   | `/landing/testimonials/`    | Required | Admin      | Add testimonial       |
| PATCH  | `/landing/testimonials/{id}/`| Required | Admin     | Update testimonial    |
| DELETE | `/landing/testimonials/{id}/`| Required | Admin     | Remove testimonial    |
| GET    | `/landing/advantages/`      | Public   | —          | List advantages       |
| POST   | `/landing/advantages/`      | Required | Admin      | Add advantage         |
| PATCH  | `/landing/advantages/{id}/` | Required | Admin      | Update advantage      |
| DELETE | `/landing/advantages/{id}/` | Required | Admin      | Remove advantage      |
| GET    | `/landing/metrics/`         | Public   | —          | Platform metrics      |

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

| HTTP Code | Meaning                |
|-----------|------------------------|
| 400       | Bad request / validation error |
| 401       | Unauthorized (no/invalid token) |
| 403       | Forbidden (insufficient permissions) |
| 404       | Not found              |
| 429       | Rate limited           |
| 500       | Internal server error  |

## Rate Limiting

- Anonymous: 100 requests/minute
- Authenticated: 1000 requests/minute
- Login attempts: 5/minute per IP

## Interactive Documentation

When the backend is running, OpenAPI docs are available at:
- **Swagger UI:** `/api/schema/swagger-ui/`
- **ReDoc:** `/api/schema/redoc/`
- **OpenAPI JSON:** `/api/schema/`
