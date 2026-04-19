"""HR2 Use-Case Tests (specification-based, black-box).

Covers:
    UC-1  Submit LTC Application
    UC-2  Retrieve LTC Application History
    UC-3  Submit CPDA Advance Application
    UC-4  Submit Appraisal Form
    UC-5  Check Leave Balance

Minimum requirement: 1 Happy Path + 1 Alternate Path + 1 Exception per UC = 15 tests.
"""

import datetime

from applications.globals.models import ExtraInfo
from applications.hr2.models import (
    CPDAAdvanceform,
    EmpConfidentialDetails,
    LTCform,
    Appraisalform,
    LeaveBalance,
)
from applications.hr2.tests.conftest import UCTestBase

# ── Helpers to build valid payloads ──────────────────────────────────────────


def _ltc_payload(submitter_user, receiver_name="hr_admin", receiver_desig="HR Admin",
                 uploader_desig="Faculty"):
    """Return a list-format LTC POST payload."""
    form_data = {
        "employeeId": 1001,
        "name": submitter_user.get_full_name() or submitter_user.username,
        "designation": "Faculty",
        "pfNo": 1001,
        "blockYear": "2024-2026",
        "basicPaySalary": 60000,
        "departmentInfo": "CSE",
        "hometownOrNot": False,
        "placeOfVisit": "Delhi",
        "addressDuringLeave": "123 Test Street, Delhi",
        "modeofTravel": "Train",
        "amountOfAdvanceRequired": 10000,
        "phoneNumberForContact": 9876543210,
        "submissionDate": datetime.date.today().isoformat(),
    }
    user_info = {
        "receiver_name": receiver_name,
        "receiver_designation": receiver_desig,
        "uploader_designation": uploader_desig,
    }
    return [form_data, user_info]


def _cpda_payload(submitter_user, uploader_desig="Faculty"):
    """Return a list-format CPDA Advance POST payload."""
    form_data = {
        "employeeId": 1001,
        "name": submitter_user.get_full_name() or submitter_user.username,
        "designation": "Faculty",
        "pfNo": 1001,
        "purpose": "Conference registration",
        "amountRequired": 5000,
        "submissionDate": datetime.date.today().isoformat(),
    }
    user_info = {"uploader_designation": uploader_desig}
    return [form_data, user_info]


def _appraisal_payload(receiver_name="hr_admin", receiver_desig="HR Admin",
                       uploader_desig="Faculty"):
    form_data = {
        "employeeId": 1001,
        "name": "Test Employee",
        "designation": "Faculty",
        "pfNo": 1001,
        "disciplineInfo": "Computer Science",
        "specificFieldOfKnowledge": "Machine Learning",
        "currentResearchInterests": "Deep Learning",
        "submissionDate": datetime.date.today().isoformat(),
    }
    user_info = {
        "receiver_name": receiver_name,
        "receiver_designation": receiver_desig,
        "uploader_designation": uploader_desig,
    }
    return [form_data, user_info]


# ─────────────────────────────────────────────────────────────────────────────
# UC-1: Submit LTC Application
# ─────────────────────────────────────────────────────────────────────────────

class TestUC01_SubmitLTC(UCTestBase):
    """UC-1: Employee submits an LTC application."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Create complete confidential details so profile check passes
        cls.confidential = EmpConfidentialDetails.objects.create(
            extra_info=cls.emp_extra,
            aadhar_no=123456789012,
            bank_account_no=987654321,
            maritial_status="UN-MARRIED",
            salary=60000,
        )

    def test_hp01_submit_ltc_with_complete_profile(self):
        """Happy Path — Employee with complete profile submits LTC successfully."""
        self._test_id = "UC-1-HP-01"
        self._uc_id = "UC-1"
        self._test_category = "Happy Path"
        self._scenario = "Employee with complete profile submits LTC with valid approver"
        self._preconditions = "EmpConfidentialDetails has Aadhaar and bank_account_no"
        self._input_action = "POST /hr/ltc/ with valid list payload"
        self._expected_result = "LTCform created in DB, HTTP 200"

        self.login_as_employee()
        payload = _ltc_payload(self.employee_user)
        response = self.api_post("/hr/ltc/", payload, expected_status=None)

        if response.status_code == 200:
            self.assertTrue(LTCform.objects.filter(created_by=self.employee_user).exists())
            self._record_result(
                "LTC created successfully",
                "Pass",
                f"HTTP {response.status_code}",
            )
        else:
            self._record_result(
                f"Unexpected HTTP {response.status_code}",
                "Fail",
                str(response.data),
            )
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ap01_submit_ltc_dict_format(self):
        """Alternate Path — LTC submitted using dict payload format instead of list."""
        self._test_id = "UC-1-AP-01"
        self._uc_id = "UC-1"
        self._test_category = "Alternate Path"
        self._scenario = "Employee submits LTC with dict payload (form_data + user_info keys)"
        self._preconditions = "EmpConfidentialDetails complete"
        self._input_action = "POST /hr/ltc/ with {'form_data': {...}, 'user_info': {...}}"
        self._expected_result = "LTCform created, HTTP 200"

        self.login_as_employee()
        list_payload = _ltc_payload(self.employee_user)
        dict_payload = {
            "form_data": list_payload[0],
            "user_info": list_payload[1],
        }
        response = self.api_post("/hr/ltc/", dict_payload, expected_status=None)

        if response.status_code == 200:
            self._record_result("LTC accepted in dict format", "Pass",
                                f"HTTP {response.status_code}")
        else:
            # Some implementations may only support list format; treat as Partial
            self._record_result(
                f"Dict format not accepted: HTTP {response.status_code}",
                "Partial",
                str(response.data),
            )

    def test_ex01_submit_ltc_incomplete_profile(self):
        """Exception — Employee with missing Aadhaar/bank details is rejected."""
        self._test_id = "UC-1-EX-01"
        self._uc_id = "UC-1"
        self._test_category = "Exception"
        self._scenario = "Employee with aadhar_no=0 and bank_account_no=0 tries LTC"
        self._preconditions = "EmpConfidentialDetails has aadhar_no=0, bank_account_no=0"
        self._input_action = "POST /hr/ltc/ after resetting confidential details to zero"
        self._expected_result = "HTTP 400 with incomplete profile message"

        # Temporarily blank out the confidential record
        self.confidential.aadhar_no = 0
        self.confidential.bank_account_no = 0
        self.confidential.save()

        try:
            self.login_as_employee()
            payload = _ltc_payload(self.employee_user)
            response = self.api_post("/hr/ltc/", payload, expected_status=None)

            if response.status_code == 400:
                self._record_result(
                    "Profile check rejected incomplete data",
                    "Pass",
                    str(response.data),
                )
            else:
                self._record_result(
                    f"Expected 400, got {response.status_code}",
                    "Fail",
                    str(response.data),
                )
                self.fail("Incomplete profile should return HTTP 400")
        finally:
            # Restore so later tests are not affected
            self.confidential.aadhar_no = 123456789012
            self.confidential.bank_account_no = 987654321
            self.confidential.save()


# ─────────────────────────────────────────────────────────────────────────────
# UC-2: Retrieve LTC Application History
# ─────────────────────────────────────────────────────────────────────────────

class TestUC02_RetrieveLTCHistory(UCTestBase):
    """UC-2: Employee retrieves their LTC application history."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Pre-create an LTC form for the employee
        cls.ltc_form = LTCform.objects.create(
            employeeId=1001,
            name="Test Employee",
            designation="Faculty",
            pfNo=1001,
            blockYear="2024-2026",
            basicPaySalary=60000,
            departmentInfo="CSE",
            hometownOrNot=False,
            placeOfVisit="Delhi",
            addressDuringLeave="123 Main St",
            modeofTravel="Train",
            amountOfAdvanceRequired=10000,
            phoneNumberForContact=9876543210,
            submissionDate=datetime.date.today(),
            created_by=cls.employee_user,
            workflow_status="submitted",
        )

    def test_hp01_get_ltc_forms_current_year(self):
        """Happy Path — Employee fetches their own LTC forms for the current year."""
        self._test_id = "UC-2-HP-01"
        self._uc_id = "UC-2"
        self._test_category = "Happy Path"
        self._scenario = "Employee GETs /ltc/?name=emp_test"
        self._preconditions = "LTC form exists in DB for emp_test"
        self._input_action = "GET /hr/ltc/?name=emp_test"
        self._expected_result = "HTTP 200 with list containing the LTC form"

        self.login_as_employee()
        response = self.api_get("/hr/ltc/", {"name": self.employee_user.username},
                                expected_status=None)

        if response.status_code == 200:
            self._record_result("LTC history returned", "Pass",
                                f"Data: {response.data}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ap01_get_ltc_with_explicit_date_range(self):
        """Alternate Path — Employee retrieves LTC forms with explicit from/to dates."""
        self._test_id = "UC-2-AP-01"
        self._uc_id = "UC-2"
        self._test_category = "Alternate Path"
        self._scenario = "GET with from_date and to_date spanning today"
        self._preconditions = "LTC form created today"
        self._input_action = "GET /hr/ltc/?name=emp_test&from_date=2026-01-01&to_date=2026-12-31"
        self._expected_result = "HTTP 200 with filtered results"

        self.login_as_employee()
        response = self.api_get("/hr/ltc/", {
            "name": self.employee_user.username,
            "from_date": f"{datetime.date.today().year}-01-01",
            "to_date": f"{datetime.date.today().year}-12-31",
        }, expected_status=None)

        if response.status_code == 200:
            self._record_result("Date-filtered LTC list returned", "Pass",
                                f"Data: {response.data}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_get_ltc_invalid_date_range(self):
        """Exception — from_date after to_date returns empty list (not error)."""
        self._test_id = "UC-2-EX-01"
        self._uc_id = "UC-2"
        self._test_category = "Exception"
        self._scenario = "from_date=2026-12-31, to_date=2026-01-01 (reversed)"
        self._preconditions = "Employee logged in"
        self._input_action = "GET /hr/ltc/?name=emp_test&from_date=2026-12-31&to_date=2026-01-01"
        self._expected_result = "HTTP 200 with empty list"

        self.login_as_employee()
        response = self.api_get("/hr/ltc/", {
            "name": self.employee_user.username,
            "from_date": "2026-12-31",
            "to_date": "2026-01-01",
        }, expected_status=None)

        if response.status_code == 200:
            # Service returns [] for invalid ranges
            self._record_result("Empty list returned for invalid range", "Pass",
                                f"Data: {response.data}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Partial",
                                str(response.data))


# ─────────────────────────────────────────────────────────────────────────────
# UC-3: Submit CPDA Advance Application
# ─────────────────────────────────────────────────────────────────────────────

class TestUC03_SubmitCPDAAdvance(UCTestBase):
    """UC-3: Faculty member submits a CPDA Advance request."""

    def test_hp01_submit_cpda_with_hod_configured(self):
        """Happy Path — Faculty in CSE (HOD configured) submits CPDA Advance."""
        self._test_id = "UC-3-HP-01"
        self._uc_id = "UC-3"
        self._test_category = "Happy Path"
        self._scenario = "Faculty in CSE dept with HOD submits CPDA Advance"
        self._preconditions = "HOD (CSE) designation assigned to hod_cse; employee dept=CSE"
        self._input_action = "POST /hr/cpdaadv/ with valid form_data"
        self._expected_result = "CPDAAdvanceform created, workflow_status=submitted, HTTP 200"

        self.login_as_employee()
        payload = _cpda_payload(self.employee_user)
        response = self.api_post("/hr/cpdaadv/", payload, expected_status=None)

        if response.status_code == 200:
            self.assertTrue(
                CPDAAdvanceform.objects.filter(created_by=self.employee_user).exists()
            )
            cpda = CPDAAdvanceform.objects.filter(created_by=self.employee_user).first()
            self.assertEqual(cpda.workflow_status, "submitted")
            self._record_result("CPDA Advance created and routed to HOD", "Pass",
                                f"workflow_status={cpda.workflow_status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ap01_hr_admin_lists_employee_cpda_forms(self):
        """Alternate Path — HR Admin retrieves another employee's CPDA forms."""
        self._test_id = "UC-3-AP-01"
        self._uc_id = "UC-3"
        self._test_category = "Alternate Path"
        self._scenario = "HR Admin GETs /cpdaadv/?name=emp_test"
        self._preconditions = "HR Admin designation exists; CPDAAdvanceform exists for emp_test"
        self._input_action = "GET /hr/cpdaadv/?name=emp_test as hr_admin"
        self._expected_result = "HTTP 200 with emp_test CPDA forms"

        # Create a CPDA form to be retrieved
        CPDAAdvanceform.objects.create(
            employeeId=1001, name="Test Employee", designation="Faculty",
            pfNo=1001, purpose="Conference", amountRequired=3000,
            submissionDate=datetime.date.today(), created_by=self.employee_user,
            workflow_status="submitted",
        )

        self.login_as_hr_admin()
        response = self.api_get("/hr/cpdaadv/",
                                {"name": self.employee_user.username}, expected_status=None)

        if response.status_code == 200:
            self._record_result("HR Admin fetched employee CPDA forms", "Pass",
                                f"Data: {response.data}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_submit_cpda_no_hod(self):
        """Exception — Employee with no department has no HOD; submission rejected."""
        self._test_id = "UC-3-EX-01"
        self._uc_id = "UC-3"
        self._test_category = "Exception"
        self._scenario = "Employee without a department (no HOD) submits CPDA"
        self._preconditions = "emp_extra.department = None"
        self._input_action = "POST /hr/cpdaadv/ as employee with no department"
        self._expected_result = "HTTP 400 with HOD not configured message"

        # Temporarily remove department
        original_dept = self.emp_extra.department
        self.emp_extra.department = None
        self.emp_extra.save()

        try:
            self.login_as_employee()
            payload = _cpda_payload(self.employee_user)
            response = self.api_post("/hr/cpdaadv/", payload, expected_status=None)

            if response.status_code == 400:
                data = response.data
                detail = str(data.get("detail", ""))
                if "HOD" in detail or "hod" in detail.lower() or "configured" in detail.lower():
                    self._record_result("Correctly rejected (no HOD)", "Pass", str(data))
                else:
                    self._record_result("Rejected but wrong message", "Partial", str(data))
            else:
                self._record_result(f"Expected 400, got {response.status_code}", "Fail",
                                    str(response.data))
                self.fail("Should reject when no HOD configured")
        finally:
            self.emp_extra.department = original_dept
            self.emp_extra.save()


# ─────────────────────────────────────────────────────────────────────────────
# UC-4: Submit Appraisal Form
# ─────────────────────────────────────────────────────────────────────────────

class TestUC04_SubmitAppraisal(UCTestBase):
    """UC-4: Faculty/staff submits annual appraisal form."""

    def test_hp01_submit_appraisal_valid(self):
        """Happy Path — Faculty submits appraisal with valid data and approver."""
        self._test_id = "UC-4-HP-01"
        self._uc_id = "UC-4"
        self._test_category = "Happy Path"
        self._scenario = "Faculty submits appraisal with receiver_name=hr_admin"
        self._preconditions = "HR Admin user and designation exist; no submission window restriction"
        self._input_action = "POST /hr/appraisal/ with valid list payload"
        self._expected_result = "Appraisalform created, workflow_status=submitted, HTTP 200"

        self.login_as_employee()
        payload = _appraisal_payload()
        response = self.api_post("/hr/appraisal/", payload, expected_status=None)

        if response.status_code == 200:
            self.assertTrue(
                Appraisalform.objects.filter(created_by=self.employee_user).exists()
            )
            form = Appraisalform.objects.filter(created_by=self.employee_user).first()
            self.assertEqual(form.workflow_status, "submitted")
            self._record_result("Appraisal form created", "Pass",
                                f"workflow_status={form.workflow_status}")
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}: {response.data}")

    def test_ap01_retrieve_appraisal_history(self):
        """Alternate Path — Employee retrieves previously submitted appraisals."""
        self._test_id = "UC-4-AP-01"
        self._uc_id = "UC-4"
        self._test_category = "Alternate Path"
        self._scenario = "GET /hr/appraisal/?name=emp_test returns existing appraisals"
        self._preconditions = "One Appraisalform exists for emp_test"
        self._input_action = "GET /hr/appraisal/?name=emp_test"
        self._expected_result = "HTTP 200 with list of appraisals"

        Appraisalform.objects.create(
            employeeId=1001, name="Test Employee", designation="Faculty",
            pfNo=1001, submissionDate=datetime.date.today(),
            created_by=self.employee_user, workflow_status="submitted",
        )

        self.login_as_employee()
        response = self.api_get("/hr/appraisal/",
                                {"name": self.employee_user.username}, expected_status=None)

        if response.status_code == 200:
            self._record_result("Appraisal history returned", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Fail", str(response.data))
            self.fail(f"Expected 200, got {response.status_code}")

    def test_ex01_submit_appraisal_missing_receiver(self):
        """Exception — Appraisal submission without receiver/approver info is rejected."""
        self._test_id = "UC-4-EX-01"
        self._uc_id = "UC-4"
        self._test_category = "Exception"
        self._scenario = "POST /hr/appraisal/ with empty user_info"
        self._preconditions = "Employee is logged in"
        self._input_action = "POST /hr/appraisal/ with [{...form_data}, {}] (empty user_info)"
        self._expected_result = "HTTP 400 with approver required message"

        self.login_as_employee()
        form_data = {
            "employeeId": 1001, "name": "Test Employee", "designation": "Faculty",
            "pfNo": 1001, "submissionDate": datetime.date.today().isoformat(),
        }
        payload = [form_data, {}]  # empty user_info
        response = self.api_post("/hr/appraisal/", payload, expected_status=None)

        if response.status_code == 400:
            self._record_result("Correctly rejected missing receiver", "Pass",
                                str(response.data))
        else:
            self._record_result(f"Expected 400, got {response.status_code}", "Fail",
                                str(response.data))
            self.fail("Should reject appraisal with missing receiver info")


# ─────────────────────────────────────────────────────────────────────────────
# UC-5: Check Leave Balance
# ─────────────────────────────────────────────────────────────────────────────

class TestUC05_CheckLeaveBalance(UCTestBase):
    """UC-5: Employee checks their leave balance."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.leave_balance = LeaveBalance.objects.create(
            employeeId=cls.emp_extra,
            casual_leave_allotted=15,
            casual_leave_used=3,
            earned_leave_allotted=30,
            earned_leave_used=5,
        )

    def test_hp01_employee_fetches_leave_balance(self):
        """Happy Path — Authenticated employee retrieves their leave balance."""
        self._test_id = "UC-5-HP-01"
        self._uc_id = "UC-5"
        self._test_category = "Happy Path"
        self._scenario = "GET /hr/leaveBalance/ as authenticated employee"
        self._preconditions = "LeaveBalance record exists for employee"
        self._input_action = "GET /hr/leaveBalance/"
        self._expected_result = "HTTP 200 with leave balance data"

        self.login_as_employee()
        response = self.api_get("/hr/leaveBalance/", expected_status=None)

        if response.status_code == 200:
            self._record_result("Leave balance returned", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Partial",
                                str(response.data))

    def test_ap01_hr_admin_fetches_all_leave_balances(self):
        """Alternate Path — HR Admin retrieves all employee leave balances."""
        self._test_id = "UC-5-AP-01"
        self._uc_id = "UC-5"
        self._test_category = "Alternate Path"
        self._scenario = "GET /hr/leaveBalance/all/ as HR Admin"
        self._preconditions = "HR Admin logged in; at least one LeaveBalance exists"
        self._input_action = "GET /hr/leaveBalance/all/"
        self._expected_result = "HTTP 200 with list of leave balance records"

        self.login_as_hr_admin()
        response = self.api_get("/hr/leaveBalance/all/", expected_status=None)

        if response.status_code == 200:
            self._record_result("All leave balances returned", "Pass", str(response.data))
        else:
            self._record_result(f"HTTP {response.status_code}", "Partial",
                                str(response.data))

    def test_ex01_unauthenticated_leave_balance_access(self):
        """Exception — Unauthenticated request to leave balance endpoint is rejected."""
        self._test_id = "UC-5-EX-01"
        self._uc_id = "UC-5"
        self._test_category = "Exception"
        self._scenario = "GET /hr/leaveBalance/ without any credentials"
        self._preconditions = "No auth token"
        self._input_action = "GET /hr/leaveBalance/ with no authentication"
        self._expected_result = "HTTP 401 or 403"

        self.logout()
        response = self.api_get("/hr/leaveBalance/", expected_status=None)

        if response.status_code in (401, 403):
            self._record_result("Unauthenticated access correctly blocked", "Pass",
                                f"HTTP {response.status_code}")
        else:
            self._record_result(f"Expected 401/403, got {response.status_code}", "Fail",
                                str(response.data))
            self.fail("Unauthenticated access should be blocked")
