"""Base test configuration for HR2 module.

Provides BaseHR2TestCase with shared users (employee, hr_admin, hod, director,
accountant), designations, ExtraInfo, and helper methods used across all test
classes.
"""

import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from applications.globals.models import (
    Designation,
    ExtraInfo,
    HoldsDesignation,
)

User = get_user_model()


class BaseHR2TestCase(TestCase):
    """Shared fixture for HR2 tests.

    Creates a minimal but complete set of users and designations that mirrors
    the production setup expected by the workflow resolvers (resolve_hod_for_applicant,
    resolve_director, resolve_accountant, resolve_hr_admin).
    """

    @classmethod
    def setUpTestData(cls):
        # ── Users ──────────────────────────────────────────────────────────────
        cls.employee_user = User.objects.create_user(
            username="emp_test",
            password="test@1234",
            first_name="Test",
            last_name="Employee",
        )
        cls.hr_admin_user = User.objects.create_user(
            username="hr_admin",
            password="test@1234",
            first_name="HR",
            last_name="Admin",
        )
        cls.hod_user = User.objects.create_user(
            username="hod_cse",
            password="test@1234",
            first_name="HOD",
            last_name="CSE",
        )
        cls.director_user = User.objects.create_user(
            username="director",
            password="test@1234",
            first_name="Director",
            last_name="IIIT",
        )
        cls.accountant_user = User.objects.create_user(
            username="accountant",
            password="test@1234",
            first_name="Accountant",
            last_name="Staff",
        )

        # ── Department (needed for HOD resolution) ─────────────────────────────
        from applications.globals.models import DepartmentInfo
        cls.department, _ = DepartmentInfo.objects.get_or_create(name="CSE")

        # ── ExtraInfo ──────────────────────────────────────────────────────────
        cls.emp_extra = ExtraInfo.objects.create(
            user=cls.employee_user,
            id="EMP001",
            user_type="faculty",
            department=cls.department,
        )
        cls.hr_admin_extra = ExtraInfo.objects.create(
            user=cls.hr_admin_user,
            id="HR001",
            user_type="staff",
        )
        cls.hod_extra = ExtraInfo.objects.create(
            user=cls.hod_user,
            id="HOD001",
            user_type="faculty",
            department=cls.department,
        )
        cls.director_extra = ExtraInfo.objects.create(
            user=cls.director_user,
            id="DIR001",
            user_type="staff",
        )
        cls.accountant_extra = ExtraInfo.objects.create(
            user=cls.accountant_user,
            id="ACC001",
            user_type="staff",
        )

        # ── Designations ───────────────────────────────────────────────────────
        cls.desig_employee, _ = Designation.objects.get_or_create(name="Faculty")
        cls.desig_hr_admin, _ = Designation.objects.get_or_create(name="HR Admin")
        cls.desig_hod, _ = Designation.objects.get_or_create(name="HOD (CSE)")
        cls.desig_director, _ = Designation.objects.get_or_create(name="Director")
        cls.desig_accountant, _ = Designation.objects.get_or_create(name="Accountant")

        # ── HoldsDesignation ───────────────────────────────────────────────────
        HoldsDesignation.objects.get_or_create(
            user=cls.employee_user,
            working=cls.employee_user,
            designation=cls.desig_employee,
        )
        HoldsDesignation.objects.get_or_create(
            user=cls.hr_admin_user,
            working=cls.hr_admin_user,
            designation=cls.desig_hr_admin,
        )
        HoldsDesignation.objects.get_or_create(
            user=cls.hod_user,
            working=cls.hod_user,
            designation=cls.desig_hod,
        )
        HoldsDesignation.objects.get_or_create(
            user=cls.director_user,
            working=cls.director_user,
            designation=cls.desig_director,
        )
        HoldsDesignation.objects.get_or_create(
            user=cls.accountant_user,
            working=cls.accountant_user,
            designation=cls.desig_accountant,
        )

    def setUp(self):
        self.client = APIClient()

        # ── Report metadata (filled per test) ─────────────────────────────────
        self._test_id = ""
        self._uc_id = ""
        self._br_id = ""
        self._wf_id = ""
        self._test_category = ""
        self._scenario = ""
        self._preconditions = ""
        self._input_action = ""
        self._expected_result = ""
        self._actual_result = ""
        self._status = "Not Run"
        self._evidence = ""
        self._steps = []

    # ── Auth helpers ──────────────────────────────────────────────────────────

    def login_as_employee(self):
        self.client.force_authenticate(user=self.employee_user)

    def login_as_hr_admin(self):
        self.client.force_authenticate(user=self.hr_admin_user)

    def login_as_hod(self):
        self.client.force_authenticate(user=self.hod_user)

    def login_as_director(self):
        self.client.force_authenticate(user=self.director_user)

    def login_as_accountant(self):
        self.client.force_authenticate(user=self.accountant_user)

    def logout(self):
        self.client.force_authenticate(user=None)

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    def api_get(self, url, params=None, expected_status=200):
        response = self.client.get(url, params or {})
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"GET {url} → expected {expected_status}, got {response.status_code}")
        return response

    def api_post(self, url, data=None, expected_status=None, format="json"):
        response = self.client.post(url, data or {}, format=format)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"POST {url} → expected {expected_status}, got {response.status_code}")
        return response

    def api_put(self, url, data=None, expected_status=None, format="json"):
        response = self.client.put(url, data or {}, format=format)
        if expected_status is not None:
            self.assertEqual(response.status_code, expected_status,
                             f"PUT {url} → expected {expected_status}, got {response.status_code}")
        return response

    # ── Date helpers ──────────────────────────────────────────────────────────

    def future_date(self, days=5):
        return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()

    def past_date(self, days=3):
        return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()

    def today(self):
        return datetime.date.today().isoformat()

    # ── Assertion helpers ─────────────────────────────────────────────────────

    def assert_object_exists(self, model_class, **kwargs):
        self.assertTrue(
            model_class.objects.filter(**kwargs).exists(),
            f"Expected {model_class.__name__} with {kwargs} to exist in DB.",
        )

    # ── Report helpers ────────────────────────────────────────────────────────

    def _record_result(self, actual_result, status, evidence=""):
        self._actual_result = actual_result
        self._status = status
        self._evidence = evidence

    def _add_step(self, step_num, action, expected, actual, passed):
        self._steps.append({
            "step": step_num,
            "action": action,
            "expected": expected,
            "actual": actual,
            "passed": passed,
        })

    def _all_steps_passed(self):
        return all(s["passed"] for s in self._steps)


# ── Specialised base classes (thin wrappers for naming clarity in reports) ────

class UCTestBase(BaseHR2TestCase):
    """Base for Use Case tests."""
    pass


class BRTestBase(BaseHR2TestCase):
    """Base for Business Rule tests."""
    pass


class WFTestBase(BaseHR2TestCase):
    """Base for Workflow tests."""
    pass
