import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')

try:
    import Fusion.settings.development as dev_settings
    if 'allauth.account.middleware.AccountMiddleware' not in dev_settings.MIDDLEWARE:
        dev_settings.MIDDLEWARE.append('allauth.account.middleware.AccountMiddleware')
    
    import Fusion.settings.common as common_settings
    if 'allauth.account.middleware.AccountMiddleware' not in common_settings.MIDDLEWARE:
        common_settings.MIDDLEWARE.append('allauth.account.middleware.AccountMiddleware')
except ImportError:
    pass

import django
django.setup()
from django.db import connection
from django.core.management import call_command

print("Resetting 'hr2' database tables and migrations to perfectly match new models...")

with connection.cursor() as cursor:
    cursor.execute("DELETE FROM django_migrations WHERE app = 'hr2'")
    
    # Dynamically find and drop ALL tables belonging to the hr2 module
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'hr2_%'")
    hr2_tables = cursor.fetchall()
    
    for table in hr2_tables:
        table_name = table[0]
        print(f"Dropping table {table_name}...")
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        
# Fix path: __file__ is in FusionIIIT
migrations_dir = os.path.join(os.path.dirname(__file__), 'applications', 'hr2', 'migrations')
print(f"Clearing old migrations in {migrations_dir}...")
if os.path.exists(migrations_dir):
    for filename in os.listdir(migrations_dir):
        if filename != '__init__.py' and filename.endswith('.py'):
            os.remove(os.path.join(migrations_dir, filename))

print("Generating new migrations based strictly on current models.py...")
call_command('makemigrations', 'hr2')
print("Applying new migrations to recreate tables...")
call_command('migrate', 'hr2')

print("Database schema successfully synced and follows the new models perfectly!")

print("Inserting test data for all forms...")
from django.contrib.auth.models import User
from applications.globals.models import ExtraInfo, Designation, HoldsDesignation
from applications.filetracking.models import File, Tracking
from applications.hr2.models import (
    LeaveForm, LTCform, CPDAAdvanceform, 
    CPDAReimbursementform, Appraisalform
)
from applications.hr2.constants.form_types import FormType

def populate_test_data():
    professors = HoldsDesignation.objects.filter(designation__name__icontains='professor').select_related('user', 'designation')
    
    if not professors.exists():
        print("No users found with Professor designation.")
        return

    File.objects.filter(src_module='HR').delete()

    for hold_desig in professors:
        user = hold_desig.user
        designation = hold_desig.designation
        
        extrainfo, _ = ExtraInfo.objects.get_or_create(
            user=user, 
            defaults={'id': str(user.id), 'user_type': 'faculty'}
        )
        
        def create_workflow(form_instance, form_type_str, state):
            file_obj = File.objects.create(
                uploader=extrainfo,
                designation=designation,
                subject=f'{form_type_str} {state}',
                description='Test auto-generated',
                is_read=(state == 'archive'),
                src_module='HR',
                src_object_id=str(form_instance.id),
                file_extra_JSON={"type": form_type_str}
            )
            
            if state == 'inbox':
                Tracking.objects.create(
                    file_id=file_obj,
                    current_id=extrainfo,
                    current_design=hold_desig,
                    receiver_id=user,
                    receive_design=designation,
                    remarks='Inbox Test',
                    is_read=False
                )
            elif state == 'outbox':
                Tracking.objects.create(
                    file_id=file_obj,
                    current_id=extrainfo,
                    current_design=hold_desig,
                    receiver_id=User.objects.first(),
                    receive_design=Designation.objects.first(),
                    remarks='Outbox Test',
                    is_read=False
                )
            elif state == 'archive':
                Tracking.objects.create(
                    file_id=file_obj,
                    current_id=extrainfo,
                    current_design=hold_desig,
                    receiver_id=user,
                    receive_design=designation,
                    remarks='Archive Test',
                    is_read=True
                )

        # CPDA Advance
        for state in ['inbox', 'outbox', 'archive']:
            f = CPDAAdvanceform.objects.create(
                employeeId=user.id, name=user.username, designation=designation.name,
                purpose=f'Test {state.capitalize()}', amountRequired=10000
            )
            create_workflow(f, FormType.CPDA_ADVANCE, state)
            
        # Leave
        for state in ['inbox', 'outbox', 'archive']:
            f = LeaveForm.objects.create(
                employeeId=user.id, name=user.username, designation=designation.name,
                departmentInfo='CSE', natureOfLeave='Casual',
                purposeOfLeave=f'Test {state.capitalize()}'
            )
            create_workflow(f, FormType.LEAVE, state)
            
        # LTC
        for state in ['inbox', 'outbox', 'archive']:
            f = LTCform.objects.create(
                employeeId=user.id, name=user.username, designation=designation.name,
                blockYear='2026', departmentInfo='CSE',
                phoneNumberForContact=1234567890
            )
            create_workflow(f, FormType.LTC, state)
            
        # CPDA Claim
        for state in ['inbox', 'outbox', 'archive']:
            f = CPDAReimbursementform.objects.create(
                employeeId=user.id, name=user.username, designation=designation.name,
                advanceTaken=0, purpose=f'Test Claim {state.capitalize()}'
            )
            create_workflow(f, FormType.CPDA_REIMBURSEMENT, state)
            
        # Appraisal
        for state in ['inbox', 'outbox', 'archive']:
            f = Appraisalform.objects.create(
                employeeId=user.id, name=user.username, designation=designation.name,
                disciplineInfo='CSE', specificFieldOfKnowledge='AI'
            )
            create_workflow(f, FormType.APPRAISAL, state)

    print("Successfully populated perfectly synced test data for all forms.")

if __name__ == '__main__':
    populate_test_data()
