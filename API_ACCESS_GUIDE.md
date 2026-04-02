# API Access Guide

## 🌐 Root URL Access

The Django server now provides a beautiful home page at the root URL:

**Home Page**: `http://127.0.0.1:8000/`

This page displays:
- All available API endpoints organized by category
- Quick access links to documentation
- Visual representation of HTTP methods (GET, POST, PATCH)
- Description of each endpoint

## 📋 Available URLs

### Root & Info
- **`/`** - API Home Page (HTML)
- **`/api/info/`** - API Information (JSON)

### User Authentication Endpoints
- **`POST /users/register/`** - Register new user
- **`POST /users/login/`** - Login and get JWT tokens
- **`POST /users/logout/`** - Logout (requires authentication)
- **`POST /users/token/refresh/`** - Refresh JWT access token

### User Profile Endpoints
- **`GET /users/profile/`** - Get user profile (requires authentication)
- **`PATCH /users/profile/`** - Update user profile (requires authentication)

### Documentation
- **`/swagger/`** - Swagger UI API Documentation
- **`/redoc/`** - ReDoc API Documentation
- **`/admin/`** - Django Admin Panel

## 🚀 Testing the API

### 1. Visit the Home Page
Open your browser and go to:
```
http://127.0.0.1:8000/
```

### 2. Register a New User (Example)
```bash
curl -X POST http://127.0.0.1:8000/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone_number": "+1234567890",
    "password": "securepass123",
    "role": "patient",
    "gender": "M",
    "age": 30,
    "address": "123 Main St"
  }'
```

### 3. Login
```bash
curl -X POST http://127.0.0.1:8000/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### 4. Get API Info (JSON)
```bash
curl http://127.0.0.1:8000/api/info/
```

## 📱 Features of the Home Page

- **Modern UI**: Beautiful gradient design with responsive layout
- **Organized Endpoints**: Endpoints grouped by category
- **HTTP Method Tags**: Color-coded method badges (GET=blue, POST=green, PATCH=yellow)
- **Quick Links**: Direct buttons to important pages
- **API Information**: Link to JSON API info endpoint

## 🔄 Server Status

If you see a 404 error:
1. Make sure the Django server is running
2. Check that you're accessing `http://127.0.0.1:8000/` (with the trailing slash)
3. Verify the server logs for any errors

The server should automatically reload when you make changes to Python files. If it doesn't, restart the server:
```bash
cd telemedicine_project
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

