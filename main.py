from pawpal_system import Owner, Pet, Task, Frequency

# --- Create Owner ---
owner = Owner(name="Jordan", available_minutes=180, preferences=["morning"])

# --- Create Pets ---
mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5, special_needs=["medication"])

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Create Tasks (different times, assigned to specific pets) ---
morning_walk = Task(
    title="Morning Walk",
    duration_minutes=30,
    priority="high",
    is_required=True,
    frequency=Frequency.DAILY,
    pet=mochi,
)

feeding = Task(
    title="Feeding",
    duration_minutes=15,
    priority="high",
    is_required=True,
    frequency=Frequency.DAILY,
    pet=None,  # applies to both pets
)

luna_medication = Task(
    title="Luna's Medication",
    duration_minutes=10,
    priority="high",
    is_required=True,
    frequency=Frequency.DAILY,
    pet=luna,
)

grooming = Task(
    title="Grooming Session",
    duration_minutes=45,
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
)

playtime = Task(
    title="Playtime",
    duration_minutes=20,
    priority="low",
    is_required=False,
    frequency=Frequency.DAILY,
    pet=luna,
)

# --- Add Tasks to Owner ---
owner.add_task(morning_walk)
owner.add_task(feeding)
owner.add_task(luna_medication)
owner.add_task(grooming)
owner.add_task(playtime)
owner.add_task(vet_visit)

# --- Generate and Print Today's Schedule (vet visit is pending) ---
print("=== Schedule with pending one-time task ===")
plan = owner.schedule_day()
print(plan.display())
print()
print(plan.explain())

# --- Mark one-time task complete and reschedule ---
print("\n--- Marking 'Vet Checkup' as complete ---")
vet_visit.mark_complete()
print(f"vet_visit.is_complete = {vet_visit.is_complete}")

print("\n=== Schedule after completing one-time task (Vet Checkup should be gone) ===")
plan2 = owner.schedule_day()
print(plan2.display())
