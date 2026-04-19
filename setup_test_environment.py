#!/usr/bin/env python3
"""
Test Environment Setup Script
Creates test users, assigns designations, and configures leave parameters
Run: python manage.py shell < setup_test_environment.py
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.production')
django.setup()

from django.contrib.auth.models import User
from FusionIIIT.applications.globals.models import HoldsDesignation, Designation, ExtraInfo
from datetime import datetime, date

print("=" * 70)
print("HR MODULE TEST ENVIRONMENT SETUP")
print("=" * 70)

# ============================================================================
# STEP 1: CREATE TEST USERS
# ============================================================================
print("\n[STEP 1] Creating test users...")

test_users = {
    'employee1': ('password123', 'Employee 1'),
    'employee2': ('password123', 'Employee 2'),
    'manager1': ('password123', 'Manager 1'),
    'hradmin1': ('password123', 'HR Admin 1'),
    'hod1': ('password123', 'HOD 1'),
    'sanctioning_auth': ('password123', 'Sanctioning Authority'),
    'accountant1': ('password123', 'Accountant 1'),
}

created_users = {}

for username, (password, full_name) in test_users.items():
    try:
        user = User.objects.get(username=username)
        print(f"  ✓ {username} already exists")
        created_users[username] = user
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=full_name.split()[0] if full_name else username,
            last_name=full_name.split()[1] if len(full_name.split()) > 1 else ''
        )
        created_users[username] = user
        print(f"  ✓ Created {username}")

# ============================================================================
# STEP 2: CREATE/ASSIGN DESIGNATIONS
# ============================================================================
print("\n[STEP 2] Creating and assigning designations...")

designations_map = {
    'employee1': 'Faculty',  # Faculty for VL testing
    'employee2': 'Faculty',
    'manager1': 'Manager',
    'hradmin1': 'HR Admin',
    'hod1': 'Department Head',
    'sanctioning_auth': 'Sanctioning Authority',
    'accountant1': 'Accountant',
}

for username, designation_name in designations_map.items():
    user = created_users[username]
    
    try:
        designation = Designation.objects.get(name=designation_name)
    except Designation.DoesNotExist:
        designation = Designation.objects.create(name=designation_name)
        print(f"  ✓ Created designation: {designation_name}")
    
    try:
        holds_designation = HoldsDesignation.objects.get(user=user, designation=designation)
        print(f"  ✓ {username} already has {designation_name}")
    except HoldsDesignation.DoesNotExist:
        holds_designation = HoldsDesignation.objects.create(
            user=user,
            designation=designation,
            start_date=date.today()
        )
        print(f"  ✓ Assigned {designation_name} to {username}")

# ============================================================================
# STEP 3: CREATE EXTRA INFO (for leave tracking)
# ============================================================================
print("\n[STEP 3] Creating ExtraInfo records...")

for username in test_users.keys():
    user = created_users[username]
    
    try:
        extra_info = ExtraInfo.objects.get(user=user)
        print(f"  ✓ {username} already has ExtraInfo")
    except ExtraInfo.DoesNotExist:
        extra_info = ExtraInfo.objects.create(
            user=user,
            aadhaar='12345678901234',
            pan='ABCDE1234F',
            bank_account='9876543210123456'
        )
        print(f"  ✓ Created ExtraInfo for {username}")

# ============================================================================
# STEP 4: CONFIGURE LEAVE PARAMETERS
# ============================================================================
print("\n[STEP 4] Configuring leave parameters...")

try:
    from FusionIIIT.applications.hr2.models import LeavePolicy
    
    leave_policy, created = LeavePolicy.objects.get_or_create(
        defaults={
            'cl_entitlement': 12,
            'sl_entitlement': 10,
            'vl_entitlement': 20,  # Faculty only
            'hr_entitlement': 5,
            'scl_entitlement': 3,
            'is_published': True,
            'version': 1,
        }
    )
    
    if created:
        print(f"  ✓ Created LeavePolicy: CL=12, SL=10, VL=20, HR=5, SCL=3")
    else:
        print(f"  ✓ LeavePolicy exists (CL={leave_policy.cl_entitlement})")
        
except Exception as e:
    print(f"  ⚠ Could not set LeavePolicy: {e}")

# ============================================================================
# STEP 5: CONFIGURE HOLIDAY CALENDAR
# ============================================================================
print("\n[STEP 5] Configuring holiday calendar...")

try:
    from FusionIIIT.applications.hr2.models import Holiday
    
    holidays = [
        ('2026-05-01', 'Labour Day', 'RH'),
        ('2026-06-15', 'Founder Day', 'RH'),
        ('2026-12-25', 'Christmas', 'RH'),
    ]
    
    for date_str, name, holiday_type in holidays:
        try:
            holiday = Holiday.objects.get(date=date_str)
            print(f"  ✓ Holiday {name} already exists")
        except Holiday.DoesNotExist:
            holiday = Holiday.objects.create(
                date=date_str,
                name=name,
                holiday_type=holiday_type,
                is_published=True
            )
            print(f"  ✓ Created holiday: {name} ({date_str})")
            
except Exception as e:
    print(f"  ⚠ Could not set holidays: {e}")

# ============================================================================
# STEP 6: CREATE LEAVE BALANCES FOR TEST USERS
# ============================================================================
print("\n[STEP 6] Initializing leave balances...")

try:
    from FusionIIIT.applications.hr2.models import LeaveBalance
    
    for username in ['employee1', 'employee2']:
        user = created_users[username]
        
        balance, created = LeaveBalance.objects.get_or_create(
            user=user,
            defaults={
                'cl_balance': 12,
                'sl_balance': 10,
                'vl_balance': 20,  # Faculty
                'hr_balance': 5,
                'scl_balance': 3,
            }
        )
        
        if created:
            print(f"  ✓ Initialized leave balance for {username}")
        else:
            print(f"  ✓ Leave balance exists for {username}")
            
except Exception as e:
    print(f"  ⚠ Could not set leave balances: {e}")

print("\n" + "=" * 70)
print("✅ TEST ENVIRONMENT SETUP COMPLETE!")
print("=" * 70)
print("\nTest Users Created:")
for username in test_users.keys():
    print(f"  • {username} (password: password123)")

print("\nDesignations Assigned:")
for username, designation in designations_map.items():
    print(f"  • {username}: {designation}")

print("\nTest Environment Ready for Manual UI Testing!")
print("Start with: http://localhost:5173 (Frontend)")
print("=" * 70)
