from dataclasses import dataclass


class Task:
    PRIORITY_VALUES = {"high": 3, "medium": 2, "low": 1}

    def __init__(self, title: str, duration_minutes: int, priority: str, is_required: bool):
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority.lower()
        self.is_required = is_required

    def priority_value(self) -> int:
        return self.PRIORITY_VALUES.get(self.priority, 0)

    def __repr__(self):
        return f"Task({self.title!r}, {self.duration_minutes}min, {self.priority}, required={self.is_required})"


class Pet:
    def __init__(self, name: str, species: str, age: int, special_needs: list[str] = None):
        self.name = name
        self.species = species
        self.age = age
        self.special_needs: list[str] = special_needs or []

    def __repr__(self):
        return f"Pet({self.name!r}, {self.species}, age={self.age})"


@dataclass
class ScheduledTask:
    task: Task
    start_time: str
    reason: str


class DailyPlan:
    def __init__(self, scheduled_tasks: list[ScheduledTask], skipped_tasks: list[Task], total_minutes_used: int):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_minutes_used = total_minutes_used

    def display(self) -> str:
        lines = ["=== Today's PawPal Schedule ==="]
        for st in self.scheduled_tasks:
            lines.append(f"  {st.start_time}  {st.task.title} ({st.task.duration_minutes} min)")
        lines.append(f"\nTotal time: {self.total_minutes_used} min")
        if self.skipped_tasks:
            lines.append("\nSkipped tasks:")
            for t in self.skipped_tasks:
                lines.append(f"  - {t.title}")
        return "\n".join(lines)

    def explain(self) -> str:
        lines = ["=== Schedule Explanation ==="]
        for st in self.scheduled_tasks:
            lines.append(f"  {st.task.title}: {st.reason}")
        if self.skipped_tasks:
            lines.append("\nSkipped (not enough time):")
            for t in self.skipped_tasks:
                lines.append(f"  - {t.title} ({t.duration_minutes} min)")
        return "\n".join(lines)


class Scheduler:
    def __init__(self, available_minutes: int):
        self.available_minutes = available_minutes
        self._tasks: list[Task] = []

    def add_task(self, task: Task):
        self._tasks.append(task)

    def generate_plan(self) -> DailyPlan:
        sorted_tasks = self._sort_by_priority()
        scheduled: list[ScheduledTask] = []
        skipped: list[Task] = []
        minutes_used = 0
        current_hour = 8 * 60  # start at 08:00

        for task in sorted_tasks:
            if task.is_required or self._fits_in_time(task, minutes_used):
                start = f"{current_hour // 60:02d}:{current_hour % 60:02d}"
                reason = "Required task" if task.is_required else f"Priority: {task.priority}"
                scheduled.append(ScheduledTask(task=task, start_time=start, reason=reason))
                minutes_used += task.duration_minutes
                current_hour += task.duration_minutes
            else:
                skipped.append(task)

        return DailyPlan(scheduled, skipped, minutes_used)

    def _sort_by_priority(self) -> list[Task]:
        return sorted(self._tasks, key=lambda t: (t.is_required, t.priority_value()), reverse=True)

    def _fits_in_time(self, task: Task, minutes_used: int) -> bool:
        return minutes_used + task.duration_minutes <= self.available_minutes


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: list[str] = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: list[str] = preferences or []
        self._pets: list[Pet] = []
        self.tasks: list[Task] = []

    def add_pet(self, pet: Pet):
        self._pets.append(pet)

    def add_task(self, task: Task):
        self.tasks.append(task)

    def set_available_time(self, minutes: int):
        self.available_minutes = minutes

    def schedule_day(self) -> DailyPlan:
        scheduler = Scheduler(self.available_minutes)
        for task in self.tasks:
            scheduler.add_task(task)
        return scheduler.generate_plan()

    @property
    def pets(self) -> list[Pet]:
        return list(self._pets)

    def __repr__(self):
        return f"Owner({self.name!r}, {len(self._pets)} pet(s))"
