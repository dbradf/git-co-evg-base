"""Unit tests for build_status.py."""

import goodbase.models.build_status as under_test


class TestBuildStatus:
    def test_success_percent_should_be_percent_of_successful_tasks(self):
        build_status = under_test.BuildStatus(
            build_name="build name",
            successful_tasks={f"task {i}" for i in range(5)},
            inactive_tasks=set(),
            all_tasks={f"task {i}" for i in range(10)},
        )

        assert build_status.success_pct() == 0.5

    def test_active_pct_should_be_percent_of_active_tasks(self):
        build_status = under_test.BuildStatus(
            build_name="build name",
            successful_tasks=set(),
            inactive_tasks={f"task {i}" for i in range(3)},
            all_tasks={f"task {i}" for i in range(10)},
        )

        assert build_status.active_pct() == 0.7
