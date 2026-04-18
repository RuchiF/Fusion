import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Fusion.settings.development')
import Fusion.settings.development as d
d.MIDDLEWARE.append('allauth.account.middleware.AccountMiddleware')
import Fusion.settings.common as c
c.MIDDLEWARE.append('allauth.account.middleware.AccountMiddleware')
django.setup()
from django.contrib.auth.models import User
from applications.hr2.models import EmpConfidentialDetails
from applications.globals.models import ExtraInfo

users = User.objects.filter(username__in=['faculty1', 'faculty2'])
print(f'Found {users.count()} users.')
for u in users:
    ext = ExtraInfo.objects.filter(user=u).first()
    if ext:
        EmpConfidentialDetails.objects.update_or_create(
            extra_info=ext, 
            defaults={'aadhar_no': 123456789012, 'bank_account_no': 1234567890}
        )
        print('Updated details for', u.username)
