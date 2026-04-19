# Database Optimization Migration for Student List Generation

from django.db import migrations

class Migration(migrations.Migration):
    """
    Add database indexes to optimize student list generation queries
    """
    
    dependencies = [
        ('programme_curriculum', '0025_update_minority_values'),
    ]

    operations = [
        # NOTE: Removed - course_registration table does not exist in this version
        # This migration was attempting to create indexes on a non-existent model
    ]
