from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, DonorProfile, FoodBankProfile, RecipientProfile, FoodBankRequest, Donation, DonationAllocation, Testimonial, Subscription, FoodBankSubscription, SubscriptionPayment
from django.urls import path
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Sum
from django.contrib.admin import AdminSite
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
import io
from reportlab.pdfgen import canvas
import json

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('user_type', 'is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

class FoodBankRequestAdmin(admin.ModelAdmin):
    list_display = ('foodbank', 'title', 'get_location', 'priority', 'status', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    search_fields = (
        'foodbank__foodbank_name',
        'foodbank__address',
        'title',
        'description',
        'original_request__location',
        'linked_request_management__location',
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-priority', '-created_at')

    def get_location(self, obj):
        if obj.original_request and obj.original_request.location:
            return obj.original_request.location
        if obj.linked_request_management and obj.linked_request_management.location:
            return obj.linked_request_management.location
        if obj.foodbank and obj.foodbank.address:
            return obj.foodbank.address
        return '-'
    get_location.short_description = 'Location'

# Unregister the default admin site and register the custom one
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(DonorProfile)
admin.site.register(FoodBankProfile)
admin.site.register(RecipientProfile)
admin.site.register(FoodBankRequest, FoodBankRequestAdmin)

@admin.register(DonationAllocation)
class DonationAllocationAdmin(admin.ModelAdmin):
    list_display = ['donation', 'recipient', 'quantity', 'amount', 'allocated_at']
    list_filter = ['allocated_at', 'donation__donation_type']
    search_fields = ['donation__donor__email', 'recipient__full_name', 'donation__item_name']
    date_hierarchy = 'allocated_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('donation', 'recipient', 'donation__donor')

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['get_recipient_name', 'approval_status', 'is_featured', 'display_on_public', 'created_at', 'reviewed_by']
    list_filter = ['approval_status', 'is_featured', 'display_on_public', 'created_at']
    search_fields = ['recipient__full_name', 'recipient__organization_name', 'message']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Testimonial Info', {
            'fields': ('recipient', 'message', 'impact_image')
        }),
        ('Approval', {
            'fields': ('approval_status', 'reviewed_by', 'reviewed_at', 'rejection_reason')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'display_on_public', 'display_start_date', 'display_end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_recipient_name(self, obj):
        if obj.recipient.is_organization:
            return obj.recipient.organization_name
        return obj.recipient.full_name
    get_recipient_name.short_description = 'Recipient'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient__user', 'reviewed_by')

@staff_member_required
def custom_admin_dashboard(request):
    from .models import Donation
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import timedelta

    # KPIs
    total_users = CustomUser.objects.count()
    total_donors = CustomUser.objects.filter(user_type='DONOR').count()
    total_foodbanks = CustomUser.objects.filter(user_type='FOODBANK').count()
    total_recipients = CustomUser.objects.filter(user_type='RECIPIENT').count()
    total_donations = Donation.objects.count()
    total_donated_amount = Donation.objects.aggregate(
        total=Sum('amount'))['total'] or 0

    # User counts by type (pie chart)
    user_counts = CustomUser.objects.values('user_type').annotate(count=Count('id'))
    user_type_labels = [uc['user_type'] for uc in user_counts]
    user_type_data = [uc['count'] for uc in user_counts]

    # Registrations over the last 12 months (line chart)
    now = timezone.now()
    months = [(now - timedelta(days=30*i)).strftime('%b %Y') for i in reversed(range(12))]
    registration_counts = []
    for i in reversed(range(12)):
        start = (now - timedelta(days=30*(i+1)))
        end = (now - timedelta(days=30*i))
        count = CustomUser.objects.filter(date_joined__gte=start, date_joined__lt=end).count()
        registration_counts.append(count)

    # Donations by type (bar chart)
    donation_counts = Donation.objects.values('donation_type').annotate(count=Count('id'))
    donation_type_labels = [d['donation_type'] for d in donation_counts]
    donation_type_data = [d['count'] for d in donation_counts]

    context = {
        'total_users': total_users,
        'total_donors': total_donors,
        'total_foodbanks': total_foodbanks,
        'total_recipients': total_recipients,
        'total_donations': total_donations,
        'total_donated_amount': total_donated_amount,
        'user_type_labels': json.dumps(user_type_labels),
        'user_type_data': json.dumps(user_type_data),
        'registration_months': json.dumps(months),
        'registration_counts': json.dumps(registration_counts),
        'donation_type_labels': json.dumps(donation_type_labels),
        'donation_type_data': json.dumps(donation_type_data),
    }
    return TemplateResponse(request, 'admin/custom_dashboard.html', context)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type', 'is_active', 'payment_status', 'last_payment_date', 'end_date')
    list_filter = ('user_type', 'is_active', 'payment_status')
    search_fields = ('user__username',)


@admin.register(FoodBankSubscription)
class FoodBankSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('foodbank', 'plan', 'status', 'trial_end_date', 'subscription_end_date', 'days_remaining')
    list_filter = ('status', 'plan', 'created_at')
    search_fields = ('foodbank__foodbank_name', 'foodbank__user__email')
    readonly_fields = ('created_at', 'updated_at', 'trial_start_date')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Food Bank Info', {
            'fields': ('foodbank',)
        }),
        ('Subscription Details', {
            'fields': ('plan', 'status')
        }),
        ('Trial Period', {
            'fields': ('trial_start_date', 'trial_end_date')
        }),
        ('Paid Subscription', {
            'fields': ('subscription_start_date', 'subscription_end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('foodbank', 'foodbank__user')
    
from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from .models import AccountDeletionRequest

@admin.action(description='Approve selected deletion requests')
def approve_deletion_requests(modeladmin, request, queryset):
    for deletion_request in queryset.filter(status='pending'):
        user = deletion_request.user
        user.is_active = False  # Deactivate user
        user.save()
        
        # Delete user data (customize based on your needs)
        # user.delete()  # Uncomment if you want to permanently delete
        
        deletion_request.status = 'approved'
        deletion_request.processed_by = request.user
        deletion_request.processed_at = timezone.now()
        deletion_request.save()
        
        # Notify user
        Notification.objects.create(
            user=user,
            notification_type='account_deletion_approved',
            message="Your account deletion request has been approved. Your account has been deactivated."
        )
    
    messages.success(request, "Selected deletion requests have been approved.")

@admin.action(description='Reject selected deletion requests')
def reject_deletion_requests(modeladmin, request, queryset):
    for deletion_request in queryset.filter(status='pending'):
        deletion_request.status = 'rejected'
        deletion_request.processed_by = request.user
        deletion_request.processed_at = timezone.now()
        deletion_request.save()
        
        # Notify user
        Notification.objects.create(
            user=deletion_request.user,
            notification_type='account_deletion_rejected',
            message="Your account deletion request has been rejected. Please contact support for more information."
        )
    
    messages.success(request, "Selected deletion requests have been rejected.")

@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'requested_at', 'processed_at', 'processed_by']
    list_filter = ['status', 'requested_at']
    actions = [approve_deletion_requests, reject_deletion_requests]
    readonly_fields = ['user', 'requested_at']
    
    def has_add_permission(self, request):
        return False    


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('foodbank', 'plan_type', 'amount', 'payment_method', 'status', 'submitted_at', 'verified_by')
    list_filter = ('status', 'plan_type', 'payment_method', 'submitted_at')
    search_fields = ('foodbank__foodbank_name', 'transaction_reference', 'foodbank__user__email')
    readonly_fields = ('submitted_at', 'updated_at', 'verified_at')
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('Food Bank Info', {
            'fields': ('foodbank', 'subscription')
        }),
        ('Payment Details', {
            'fields': ('plan_type', 'payment_method', 'amount', 'transaction_reference', 'payment_date', 'payment_evidence', 'notes')
        }),
        ('Verification', {
            'fields': ('status', 'verified_by', 'verified_at', 'admin_notes', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('foodbank', 'subscription', 'verified_by')
    
@staff_member_required
def admin_deletion_requests(request):
    requests = AccountDeletionRequest.objects.all().select_related('user')
    return render(request, 'admin/custom/deletion_requests.html', {
        'requests': requests,
        'title': 'Account Deletion Requests'
    })    

@staff_member_required
def export_report_pdf(request, report_type):
    from .models import CustomUser, Donation, FoodBankProfile
    import datetime
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    y = 800
    if report_type == 'user_summary':
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "User Summary Report")
        y -= 30
        p.setFont("Helvetica", 12)
        users = CustomUser.objects.all().order_by('-date_joined')[:50]
        p.drawString(100, y, f"Total Users: {users.count()}")
        y -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, y, "Email")
        p.drawString(200, y, "Type")
        p.drawString(260, y, "Phone")
        p.drawString(340, y, "Registered")
        y -= 15
        p.setFont("Helvetica", 10)
        for user in users:
            if y < 50:
                p.showPage()
                y = 800
            p.drawString(60, y, user.email)
            p.drawString(200, y, user.user_type)
            p.drawString(260, y, user.phone_number or "-")
            p.drawString(340, y, user.date_joined.strftime('%Y-%m-%d'))
            y -= 15
    elif report_type == 'donations_summary':
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Donations Summary Report")
        y -= 30
        p.setFont("Helvetica", 12)
        donations = Donation.objects.select_related('donor', 'foodbank').order_by('-donated_at')[:50]
        p.drawString(100, y, f"Total Donations: {donations.count()}")
        y -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, y, "Donor")
        p.drawString(180, y, "Foodbank")
        p.drawString(300, y, "Type")
        p.drawString(350, y, "Amount")
        p.drawString(420, y, "Date")
        y -= 15
        p.setFont("Helvetica", 10)
        for d in donations:
            if y < 50:
                p.showPage()
                y = 800
            donor = getattr(d.donor, 'email', '-')
            foodbank = getattr(d.foodbank, 'foodbank_name', '-')
            dtype = d.donation_type
            amount = str(d.amount or d.subsidized_price or '-')
            date = d.donated_at.strftime('%Y-%m-%d')
            p.drawString(60, y, donor)
            p.drawString(180, y, foodbank)
            p.drawString(300, y, dtype)
            p.drawString(350, y, amount)
            p.drawString(420, y, date)
            y -= 15
    elif report_type == 'top_donors':
        from django.db.models import Sum, Count, Max
        from .models import DonorProfile
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Top Donors Report")
        y -= 30
        p.setFont("Helvetica", 12)
        donors = (
            DonorProfile.objects.select_related('user')
            .annotate(
                total_donations=Count('user__donation'),
                total_amount=Sum('user__donation__amount'),
                last_donation=Max('user__donation__donated_at')
            )
            .order_by('-total_amount')[:50]
        )
        p.drawString(100, y, f"Top {donors.count()} Donors")
        y -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, y, "Donor Name")
        p.drawString(180, y, "Email")
        p.drawString(320, y, "Total Donations")
        p.drawString(400, y, "Total Amount")
        p.drawString(480, y, "Last Donation")
        y -= 15
        p.setFont("Helvetica", 10)
        for donor in donors:
            if y < 50:
                p.showPage()
                y = 800
            name = donor.full_name
            email = donor.user.email
            total_don = str(donor.total_donations or 0)
            total_amt = str(donor.total_amount or 0)
            last_don = donor.last_donation.strftime('%Y-%m-%d') if donor.last_donation else '-'
            p.drawString(60, y, name)
            p.drawString(180, y, email)
            p.drawString(320, y, total_don)
            p.drawString(400, y, total_amt)
            p.drawString(480, y, last_don)
            y -= 15
    elif report_type == 'top_foodbanks':
        from django.db.models import Sum, Count, Max
        from .models import FoodBankProfile, Donation
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Top Foodbanks Report")
        y -= 30
        p.setFont("Helvetica", 12)
        foodbanks = (
            FoodBankProfile.objects.annotate(
                total_donations=Count('donation'),
                total_amount=Sum('donation__amount'),
                last_donation=Max('donation__donated_at')
            )
            .order_by('-total_amount')[:50]
        )
        p.drawString(100, y, f"Top {foodbanks.count()} Foodbanks")
        y -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, y, "Foodbank Name")
        p.drawString(200, y, "Contact Person")
        p.drawString(320, y, "Total Donations")
        p.drawString(420, y, "Total Amount")
        p.drawString(500, y, "Last Donation")
        y -= 15
        p.setFont("Helvetica", 10)
        for fb in foodbanks:
            if y < 50:
                p.showPage()
                y = 800
            name = fb.foodbank_name
            contact = fb.contact_person
            total_don = str(fb.total_donations or 0)
            total_amt = str(fb.total_amount or 0)
            last_don = fb.last_donation.strftime('%Y-%m-%d') if fb.last_donation else '-'
            p.drawString(60, y, name)
            p.drawString(200, y, contact)
            p.drawString(320, y, total_don)
            p.drawString(420, y, total_amt)
            p.drawString(500, y, last_don)
            y -= 15
    elif report_type == 'monthly_registration':
        from .models import CustomUser
        import calendar
        from django.utils import timezone
        now = timezone.now()
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Monthly Registration Report (Last 12 Months)")
        y -= 30
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, y, "Month")
        p.drawString(160, y, "Donors")
        p.drawString(240, y, "Foodbanks")
        p.drawString(340, y, "Recipients")
        p.drawString(440, y, "Total Users")
        y -= 15
        p.setFont("Helvetica", 10)
        for i in reversed(range(12)):
            start = (now.replace(day=1) - timezone.timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_month = start.month + 1 if start.month < 12 else 1
            end_year = start.year if start.month < 12 else start.year + 1
            end = start.replace(month=end_month, year=end_year) if end_month != 1 else start.replace(year=end_year, month=1)
            month_label = start.strftime('%b %Y')
            donors = CustomUser.objects.filter(user_type='DONOR', date_joined__gte=start, date_joined__lt=end).count()
            foodbanks = CustomUser.objects.filter(user_type='FOODBANK', date_joined__gte=start, date_joined__lt=end).count()
            recipients = CustomUser.objects.filter(user_type='RECIPIENT', date_joined__gte=start, date_joined__lt=end).count()
            total = donors + foodbanks + recipients
            if y < 50:
                p.showPage()
                y = 800
            p.drawString(60, y, month_label)
            p.drawString(160, y, str(donors))
            p.drawString(240, y, str(foodbanks))
            p.drawString(340, y, str(recipients))
            p.drawString(440, y, str(total))
            y -= 15
    elif report_type == 'donation_trends':
        from .models import Donation
        from django.utils import timezone
        now = timezone.now()
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Donation Trends Report (Last 12 Months)")
        y -= 30
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, y, "Month")
        p.drawString(140, y, "Total Donations")
        p.drawString(240, y, "Item")
        p.drawString(300, y, "Money")
        p.drawString(360, y, "Subsidized")
        p.drawString(440, y, "Total Amount")
        y -= 15
        p.setFont("Helvetica", 10)
        for i in reversed(range(12)):
            start = (now.replace(day=1) - timezone.timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_month = start.month + 1 if start.month < 12 else 1
            end_year = start.year if start.month < 12 else start.year + 1
            end = start.replace(month=end_month, year=end_year) if end_month != 1 else start.replace(year=end_year, month=1)
            month_label = start.strftime('%b %Y')
            qs = Donation.objects.filter(donated_at__gte=start, donated_at__lt=end)
            total = qs.count()
            item = qs.filter(donation_type='item').count()
            money = qs.filter(donation_type='money').count()
            subsidized = qs.filter(donation_type='subsidized').count()
            total_amount = qs.aggregate(total=Sum('amount'))['total'] or 0
            if y < 50:
                p.showPage()
                y = 800
            p.drawString(60, y, month_label)
            p.drawString(140, y, str(total))
            p.drawString(240, y, str(item))
            p.drawString(300, y, str(money))
            p.drawString(360, y, str(subsidized))
            p.drawString(440, y, str(total_amount))
            y -= 15
    elif report_type == 'active_inactive_users':
        from .models import CustomUser
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Active vs. Inactive Users Report")
        y -= 30
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, y, "Email")
        p.drawString(180, y, "Full Name")
        p.drawString(320, y, "User Type")
        p.drawString(400, y, "Is Active")
        p.drawString(470, y, "Last Login")
        p.drawString(550, y, "Registered")
        y -= 15
        p.setFont("Helvetica", 10)
        users = CustomUser.objects.all().order_by('-date_joined')[:50]
        for user in users:
            if y < 50:
                p.showPage()
                y = 800
            email = user.email
            # Get full name from profile if available
            if user.user_type == 'DONOR' and hasattr(user, 'donor_profile'):
                full_name = user.donor_profile.full_name
            elif user.user_type == 'FOODBANK' and hasattr(user, 'foodbank_profile'):
                full_name = user.foodbank_profile.foodbank_name
            elif user.user_type == 'RECIPIENT' and hasattr(user, 'recipient_profile'):
                full_name = user.recipient_profile.full_name
            else:
                full_name = ''
            user_type = user.user_type
            is_active = 'Yes' if user.is_active else 'No'
            last_login = user.last_login.strftime('%Y-%m-%d') if user.last_login else '-'
            registered = user.date_joined.strftime('%Y-%m-%d')
            p.drawString(40, y, email)
            p.drawString(180, y, full_name)
            p.drawString(320, y, user_type)
            p.drawString(400, y, is_active)
            p.drawString(470, y, last_login)
            p.drawString(550, y, registered)
            y -= 15
    elif report_type == 'pending_deliveries':
        from .models import Donation
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Pending Deliveries Report")
        y -= 30
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, y, "Donation ID")
        p.drawString(110, y, "Donor Name")
        p.drawString(220, y, "Foodbank Name")
        p.drawString(340, y, "Item/Amount")
        p.drawString(420, y, "Delivery Method")
        p.drawString(500, y, "Status")
        p.drawString(560, y, "Pickup/Dropoff Time")
        y -= 15
        p.setFont("Helvetica", 10)
        deliveries = Donation.objects.filter(delivery_status__in=["pending", "scheduled", "in_transit"]).order_by('-donated_at')[:50]
        for d in deliveries:
            if y < 50:
                p.showPage()
                y = 800
            donor_name = getattr(d.donor.donor_profile, 'full_name', d.donor.email) if hasattr(d.donor, 'donor_profile') else d.donor.email
            foodbank_name = d.foodbank.foodbank_name
            item_amt = d.item_name or str(d.amount or d.subsidized_price or '-')
            p.drawString(40, y, str(d.id))
            p.drawString(110, y, donor_name)
            p.drawString(220, y, foodbank_name)
            p.drawString(340, y, item_amt)
            p.drawString(420, y, d.delivery_method or '-')
            p.drawString(500, y, d.delivery_status)
            p.drawString(560, y, d.pickup_time.strftime('%Y-%m-%d %H:%M') if d.pickup_time else '-')
            y -= 15
    elif report_type == 'recipient_impact':
        from .models import RecipientProfile, Donation
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Recipient Impact Report")
        y -= 30
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, y, "Recipient Name")
        p.drawString(180, y, "Email")
        p.drawString(320, y, "Location")
        p.drawString(420, y, "Donations Received")
        p.drawString(520, y, "Last Donation")
        y -= 15
        p.setFont("Helvetica", 10)
        recipients = RecipientProfile.objects.select_related('user').all()[:50]
        for r in recipients:
            if y < 50:
                p.showPage()
                y = 800
            email = r.user.email
            name = r.full_name
            location = r.location
            donations = Donation.objects.filter(foodbank__user=r.user).count()
            last_donation = Donation.objects.filter(foodbank__user=r.user).order_by('-donated_at').first()
            last_don = last_donation.donated_at.strftime('%Y-%m-%d') if last_donation else '-'
            p.drawString(40, y, name)
            p.drawString(180, y, email)
            p.drawString(320, y, location)
            p.drawString(420, y, str(donations))
            p.drawString(520, y, last_don)
            y -= 15
    elif report_type == 'urgent_requests':
        from .models import Notification
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, y, "Urgent Requests Report")
        y -= 30
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, y, "Foodbank/User")
        p.drawString(200, y, "Request Description")
        p.drawString(420, y, "Date Created")
        p.drawString(520, y, "Status")
        y -= 15
        p.setFont("Helvetica", 10)
        requests = Notification.objects.filter(notification_type='request').order_by('-created_at')[:50]
        for req in requests:
            if y < 50:
                p.showPage()
                y = 800
            user = req.user.email
            desc = req.message[:60]
            date = req.created_at.strftime('%Y-%m-%d %H:%M')
            status = 'Unread' if not req.is_read else 'Read'
            p.drawString(40, y, user)
            p.drawString(200, y, desc)
            p.drawString(420, y, date)
            p.drawString(520, y, status)
            y -= 15
    else:
        p.drawString(100, y, f"Unknown report type: {report_type}")
    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}.pdf"'
    return response

# Add a URL pattern for the custom dashboard
custom_admin_urls = [
    path('dashboard/', custom_admin_dashboard, name='custom_admin_dashboard'),
]

# Patch admin site to include our custom URLs
from django.contrib import admin
original_get_urls = admin.site.get_urls
admin.site.get_urls = lambda: custom_admin_urls + original_get_urls()

custom_admin_urls += [
    path('dashboard/export_report/<str:report_type>/', export_report_pdf, name='export_report_pdf'),
]
