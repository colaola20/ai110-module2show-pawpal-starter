from pawpal_system import Owner, Pet, Task, Frequency

# --- Create Owner ---
owner = Owner(name="Jordan", available_minutes=180, preferences=["morning"])

# --- Create Pets ---
mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5, special_needs=["medication"])

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Create Tasks ---
morning_walk = Task(
    title="Morning Walk",
    duration_minutes=30,
    priority="high",
    is_required=True,
    frequency=Frequency.DAILY,
    pet=mochi,
    time="08:00",  # pinned to 8 AM
)

feeding = Task(
    title="Feeding",
    duration_minutes=15,
    priority="high",
    is_required=True,
    frequency=Frequency.DAILY,
    pet=None,
)

luna_medication = Task(
    title="Luna's Medication",
    duration_minutes=10,
    priority="high",
    is_required=True,
    frequency=Frequency.DAILY,
    pet=luna,
    time="09:00",  # pinned to 9 AM
)

grooming = Task(
    title="Grooming Session",
    duration_minutes=20,
    priority="medium",
    is_required=False,
    frequency=Frequency.WEEKLY,
    pet=mochi,
)

vet_visit = Task(
    title="Vet Checkup",
    duration_minutes=60,
    priority="high",
    is_required=True,
    frequency=Frequency.ONCE,
    pet=mochi,
    time="14:00",  # pinned to 2 PM
)

playtime = Task(
    title="Playtime",
    duration_minutes=20,
    priority="low",
    is_required=False,
    frequency=Frequency.DAILY,
    pet=luna,
)

owner.add_task(morning_walk)
owner.add_task(feeding)
owner.add_task(luna_medication)
owner.add_task(grooming)
owner.add_task(playtime)
owner.add_task(vet_visit)


# ── Test 1: Pinned times are respected ────────────────────────────────────────
print("=== Test 1: Pinned times are respected ===")
plan = owner.schedule_day()
print(plan.display())
print()

for st in plan.scheduled_tasks:
    if st.task.time:
        assert st.start_time == st.task.time, (
            f"Expected '{st.task.title}' at {st.task.time}, got {st.start_time}"
        )
        print(f"  '{st.task.title}' correctly pinned at {st.start_time} ✓")

# Free tasks should not overlap pinned slots
morning_walk_end = 8 * 60 + 30   # 08:30
med_start = 9 * 60               # 09:00
free_between = [
    st for st in plan.scheduled_tasks
    if not st.task.time and st.start_time >= "08:30" and st.start_time < "09:00"
]
for st in free_between:
    assert st.task.duration_minutes <= (med_start - morning_walk_end), (
        f"'{st.task.title}' overlaps the 09:00 pinned slot"
    )
print("Pinned time test PASSED\n")


# ── Test 2: No warning for required + optional at the same time ────────────────
print("=== Test 2: No conflict warning for required + optional at same time ===")
optional_same_time = Task(
    title="Optional Walk",
    duration_minutes=15,
    priority="low",
    is_required=False,
    frequency=Frequency.DAILY,
    pet=mochi,
    time="08:00",  # same as Morning Walk (required)
)
owner.add_task(optional_same_time)
plan2 = owner.schedule_day()
assert len(plan2.warnings) == 0, f"Unexpected warnings: {plan2.warnings}"
# Required task should be scheduled; optional one should be skipped
scheduled_titles = [st.task.title for st in plan2.scheduled_tasks]
skipped_titles = [t.title for t in plan2.skipped_tasks]
assert "Morning Walk" in scheduled_titles, "Required task at 08:00 should be scheduled"
assert "Optional Walk" in skipped_titles, "Optional task at 08:00 should be skipped"
print(f"  Scheduled: {scheduled_titles}")
print(f"  Skipped:   {skipped_titles}")
print("No-conflict test PASSED\n")
owner.remove_task("Optional Walk")


# ── Test 3: Warning for two required tasks at the same time ───────────────────
print("=== Test 3: Warning when two required tasks share a pinned time ===")
conflict_task = Task(
    title="Emergency Vet",
    duration_minutes=30,
    priority="high",
    is_required=True,
    frequency=Frequency.ONCE,
    pet=luna,
    time="08:00",  # conflicts with Morning Walk (also required at 08:00)
)
owner.add_task(conflict_task)
plan3 = owner.schedule_day()
assert len(plan3.warnings) == 1, f"Expected 1 warning, got: {plan3.warnings}"
assert "08:00" in plan3.warnings[0]
print(f"  Warning: {plan3.warnings[0]}")
# Both required tasks should still be scheduled
scheduled_titles3 = [st.task.title for st in plan3.scheduled_tasks]
assert "Morning Walk" in scheduled_titles3
assert "Emergency Vet" in scheduled_titles3
print(f"  Both required tasks scheduled: {[t for t in scheduled_titles3 if t in ('Morning Walk', 'Emergency Vet')]} ✓")
print("Conflict warning test PASSED\n")
owner.remove_task("Emergency Vet")


# ── Test 4: One-time task completion still works ──────────────────────────────
print("=== Test 4: Completed one-time task is excluded from schedule ===")
vet_visit.mark_complete()
plan4 = owner.schedule_day()
assert not any(st.task.title == "Vet Checkup" for st in plan4.scheduled_tasks), \
    "Completed vet visit should not appear"
print("  Vet Checkup absent after completion ✓")
print("One-time completion test PASSED\n")
vet_visit.is_complete = False  # reset for further testing


# ── Test 5: sort_by_time still works for free tasks ───────────────────────────
print("=== Test 5: sort_by_time orders free tasks shortest-first ===")
plan5 = owner.schedule_day(sort_by_time=True)
free_scheduled = [st for st in plan5.scheduled_tasks if not st.task.time]
required_durations = [st.task.duration_minutes for st in free_scheduled if st.task.is_required]
assert required_durations == sorted(required_durations), \
    f"Required free tasks should be shortest-first: {required_durations}"
print(f"  Free required task durations (shortest-first): {required_durations} ✓")
print("sort_by_time test PASSED")
