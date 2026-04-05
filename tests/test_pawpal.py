from pawpal_system import Task, Frequency, Pet, Owner, Scheduler

# to run: python -m pytest tests/test_pawpal.py

def test_mark_complete_changes_status():
    task = Task(
        title="Vet Checkup",
        duration_minutes=60,
        priority="high",
        is_required=True,
        frequency=Frequency.ONCE,
    )
    assert task.is_complete is False
    task.mark_complete()
    assert task.is_complete is True


def test_mark_complete_raises_for_recurring_task():
    task = Task(
        title="Morning Walk",
        duration_minutes=30,
        priority="high",
        is_required=True,
        frequency=Frequency.DAILY,
    )
    assert task.is_complete is None
    try:
        task.mark_complete()
        assert False, "Expected ValueError"
    except ValueError:
        pass
    assert task.is_complete is None  # status unchanged


# ── Behavior 1: Required tasks always appear even over budget ──────────────────

def test_required_task_scheduled_when_over_budget():
    """A required task that busts the budget must still appear in scheduled_tasks."""
    owner = Owner(name="Alex", available_minutes=10)
    owner.add_task(Task("Big Vet Visit", duration_minutes=60, priority="high", is_required=True))
    plan = owner.schedule_day()

    scheduled_titles = [st.task.title for st in plan.scheduled_tasks]
    assert "Big Vet Visit" in scheduled_titles
    assert "Big Vet Visit" not in [t.title for t in plan.skipped_tasks]


def test_over_budget_flag_set_when_required_task_exceeds_time():
    """DailyPlan.is_over_budget must be True when required tasks exceed available minutes."""
    owner = Owner(name="Alex", available_minutes=10)
    owner.add_task(Task("Big Vet Visit", duration_minutes=60, priority="high", is_required=True))
    plan = owner.schedule_day()

    assert plan.is_over_budget is True


def test_optional_task_skipped_when_budget_exceeded_by_required():
    """Optional tasks must be skipped when required tasks consume the full budget."""
    owner = Owner(name="Alex", available_minutes=30)
    owner.add_task(Task("Required Walk", duration_minutes=30, priority="high", is_required=True))
    owner.add_task(Task("Optional Grooming", duration_minutes=20, priority="low", is_required=False))
    plan = owner.schedule_day()

    assert "Optional Grooming" not in [st.task.title for st in plan.scheduled_tasks]
    assert "Optional Grooming" in [t.title for t in plan.skipped_tasks]


# ── Behavior 2: Completed ONCE tasks are excluded from the plan ────────────────

def test_completed_once_task_excluded_from_plan():
    """A ONCE task that is marked complete must not appear in the next plan."""
    owner = Owner(name="Alex", available_minutes=120)
    task = Task("Vet Checkup", duration_minutes=60, priority="high",
                is_required=True, frequency=Frequency.ONCE)
    owner.add_task(task)
    task.mark_complete()

    plan = owner.schedule_day()
    scheduled_titles = [st.task.title for st in plan.scheduled_tasks]
    assert "Vet Checkup" not in scheduled_titles


def test_incomplete_once_task_included_in_plan():
    """A ONCE task that is NOT yet complete must still appear in the plan."""
    owner = Owner(name="Alex", available_minutes=120)
    owner.add_task(Task("Vet Checkup", duration_minutes=60, priority="high",
                        is_required=True, frequency=Frequency.ONCE))
    plan = owner.schedule_day()

    assert "Vet Checkup" in [st.task.title for st in plan.scheduled_tasks]


# ── Behavior 3: Pinned task conflict resolution ────────────────────────────────

def test_optional_pinned_task_bumped_when_required_at_same_slot():
    """An optional pinned task at the same time as a required pinned task must be skipped."""
    owner = Owner(name="Alex", available_minutes=120)
    owner.add_task(Task("Required Med", duration_minutes=10, priority="high",
                        is_required=True, time="09:00"))
    owner.add_task(Task("Optional Bath", duration_minutes=20, priority="low",
                        is_required=False, time="09:00"))
    plan = owner.schedule_day()

    scheduled_titles = [st.task.title for st in plan.scheduled_tasks]
    assert "Required Med" in scheduled_titles
    assert "Optional Bath" not in scheduled_titles
    assert "Optional Bath" in [t.title for t in plan.skipped_tasks]


def test_two_required_pinned_tasks_at_same_slot_both_scheduled_with_warning():
    """Two required tasks pinned to the same slot must both be scheduled and generate a warning."""
    owner = Owner(name="Alex", available_minutes=120)
    owner.add_task(Task("Morning Meds", duration_minutes=10, priority="high",
                        is_required=True, time="08:00"))
    owner.add_task(Task("Morning Feed", duration_minutes=15, priority="high",
                        is_required=True, time="08:00"))
    plan = owner.schedule_day()

    scheduled_titles = [st.task.title for st in plan.scheduled_tasks]
    assert "Morning Meds" in scheduled_titles
    assert "Morning Feed" in scheduled_titles
    assert any("08:00" in w and "required" in w.lower() for w in plan.warnings)


# ── Behavior 4: Optional tasks respect the budget reserved for required tasks ──

def test_optional_budget_shrinks_when_required_task_is_large():
    """Optional tasks must not be scheduled beyond the budget left after required tasks."""
    owner = Owner(name="Alex", available_minutes=60)
    owner.add_task(Task("Required Walk", duration_minutes=50, priority="high", is_required=True))
    owner.add_task(Task("Optional Play", duration_minutes=20, priority="medium", is_required=False))
    plan = owner.schedule_day()

    # Only 10 min left for optionals; Optional Play (20 min) must be skipped
    assert "Optional Play" not in [st.task.title for st in plan.scheduled_tasks]
    assert "Optional Play" in [t.title for t in plan.skipped_tasks]


def test_optional_task_fits_within_remaining_budget():
    """An optional task that fits within the leftover budget must be scheduled."""
    owner = Owner(name="Alex", available_minutes=60)
    owner.add_task(Task("Required Walk", duration_minutes=30, priority="high", is_required=True))
    owner.add_task(Task("Optional Play", duration_minutes=20, priority="medium", is_required=False))
    plan = owner.schedule_day()

    assert "Optional Play" in [st.task.title for st in plan.scheduled_tasks]


# ── Behavior 5: Owner preference sets the schedule start hour ─────────────────

def test_morning_preference_starts_at_8():
    owner = Owner(name="Alex", available_minutes=120, preferences=["morning"])
    owner.add_task(Task("Walk", duration_minutes=30, priority="high", is_required=True))
    plan = owner.schedule_day()

    assert plan.scheduled_tasks[0].start_time == "08:00"


def test_afternoon_preference_starts_at_13():
    owner = Owner(name="Alex", available_minutes=120, preferences=["afternoon"])
    owner.add_task(Task("Walk", duration_minutes=30, priority="high", is_required=True))
    plan = owner.schedule_day()

    assert plan.scheduled_tasks[0].start_time == "13:00"


def test_evening_preference_starts_at_17():
    owner = Owner(name="Alex", available_minutes=120, preferences=["evening"])
    owner.add_task(Task("Walk", duration_minutes=30, priority="high", is_required=True))
    plan = owner.schedule_day()

    assert plan.scheduled_tasks[0].start_time == "17:00"


def test_first_matching_preference_wins():
    """When multiple preferences are listed, the first recognized one must win."""
    owner = Owner(name="Alex", available_minutes=120, preferences=["afternoon", "morning"])
    owner.add_task(Task("Walk", duration_minutes=30, priority="high", is_required=True))
    plan = owner.schedule_day()

    assert plan.scheduled_tasks[0].start_time == "13:00"


def test_unrecognized_preference_defaults_to_8():
    owner = Owner(name="Alex", available_minutes=120, preferences=["unknown"])
    owner.add_task(Task("Walk", duration_minutes=30, priority="high", is_required=True))
    plan = owner.schedule_day()

    assert plan.scheduled_tasks[0].start_time == "08:00"


# ── Existing tests ─────────────────────────────────────────────────────────────

def test_adding_task_to_pet_increases_task_count():
    pet = Pet(name="Buddy", species="dog", age=3)
    owner = Owner(name="Alex", available_minutes=120)

    assert len([t for t in owner.tasks if t.pet == pet]) == 0

    owner.add_task(Task(
        title="Morning Walk",
        duration_minutes=30,
        priority="high",
        is_required=True,
        frequency=Frequency.DAILY,
        pet=pet,
    ))
    assert len([t for t in owner.tasks if t.pet == pet]) == 1

    owner.add_task(Task(
        title="Evening Feed",
        duration_minutes=10,
        priority="medium",
        is_required=True,
        frequency=Frequency.DAILY,
        pet=pet,
    ))
    assert len([t for t in owner.tasks if t.pet == pet]) == 2
