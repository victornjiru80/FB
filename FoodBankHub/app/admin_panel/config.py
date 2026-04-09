"""
Configuration settings for the Custom Admin Dashboard
"""

# Dashboard Settings
DASHBOARD_TITLE = "FoodBankHub Admin"
DASHBOARD_SUBTITLE = "Admin Panel"
ITEMS_PER_PAGE = 25
CHART_MONTHS = 12

# Color Scheme
COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#11998e',
    'warning': '#f093fb',
    'info': '#4facfe',
    'danger': '#f5576c',
}

# Chart Colors
CHART_COLORS = [
    'rgba(102, 126, 234, 0.8)',
    'rgba(17, 153, 142, 0.8)', 
    'rgba(245, 87, 108, 0.8)',
    'rgba(79, 172, 254, 0.8)',
    'rgba(240, 147, 251, 0.8)',
]

# Navigation Menu Items
NAVIGATION_ITEMS = [
    {
        'name': 'Dashboard',
        'url': 'custom_admin:dashboard',
        'icon': 'fas fa-home',
        'active_patterns': ['dashboard']
    },
    {
        'name': 'User Management',
        'url': 'custom_admin:user_management',
        'icon': 'fas fa-users',
        'active_patterns': ['user_management', 'user_detail']
    },
    {
        'name': 'Donations',
        'url': 'custom_admin:donation_management',
        'icon': 'fas fa-hand-holding-heart',
        'active_patterns': ['donation_management']
    },
    {
        'name': 'Food Bank Requests',
        'url': 'custom_admin:foodbank_requests',
        'icon': 'fas fa-clipboard-list',
        'active_patterns': ['foodbank_requests']
    },
]

# Report Types
REPORT_TYPES = [
    {
        'key': 'user_summary',
        'name': 'User Summary',
        'description': 'Complete user listing with details',
        'icon': 'fas fa-users'
    },
    {
        'key': 'donations_summary',
        'name': 'Donations Summary',
        'description': 'All donations with donor and food bank info',
        'icon': 'fas fa-hand-holding-heart'
    },
    {
        'key': 'top_donors',
        'name': 'Top Donors',
        'description': 'Most active donors by contribution',
        'icon': 'fas fa-trophy'
    },
    {
        'key': 'top_foodbanks',
        'name': 'Top Food Banks',
        'description': 'Most active food banks by donations received',
        'icon': 'fas fa-warehouse'
    },
    {
        'key': 'monthly_registration',
        'name': 'Monthly Registrations',
        'description': 'User registration trends over time',
        'icon': 'fas fa-chart-line'
    },
    {
        'key': 'donation_trends',
        'name': 'Donation Trends',
        'description': 'Donation patterns and amounts over time',
        'icon': 'fas fa-chart-bar'
    },
]

# Bulk Actions Configuration
BULK_ACTIONS = {
    'users': [
        {'key': 'activate', 'name': 'Activate Users', 'class': 'btn-success'},
        {'key': 'deactivate', 'name': 'Deactivate Users', 'class': 'btn-warning'},
    ],
    'donations': [
        {'key': 'mark_delivered', 'name': 'Mark as Delivered', 'class': 'btn-success'},
    ],
}

# Status Badge Colors
STATUS_COLORS = {
    'active': 'bg-success',
    'inactive': 'bg-danger',
    'pending': 'bg-warning',
    'delivered': 'bg-success',
    'cancelled': 'bg-secondary',
    'urgent': 'bg-danger',
    'high': 'bg-warning',
    'medium': 'bg-primary',
    'low': 'bg-secondary',
    'fulfilled': 'bg-info',
    'expired': 'bg-secondary',
}

# Dashboard KPI Cards Configuration
KPI_CARDS = [
    {
        'title': 'Total Users',
        'key': 'total_users',
        'icon': 'fas fa-users',
        'color': 'stats-card',
        'description': 'All registered users'
    },
    {
        'title': 'Total Donations',
        'key': 'total_donations',
        'icon': 'fas fa-hand-holding-heart',
        'color': 'stats-card success',
        'description': 'All donations made'
    },
    {
        'title': 'Food Banks',
        'key': 'total_foodbanks',
        'icon': 'fas fa-warehouse',
        'color': 'stats-card warning',
        'description': 'Registered food banks'
    },
    {
        'title': 'Total Amount',
        'key': 'total_donated_amount',
        'icon': 'fas fa-dollar-sign',
        'color': 'stats-card info',
        'description': 'Total donated amount',
        'format': 'currency'
    },
]

# Export Settings
EXPORT_SETTINGS = {
    'max_records': 1000,
    'date_format': '%Y-%m-%d',
    'datetime_format': '%Y-%m-%d %H:%M',
    'currency_symbol': 'KES',
}

# Search Configuration
SEARCH_FIELDS = {
    'users': ['email', 'phone_number'],
    'donations': ['donor__email', 'foodbank__foodbank_name', 'item_name'],
    'requests': ['title', 'description', 'foodbank__foodbank_name'],
}

# Pagination Settings
PAGINATION_SETTINGS = {
    'items_per_page': ITEMS_PER_PAGE,
    'max_page_links': 5,
    'show_first_last': True,
}

# Chart Configuration
CHART_CONFIG = {
    'responsive': True,
    'maintainAspectRatio': False,
    'plugins': {
        'legend': {
            'position': 'bottom'
        }
    },
    'scales': {
        'y': {
            'beginAtZero': True
        }
    }
}
