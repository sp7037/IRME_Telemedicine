from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

def api_home(request):
    """
    Home page displaying all available API endpoints and documentation links.
    """
    context = {
        'api_endpoints': {
            'User Authentication': [
                {'method': 'POST', 'path': '/users/register/', 'description': 'Register a new user (doctor, patient, or TMC operator)'},
                {'method': 'POST', 'path': '/users/login/', 'description': 'Login and get JWT tokens'},
                {'method': 'POST', 'path': '/users/logout/', 'description': 'Logout and blacklist refresh token'},
                {'method': 'POST', 'path': '/users/token/refresh/', 'description': 'Refresh JWT access token'},
            ],
            'User Profile': [
                {'method': 'GET', 'path': '/users/profile/', 'description': 'Get authenticated user profile'},
                {'method': 'PATCH', 'path': '/users/profile/', 'description': 'Update authenticated user profile'},
            ],
            'Documentation': [
                {'method': 'GET', 'path': '/swagger/', 'description': 'Swagger UI API Documentation'},
                {'method': 'GET', 'path': '/redoc/', 'description': 'ReDoc API Documentation'},
                {'method': 'GET', 'path': '/admin/', 'description': 'Django Admin Panel'},
            ],
        }
    }
    return render(request, 'api_home.html', context)


@require_http_methods(["GET"])
def api_info(request):
    """
    JSON endpoint providing API information.
    """
    return JsonResponse({
        'name': 'Telemedicine API',
        'version': '1.0.0',
        'description': 'Telemedicine application API with user registration, authentication, and consultation management',
        'endpoints': {
            'user_registration': '/users/register/',
            'user_login': '/users/login/',
            'user_logout': '/users/logout/',
            'token_refresh': '/users/token/refresh/',
            'user_profile': '/users/profile/',
            'swagger_docs': '/swagger/',
            'redoc_docs': '/redoc/',
            'admin': '/admin/',
        },
        'registration_roles': ['doctor', 'patient', 'tmc'],
        'status': 'running'
    })

