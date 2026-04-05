from dataclasses import dataclass
from enum import Enum


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"


class Task:
    PRIORITY_VALUES = {"high": 3, "medium": 2, "low": 1}
    VALID_PRIORITIES = set(PRIORITY_VALUES.keys())

    def __init__(
        self,
        title: str,
        duration_minutes: int,
        priority: str,
        is_required: bool,
        frequency: Frequency = Frequency.DAILY,
        pet: "Pet | None" = None,
    ):
        if priority.lower() not in self.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{priority}'. Must be one of: {', '.join(sorted(self.VALID_PRIORITIES))}"
            )
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority.lower()
        self.is_required = is_required
        self.frequency = frequency
        self.pet = pet  # links task to a specific pet; None means applies to all pets
        self.is_complete: bool | None = False if frequency == Frequency.ONCE else None

    def mark_complete(self):
        """Mark a one-time task as completed."""
        if self.frequency != Frequency.ONCE:
            raise ValueError(f"mark_complete() is only valid for one-time tasks, but '{self.title}' has frequency '{self.frequency.value}'")
        self.is_complete = True

    def priority_value(self) -> int:
        """Return the numeric priority value for sorting."""
        return self.PRIORITY_VALUES.get(self.priority, 0)

    def __repr__(self):
        """Return a concise string representation of the task."""
        pet_label = f", pet={self.pet.name!r}" if self.pet else ""
        complete_label = f", complete={self.is_complete}" if self.frequency == Frequency.ONCE else ""
        return f"Task({self.title!r}, {self.duration_minutes}min, {self.priority}, required={self.is_required}{pet_label}{complete_label})"


class Pet:
    def __init__(self, name: str, species: str, age: int, special_needs: list[str] = None):
        self.name = name
        self.species = species
        self.age = age
        self.special_needs: list[str] = special_needs or []

    def __repr__(self):
        """Return a concise string representation of the pet."""
        return f"Pet({self.name!r}, {self.species}, age={self.age})"


@dataclass
class ScheduledTask:
    task: Task
    start_time: str  # "HH:MM" format, 24-hour clock
    reason: str


class DailyPlan:
    def __init__(
        self,
        scheduled_tasks: list[ScheduledTask],
        skipped_tasks: list[Task],
        total_minutes_used: int,
        available_minutes: int,
    ):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_minutes_used = total_minutes_used
        self.available_minutes = available_minutes
        self.is_over_budget = total_minutes_used > available_minutes

    def display(self) -> str:
        """Format the daily schedule as a human-readable string."""
        lines = ["=== Today's PawPal Schedule ==="]
        for st in self.scheduled_tasks:
            pet_label = f" [{st.task.pet.name}]" if st.task.pet else ""
            lines.append(f"  {st.start_time}  {st.task.title}{pet_label} ({st.task.duration_minutes} min)")
        lines.append(f"\nTotal time: {self.total_minutes_used} min / {self.available_minutes} min available")
        if self.is_over_budget:
            over = self.total_minutes_used - self.available_minutes
            lines.append(f"  WARNING: Schedule exceeds available time by {over} min (required tasks forced in)")
        if self.skipped_tasks:
            lines.append("\nSkipped tasks:")
            for t in self.skipped_tasks:
                lines.append(f"  - {t.title} ({t.duration_minutes} min)")
        return "\n".join(lines)

    def explain(self) -> str:
        """Return a per-task explanation of why each task was scheduled or skipped."""
        lines = ["=== Schedule Explanation ==="]
        for st in self.scheduled_tasks:
            lines.append(f"  {st.task.title}: {st.reason}")
        if self.skipped_tasks:
            lines.append("\nSkipped (not enough time):")
            for t in self.skipped_tasks:
                lines.append(f"  - {t.title} ({t.duration_minutes} min)")
        return "\n".join(lines)


class Scheduler:
    MAX_CLOCK_MINUTES = 24 * 60  # hard ceiling so start_time stays within a day
    START_HOUR_BY_PREFERENCE = {"morning": 8, "afternoon": 13, "evening": 17}

    def __init__(self, available_minutes: int, start_hour: int = 8):
        self.available_minutes = available_minutes
        self.start_hour = start_hour
        self._tasks: list[Task] = []

    def add_task(self, task: Task):
        """Add a task to the scheduler's task list."""
        self._tasks.append(task)

    def generate_plan(self) -> DailyPlan:
        """Build and return a DailyPlan by scheduling tasks in priority order."""
        sorted_tasks = self._sort_by_priority()
        scheduled: list[ScheduledTask] = []
        skipped: list[Task] = []
        minutes_used = 0
        current_minute = self.start_hour * 60

        for task in sorted_tasks:
            # Skip one-time tasks that have already been completed
            if task.frequency == Frequency.ONCE and task.is_complete:
                continue

            fits = self._fits_in_time(task, minutes_used)

            if task.is_required:
                # Required tasks are always included, but flag if they push past the budget
                reason = "Required task" if fits else "Required task (exceeds available time — must still complete)"
                start = self._format_time(current_minute)
                scheduled.append(ScheduledTask(task=task, start_time=start, reason=reason))
                minutes_used += task.duration_minutes
                current_minute = min(current_minute + task.duration_minutes, self.MAX_CLOCK_MINUTES)
            elif fits:
                start = self._format_time(current_minute)
                scheduled.append(ScheduledTask(task=task, start_time=start, reason=f"Priority: {task.priority}"))
                minutes_used += task.duration_minutes
                current_minute = min(current_minute + task.duration_minutes, self.MAX_CLOCK_MINUTES)
            else:
                skipped.append(task)

        return DailyPlan(scheduled, skipped, minutes_used, self.available_minutes)

    def _sort_by_priority(self) -> list[Task]:
        """Sort tasks required-first, then by descending priority value."""
        # Primary: is_required (True first), secondary: priority_value (high first)
        return sorted(self._tasks, key=lambda t: (t.is_required, t.priority_value()), reverse=True)

    def _fits_in_time(self, task: Task, minutes_used: int) -> bool:
        """Return True if the task fits within the remaining available minutes."""
        return minutes_used + task.duration_minutes <= self.available_minutes

    @staticmethod
    def _format_time(total_minutes: int) -> str:
        """Convert total minutes from midnight to an HH:MM string."""
        hours = (total_minutes // 60) % 24
        mins = total_minutes % 60
        return f"{hours:02d}:{mins:02d}"


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: list[str] = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences: list[str] = preferences or []
        self._pets: list[Pet] = []
        self.tasks: list[Task] = []

    def add_pet(self, pet: Pet):
        """Register a pet with this owner."""
        self._pets.append(pet)

    def add_task(self, task: Task):
        """Add a task to the owner's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str):
        """Remove all tasks with the given title from the owner's task list."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def edit_task(self, title: str, **kwargs):
        """Update one or more attributes of the task matching the given title."""
        for task in self.tasks:
            if task.title == title:
                for key, value in kwargs.items():
                    setattr(task, key, value)
                # Keep is_complete in sync if frequency was changed
                if "frequency" in kwargs:
                    task.is_complete = False if task.frequency == Frequency.ONCE else None
                return
        raise ValueError(f"Task '{title}' not found")

    def set_available_time(self, minutes: int):
        """Update the owner's daily available time budget in minutes."""
        self.available_minutes = minutes

    def _resolve_start_hour(self) -> int:
        """Derive the schedule start hour from the owner's time-of-day preferences."""
        for pref in self.preferences:
            hour = Scheduler.START_HOUR_BY_PREFERENCE.get(pref.lower())
            if hour is not None:
                return hour
        return 8  # default

    def schedule_day(self) -> DailyPlan:
        """Create and return a DailyPlan for all of this owner's tasks."""
        scheduler = Scheduler(self.available_minutes, start_hour=self._resolve_start_hour())
        for task in self.tasks:
            scheduler.add_task(task)
        return scheduler.generate_plan()

    @property
    def pets(self) -> list[Pet]:
        """Return a copy of the owner's pet list."""
        return list(self._pets)

    def __repr__(self):
        """Return a concise string representation of the owner."""
        return f"Owner({self.name!r}, {len(self._pets)} pet(s))"
