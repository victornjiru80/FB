"""
User Action Views for Custom Admin
Handles toggle status and delete user actions
"""
from django.shortcuts import get_object_or_404
from .decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from authentication.models import CustomUser
import json


@staff_member_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Toggle the status
        user.is_active = not user.is_active
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
            'new_status': user.is_active
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@staff_member_required
@require_http_methods(["POST"])
def delete_user(request, user_id):
    """Delete a user"""
    try:
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Prevent deleting superusers
        if user.is_superuser:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete superuser accounts'
            }, status=403)
        
        # Prevent self-deletion
        if user.id == request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Cannot delete your own account'
            }, status=403)
        
        user_email = user.email
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {user_email} deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
