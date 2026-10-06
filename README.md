# ResumeIQ – AI Interview Coach

A full-stack AI-powered interview coaching platform built as an MCA final-year project.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite |
| Backend | Django 5 + Django REST Framework |
| Auth | JWT via `djangorestframework-simplejwt` |
| Database | SQLite (dev) → PostgreSQL (prod) |

## Project Structure

```
ResumeIQ/
├── backend/          # Django REST API
│   ├── core/         # Project config & settings
│   └── apps/
│       └── authentication/   # Unit 1 – Auth module
└── frontend/         # React + Vite SPA
    └── src/
        ├── api/      # Axios service layer
        ├── context/  # AuthContext (global state)
        ├── hooks/    # useAuth hook
        ├── pages/    # LoginPage, RegisterPage, DashboardPage
        ├── components/auth/  # ProtectedRoute
        └── utils/    # tokenStorage helpers
```

## Modules

| Unit | Module | Status |
|---|---|---|
| 1 | Authentication (Register, Login, JWT, Profile) | ✅ Complete |
| 2 | Resume Upload & ATS Analysis | 🔜 Upcoming |
| 3 | Mock Interview | 🔜 Upcoming |
| 4 | Performance Reports | 🔜 Upcoming |
| 5 | AI Coaching Tips | 🔜 Upcoming |

## Getting Started

### Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

### Run Backend Tests
```bash
cd backend
.\venv\Scripts\python manage.py test apps.authentication --verbosity=2
```

## API Endpoints (Unit 1)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | No | Create account |
| POST | `/api/auth/login/` | No | Get JWT tokens |
| POST | `/api/auth/refresh/` | No | Refresh access token |
| POST | `/api/auth/logout/` | Bearer | Blacklist refresh token |
| GET | `/api/auth/profile/` | Bearer | Fetch profile |
| PATCH | `/api/auth/profile/` | Bearer | Update profile |
