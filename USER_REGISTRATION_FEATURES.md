# Telemedicine Project - User Registration Features

## Overview
This Django telemedicine application supports multi-role user registration with role-based profiles.

## User Registration System

### 1. **User Model** (`users/models/users.py`)
- **Custom User Model**: Extends Django's `AbstractUser`
- **Fields**:
  - `email` (unique, indexed) - Primary identifier (no username)
  - `phone_number` (unique, indexed)
  - `first_name`, `last_name`
  - Role flags: `is_doctor`, `is_patient`, `is_tmc_operator`
- **Authentication**: Email-based authentication

### 2. **Role-Based Profiles** (`users/models/profiles.py`)

#### **DoctorProfile**
- Fields:
  - `qualification`
  - `specialty`
  - `experience`
  - `license_number` (unique, validated format: uppercase letters, numbers, hyphens)
  - `practice_type`
  - `date_of_birth`
  - `photo` (ImageField)
  - `signature` (ImageField)
  - `hospital_or_clinic_name`
- Auto-creates `DoctorAvailability` on profile creation

#### **PatientProfile**
- Fields:
  - `gender` (M/F/O)
  - `age`
  - `address`

#### **TMCProfile** (Telemedicine Center Operator)
- Fields:
  - `tmc_details`

### 3. **Registration API Endpoint**

**URL**: `POST /users/register/`

**Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone_number": "+1234567890",
  "password": "securepassword123",
  "role": "doctor|patient|tmc",
  // For patients only:
  "gender": "M|F|O",
  "age": 30,
  "address": "123 Main St"
}
```

**Response**: 
- `201 Created`: User registered successfully
- `400 Bad Request`: Validation errors or duplicate email/phone

**Features**:
- Validates unique email and phone number
- Creates appropriate role-based profile automatically
- Password hashing handled automatically
- Rate limiting (5000 requests/minute for anonymous users)
- Caching for performance

### 4. **Authentication Features**

#### **Login** (`POST /users/login/`)
- Email/password authentication
- Returns JWT tokens (access + refresh)
- Returns user type (doctor/patient/tmc)

#### **Logout** (`POST /users/logout/`)
- Token blacklisting
- Requires refresh token

#### **Token Refresh** (`POST /users/token/refresh/`)
- Refresh access tokens

### 5. **Profile Management**

**Endpoint**: `GET/PATCH /users/profile/`
- Fetch or update user profile
- Role-specific profile data
- Caching enabled (5-10 minutes)
- Requires authentication

### 6. **Security Features**
- JWT authentication (60 min access, 1 day refresh)
- Token blacklisting
- Password validators (minimum length, complexity)
- CORS configured for React frontend (localhost:3000)
- Rate limiting
- CSP (Content Security Policy) headers

### 7. **Admin Interface**
- Custom UserAdmin with role filtering
- Separate admin interfaces for:
  - DoctorProfile
  - PatientProfile
  - TMCProfile
- Consultation models integrated

### 8. **API Documentation**
- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`

## File Structure

```
telemedicine_project/
├── users/
│   ├── models/
│   │   ├── users.py          # Custom User model
│   │   └── profiles.py       # Role-based profiles
│   ├── serializers/
│   │   ├── authentication.py # Registration & Login serializers
│   │   └── profiles.py       # Profile serializers
│   ├── views/
│   │   ├── authentication.py # Register, Login, Logout views
│   │   └── profiles.py       # Profile management views
│   ├── urls.py               # User endpoints
│   └── admin.py              # Admin configuration
├── telemedicine_project/
│   ├── settings.py           # Django settings
│   └── urls.py               # Root URL configuration
└── requirements.txt          # Dependencies
```

## Registration Flow

1. Client sends POST to `/users/register/` with user data and role
2. `UserRegisterSerializer` validates data (email uniqueness, phone uniqueness, password strength)
3. `RegisterAPIView` creates User with appropriate role flags
4. Role-specific profile is created (DoctorProfile/PatientProfile/TMCProfile)
5. User is cached for quick lookups
6. Success response returned

## Testing the Registration

### Example cURL for Doctor Registration:
```bash
curl -X POST http://localhost:8000/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Dr. Jane",
    "last_name": "Smith",
    "email": "doctor@example.com",
    "phone_number": "+1234567890",
    "password": "securepass123",
    "role": "doctor"
  }'
```

### Example cURL for Patient Registration:
```bash
curl -X POST http://localhost:8000/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "patient@example.com",
    "phone_number": "+9876543210",
    "password": "securepass123",
    "role": "patient",
    "gender": "M",
    "age": 30,
    "address": "123 Main St"
  }'
```

## Dependencies
- Django 5.1.6
- Django REST Framework 3.15.2
- djangorestframework-simplejwt 5.3.1 (JWT tokens)
- channels 4.0.0 (WebSocket support)
- daphne 4.1.0 (ASGI server)
- drf-yasg 1.21.7 (API documentation)
- django-cors-headers 4.6.0 (CORS support)
- Pillow 11.1.0 (Image handling)
- psycopg2-binary 2.9.10 (PostgreSQL)

## Database
- PostgreSQL (configured in settings.py)
- Database name: `telemedicine25`
- Migrations: All applied

## Server
- Running on: `http://127.0.0.1:8000/` (default Django port)
- Admin: `http://127.0.0.1:8000/admin/`
- API Docs: `http://127.0.0.1:8000/swagger/`

