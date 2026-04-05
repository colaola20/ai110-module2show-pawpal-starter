from pawpal_system import Task, Frequency, Pet, Owner

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
