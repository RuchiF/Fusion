"""
Reporting Test Runner for HR2 module.

DO NOT EDIT — generated scaffold file.

Generates 7 CSV report files in applications/hr2/tests/reports/ after every run:
  Module_Test_Summary.csv
  UC_Test_Design.csv
  BR_Test_Design.csv
  WF_Test_Design.csv
  Test_Execution_Log.csv
  Defect_Log.csv
  Artifact_Evaluation.csv

Usage (from FusionIIIT/ directory):
  python manage.py test applications.hr2.tests -v 2 \\
    --testrunner=applications.hr2.tests.runner.ReportingTestRunner

Set tester name:
  set TESTER_NAME=YourName  (Windows)
  TESTER_NAME=YourName ...  (Linux/Mac)
""" 

import csv
import datetime
import os
import traceback
import unittest

# ── Constants ─────────────────────────────────────────────────────────────────

MODULE_NAME = "hr2"
TESTER_NAME = "Tester1"
REPORTS_DIR = os.path.join(
    os.path.dirname(__file__), "reports"
)

# Spec counts (update if you add more UCs / BRs / WFs)
NUM_UCS = 5
NUM_BRS = 11
NUM_WFS = 3

REQUIRED_UC_TESTS = NUM_UCS * 3   # 1 HP + 1 AP + 1 EX each
REQUIRED_BR_TESTS = NUM_BRS * 2   # 1 valid + 1 invalid each
REQUIRED_WF_TESTS = NUM_WFS * 2   # 1 E2E + 1 negative each


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ensure_reports_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _csv_path(filename):
    return os.path.join(REPORTS_DIR, filename)


def _write_csv(filename, headers, rows):
    path = _csv_path(filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return path


# ── Result collector ──────────────────────────────────────────────────────────

class _ResultCollector:
    """Collects per-test metadata and outcomes during a test run."""

    def __init__(self):
        self.records = []   # list of dicts

    def add(self, test, outcome, error_text=""):
        meta = {
            "test_id":        getattr(test, "_test_id", ""),
            "uc_id":          getattr(test, "_uc_id", ""),
            "br_id":          getattr(test, "_br_id", ""),
            "wf_id":          getattr(test, "_wf_id", ""),
            "category":       getattr(test, "_test_category", ""),
            "scenario":       getattr(test, "_scenario", ""),
            "preconditions":  getattr(test, "_preconditions", ""),
            "input_action":   getattr(test, "_input_action", ""),
            "expected_result":getattr(test, "_expected_result", ""),
            "actual_result":  getattr(test, "_actual_result", ""),
            "status":         getattr(test, "_status", "Not Run"),
            "evidence":       getattr(test, "_evidence", ""),
            "steps":          getattr(test, "_steps", []),
            "error_text":     error_text,
            "test_name":      str(test),
            "module":         MODULE_NAME,
            "tester":         TESTER_NAME,
            "timestamp":      datetime.datetime.now().isoformat(timespec="seconds"),
        }
        # Override status based on actual outcome
        if error_text and meta["status"] not in ("Pass", "Partial"):
            meta["status"] = "Fail"
        self.records.append(meta)


# ── Custom test result ────────────────────────────────────────────────────────

class _ReportingResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity, collector):
        super().__init__(stream, descriptions, verbosity)
        self._collector = collector

    def addSuccess(self, test):
        super().addSuccess(test)
        self._collector.add(test, "Pass")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._collector.add(test, "Fail",
                            "".join(traceback.format_exception(*err)))

    def addError(self, test, err):
        super().addError(test, err)
        self._collector.add(test, "Error",
                            "".join(traceback.format_exception(*err)))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._collector.add(test, "Skip", reason)


# ── Custom runner ─────────────────────────────────────────────────────────────

class ReportingTestRunner(unittest.TextTestRunner):
    """Django-compatible test runner that writes 7 CSV reports after the run."""

    # Django calls this class via --testrunner; it replaces the default runner.
    # We need to satisfy Django's runner protocol (run_tests) as well as the
    # standard unittest protocol (run).

    def __init__(self, *args, **kwargs):
        # Django passes many CLI kwargs (settings, keepdb, pythonpath, etc.)
        # to the test runner. unittest.TextTestRunner only accepts a fixed set,
        # so we whitelist only what it understands and discard the rest.
        _VALID_RUNNER_KWARGS = {
            "stream", "descriptions", "verbosity", "failfast",
            "buffer", "resultclass", "warnings", "tb_locals",
        }
        filtered = {k: v for k, v in kwargs.items() if k in _VALID_RUNNER_KWARGS}
        filtered.setdefault("verbosity", 2)
        super().__init__(*args, **filtered)
        self._collector = _ResultCollector()

    # ── unittest protocol ─────────────────────────────────────────────────────

    def _makeResult(self):
        return _ReportingResult(
            self.stream, self.descriptions, self.verbosity, self._collector
        )

    def run(self, test):
        result = super().run(test)
        _ensure_reports_dir()
        self._write_all_reports()
        return result

    # ── Django protocol ───────────────────────────────────────────────────────

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """Entry point called by `manage.py test --testrunner=...`."""
        # Build suite the same way Django's DiscoverRunner does.
        import django.test.utils as dtu
        from django.test.runner import DiscoverRunner

        django_runner = DiscoverRunner(verbosity=self.verbosity)
        suite = django_runner.build_suite(test_labels, extra_tests)

        old_config = django_runner.setup_databases()
        try:
            result = self.run(suite)
        finally:
            django_runner.teardown_databases(old_config)

        return len(result.failures) + len(result.errors)

    # ── Report generation ─────────────────────────────────────────────────────

    def _write_all_reports(self):
        records = self._collector.records

        uc_records = [r for r in records if r["uc_id"]]
        br_records = [r for r in records if r["br_id"]]
        wf_records = [r for r in records if r["wf_id"]]
        all_fail   = [r for r in records if r["status"] in ("Fail", "Error")]

        designed_uc = len(uc_records)
        designed_br = len(br_records)
        designed_wf = len(wf_records)
        total_tests  = len(records)
        total_pass   = sum(1 for r in records if r["status"] == "Pass")
        total_partial= sum(1 for r in records if r["status"] == "Partial")
        total_fail   = sum(1 for r in records if r["status"] in ("Fail", "Error"))

        def pct(n, d):
            return f"{100*n/d:.1f}%" if d else "N/A"

        # Sheet 1 — Module_Test_Summary.csv
        _write_csv("Module_Test_Summary.csv",
            ["Metric", "Value"],
            [
                ["Module", MODULE_NAME],
                ["Tester", TESTER_NAME],
                ["Run Date", datetime.date.today().isoformat()],
                ["Total Use Cases", NUM_UCS],
                ["Total Business Rules", NUM_BRS],
                ["Total Workflows", NUM_WFS],
                ["Required UC Tests", REQUIRED_UC_TESTS],
                ["Designed UC Tests", designed_uc],
                ["Required BR Tests", REQUIRED_BR_TESTS],
                ["Designed BR Tests", designed_br],
                ["Required WF Tests", REQUIRED_WF_TESTS],
                ["Designed WF Tests", designed_wf],
                ["UC Adequacy %", pct(designed_uc, REQUIRED_UC_TESTS)],
                ["BR Adequacy %", pct(designed_br, REQUIRED_BR_TESTS)],
                ["WF Adequacy %", pct(designed_wf, REQUIRED_WF_TESTS)],
                ["Total Tests Executed", total_tests],
                ["Total Pass", total_pass],
                ["Total Partial", total_partial],
                ["Total Fail", total_fail],
                ["Strict Pass Rate %", pct(total_pass, total_tests)],
            ]
        )

        # Sheet 2 — UC_Test_Design.csv
        _write_csv("UC_Test_Design.csv",
            ["Test ID", "UC ID", "Category", "Scenario",
             "Preconditions", "Input/Action", "Expected Result", "Tester"],
            [
                [r["test_id"], r["uc_id"], r["category"], r["scenario"],
                 r["preconditions"], r["input_action"], r["expected_result"],
                 r["tester"]]
                for r in uc_records
            ]
        )

        # Sheet 3 — BR_Test_Design.csv
        _write_csv("BR_Test_Design.csv",
            ["Test ID", "BR ID", "Category", "Input/Action", "Expected Result", "Tester"],
            [
                [r["test_id"], r["br_id"], r["category"],
                 r["input_action"], r["expected_result"], r["tester"]]
                for r in br_records
            ]
        )

        # Sheet 4 — WF_Test_Design.csv
        _write_csv("WF_Test_Design.csv",
            ["Test ID", "WF ID", "Category", "Scenario", "Expected Final State", "Tester"],
            [
                [r["test_id"], r["wf_id"], r["category"], r["scenario"],
                 r["expected_result"], r["tester"]]
                for r in wf_records
            ]
        )

        # Sheet 5 — Test_Execution_Log.csv
        _write_csv("Test_Execution_Log.csv",
            ["Test ID", "Test Name", "Category", "Status",
             "Actual Result", "Evidence", "Timestamp", "Tester"],
            [
                [r["test_id"], r["test_name"], r["category"], r["status"],
                 r["actual_result"], r["evidence"], r["timestamp"], r["tester"]]
                for r in records
            ]
        )

        # Sheet 6 — Defect_Log.csv
        _write_csv("Defect_Log.csv",
            ["Test ID", "Test Name", "Status", "Error / Detail", "Timestamp"],
            [
                [r["test_id"], r["test_name"], r["status"],
                 r["error_text"][:500], r["timestamp"]]
                for r in all_fail
            ]
        )

        # Sheet 7 — Artifact_Evaluation.csv
        def _uc_status(uid):
            rows = [r for r in uc_records if r["uc_id"] == uid]
            if not rows:            return "Not Implemented"
            passes = sum(1 for r in rows if r["status"] == "Pass")
            if passes == len(rows): return "Implemented Correctly"
            if passes > 0:          return "Partially Implemented"
            return "Incorrectly Implemented"

        def _br_status(bid):
            rows = [r for r in br_records if r["br_id"] == bid]
            if not rows:            return "Not Enforced"
            passes = sum(1 for r in rows if r["status"] == "Pass")
            if passes == len(rows): return "Enforced Correctly"
            if passes > 0:          return "Partially Enforced"
            return "Incorrectly Enforced"

        def _wf_status(wid):
            rows = [r for r in wf_records if r["wf_id"] == wid]
            if not rows:            return "Missing"
            passes = sum(1 for r in rows if r["status"] == "Pass")
            if passes == len(rows): return "Complete"
            if passes > 0:          return "Partial"
            return "Incorrect"

        eval_rows = []
        for i in range(1, NUM_UCS + 1):
            uid = f"UC-{i}"
            eval_rows.append([uid, "Use Case", _uc_status(uid)])
        for i in range(1, NUM_BRS + 1):
            bid = f"BR-{i}"
            eval_rows.append([bid, "Business Rule", _br_status(bid)])
        for i in range(1, NUM_WFS + 1):
            wid = f"WF-{i}"
            eval_rows.append([wid, "Workflow", _wf_status(wid)])

        _write_csv("Artifact_Evaluation.csv",
            ["Artifact ID", "Type", "Status"],
            eval_rows
        )

        print(f"\n[HR2] Reports written to: {REPORTS_DIR}")
        print(f"[HR2] UC Adequacy: {pct(designed_uc, REQUIRED_UC_TESTS)} | "
              f"BR Adequacy: {pct(designed_br, REQUIRED_BR_TESTS)} | "
              f"WF Adequacy: {pct(designed_wf, REQUIRED_WF_TESTS)}")
        print(f"[HR2] Pass: {total_pass}/{total_tests} "
              f"({pct(total_pass, total_tests)})\n")
