from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Donation, DonationAllocation, RecipientProfile, FoodBankProfile
from django.utils import timezone


def search_recipients(request):
    """API endpoint to search for recipients"""
    try:
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
        
        # Check if user is a foodbank
        if request.user.user_type != 'FOODBANK':
            return JsonResponse({'error': 'Access denied. Foodbank privileges required.'}, status=403)
        
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return JsonResponse({'recipients': []})
        
        # Search recipients by name, email, or phone
        recipients = RecipientProfile.objects.filter(
            Q(full_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__phone_number__icontains=query)
        ).select_related('user')[:10]
        
        recipients_data = [{
            'id': recipient.id,
            'full_name': recipient.full_name,
            'email': recipient.user.email,
            'phone': recipient.user.phone_number or ''
        } for recipient in recipients]
        
        return JsonResponse({'recipients': recipients_data})
    except Exception as e:
        import traceback
        print(f"Error in search_recipients: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def allocate_donation(request):
    """Handle donation allocation to a recipient"""
    if request.method != 'POST':
        return redirect('foodbank_inventory')
    
    if request.user.user_type != 'FOODBANK':
        messages.error(request, 'Access denied. Foodbank privileges required.')
        return redirect('dashboard')
    
    try:
        foodbank_profile = request.user.foodbank_profile
        
        donation_id = request.POST.get('donation_id')
        recipient_id = request.POST.get('recipient_id')
        allocated_quantity = int(request.POST.get('allocated_quantity', 0))
        notes = request.POST.get('notes', '')
        
        # Validate inputs
        if not donation_id or not recipient_id or allocated_quantity <= 0:
            messages.error(request, 'Invalid allocation data.')
            return redirect('foodbank_inventory')
        
        # Get donation and recipient
        donation = get_object_or_404(Donation, id=donation_id, foodbank=foodbank_profile)
        recipient = get_object_or_404(RecipientProfile, id=recipient_id)
        
        # Check if donation is already allocated
        if donation.is_allocated:
            messages.error(request, 'This donation has already been allocated.')
            return redirect('foodbank_inventory')
        
        # Check if quantity is valid
        if allocated_quantity > donation.quantity:
            messages.error(request, f'Cannot allocate more than available quantity ({donation.quantity}).')
            return redirect('foodbank_inventory')
        
        # Create allocation
        allocation = DonationAllocation.objects.create(
            donation=donation,
            recipient=recipient,
            foodbank=foodbank_profile,
            allocated_quantity=allocated_quantity,
            quantity_unit=donation.quantity_unit,
            notes=notes,
            allocated_by=request.user
        )
        
        # Mark donation as allocated
        donation.is_allocated = True
        donation.save()
        
        messages.success(
            request, 
            f'Successfully allocated {allocated_quantity} {donation.get_quantity_unit_display()} of {donation.item_name} to {recipient.full_name}.'
        )
        
    except Exception as e:
        messages.error(request, f'Error allocating donation: {str(e)}')
    
    return redirect('foodbank_inventory')


@login_required
def acknowledge_allocation(request, allocation_id):
    """Handle recipient acknowledgment of donation allocation"""
    if request.method != 'POST':
        return redirect('dashboard')
    
    if request.user.user_type != 'RECIPIENT':
        messages.error(request, 'Access denied. Recipient privileges required.')
        return redirect('dashboard')
    
    try:
        recipient_profile = request.user.recipient_profile
        
        # Get allocation
        allocation = get_object_or_404(
            DonationAllocation, 
            id=allocation_id, 
            recipient=recipient_profile
        )
        
        # Check if already acknowledged
        if allocation.is_acknowledged:
            messages.info(request, 'This allocation has already been acknowledged.')
            return redirect('dashboard')
        
        # Mark as acknowledged
        allocation.is_acknowledged = True
        allocation.acknowledged_at = timezone.now()
        allocation.save()
        
        messages.success(
            request, 
            f'Successfully acknowledged receipt of {allocation.allocated_quantity} {allocation.get_quantity_unit_display()} of {allocation.donation.item_name}.'
        )
        
    except Exception as e:
        messages.error(request, f'Error acknowledging allocation: {str(e)}')
    
    return redirect('dashboard')
