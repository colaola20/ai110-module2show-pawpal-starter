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
        time: "str | None" = None,
    ):
        """Initialize a Task, validating priority on construction.

        Args:
            title: Human-readable task name.
            duration_minutes: How long the task takes.
            priority: One of "high", "medium", or "low" (case-insensitive).
            is_required: If True the scheduler always includes this task, even
                when it would bust the time budget.
            frequency: ONCE, DAILY, or WEEKLY.  ONCE tasks expose
                ``is_complete`` and are skipped after ``mark_complete()`` is
                called.
            pet: Optional pet this task is associated with.
            time: Optional pinned start time in "HH:MM" (24-hour).  When set,
                the scheduler anchors the task to that clock slot instead of
                placing it freely.

        Raises:
            ValueError: If ``priority`` is not a recognised value.
        """
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
        self.time = time  # optional pinned start time "HH:MM"; None = scheduler decides
        self.is_complete: bool | None = False if frequency.value == Frequency.ONCE.value else None

    def mark_complete(self):
        """Mark a one-time task as completed."""
        if self.frequency.value != Frequency.ONCE.value:
            raise ValueError(f"mark_complete() is only valid for one-time tasks, but '{self.title}' has frequency '{self.frequency.value}'")
        self.is_complete = True

    def undo_complete(self):
        """Undo completion for a one-time task, marking it as not complete."""
        if self.frequency.value != Frequency.ONCE.value:
            raise ValueError(f"undo_complete() is only valid for one-time tasks, but '{self.title}' has frequency '{self.frequency.value}'")
        self.is_complete = False

    def priority_value(self) -> int:
        """Return the numeric priority value for sorting."""
        return self.PRIORITY_VALUES.get(self.priority, 0)

    def __repr__(self):
        """Return a concise string representation of the task."""
        pet_label = f", pet={self.pet.name!r}" if self.pet else ""
        time_label = f", time={self.time!r}" if self.time else ""
        complete_label = f", complete={self.is_complete}" if self.frequency.value == Frequency.ONCE.value else ""
        return f"Task({self.title!r}, {self.duration_minutes}min, {self.priority}, required={self.is_required}{pet_label}{time_label}{complete_label})"


class Pet:
    def __init__(self, name: str, species: str, age: int, special_needs: list[str] = None):
        """Initialize a Pet.

        Args:
            name: The pet's name.
            species: Species string (e.g. "dog", "cat").
            age: Age in years.
            special_needs: Optional list of care notes (e.g. ["diabetic", "senior diet"]).
        """
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
        warnings: list[str] = None,
    ):
        """Store the output of one scheduling pass.

        Args:
            scheduled_tasks: Ordered list of tasks the scheduler placed on the
                timeline, each paired with a start time and a placement reason.
            skipped_tasks: Tasks that could not fit within the available budget
                or were displaced by a higher-priority pinned task.
            total_minutes_used: Sum of durations for all scheduled tasks.
            available_minutes: The owner's stated daily time budget.
            warnings: Human-readable conflict or over-budget notices generated
                during scheduling.

        Sets ``is_over_budget = True`` when ``total_minutes_used`` exceeds
        ``available_minutes`` (which can happen when required tasks are forced
        in despite no remaining budget).
        """
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.total_minutes_used = total_minutes_used
        self.available_minutes = available_minutes
        self.is_over_budget = total_minutes_used > available_minutes
        self.warnings: list[str] = warnings or []

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
        """Initialize the Scheduler with a time budget and a day start hour.

        Args:
            available_minutes: Total minutes the owner has available for pet
                care tasks in a single day.
            start_hour: Hour (0–23) at which the schedule clock begins.
                Defaults to 8 (8 AM).
        """
        self.available_minutes = available_minutes
        self.start_hour = start_hour
        self._tasks: list[Task] = []

    def add_task(self, task: Task):
        """Add a task to the scheduler's task list."""
        self._tasks.append(task)

    def sort_by_time(self) -> list[Task]:
        """Sort tasks shortest-first, with required tasks before optional ones.

        The composite sort key is ``(not is_required, duration_minutes)`` so
        required tasks bubble to the front and, within each group, shorter
        tasks appear first.  This mirrors the ``use_time_sort=True`` path in
        ``generate_plan``.

        Returns:
            A new sorted list; the internal ``_tasks`` list is not mutated.
        """
        return sorted(self._tasks, key=lambda t: (not t.is_required, t.duration_minutes))

    def generate_plan(self, use_time_sort: bool = False) -> DailyPlan:
        """Build and return a DailyPlan for the current task list.

        Algorithm overview
        ------------------
        1. **Filter** already-completed one-time tasks from the active set.
        2. **Conflict detection** — group pinned tasks (those with a fixed
           ``time``) by slot.  Multiple required tasks in the same slot get a
           warning but are all scheduled; optional tasks at a slot that already
           has a required task are silently displaced to the skipped list.
        3. **Partition** active tasks into *pinned* (anchored to a clock time)
           and *free* (placed wherever budget allows).  Free tasks are sorted
           either by duration ascending (``use_time_sort=True``) or by
           required-first / priority-descending (default).
        4. **Budget reservation** — the full cost of required tasks is
           pre-subtracted so optional tasks only consume what is genuinely
           spare.
        5. **Interleaved placement loop** — advances a ``current_minute``
           cursor through the day:
           - Before each pinned task, as many free tasks as fit in the gap are
             placed via ``_schedule_free``.
           - The pinned task is then anchored at its exact clock time (the
             cursor jumps forward if needed).
           - Required tasks are always scheduled even if they exceed the budget,
             causing ``DailyPlan.is_over_budget`` to be set.
           - After all pinned tasks, any remaining free tasks fill the tail.
        6. Returns a ``DailyPlan`` with the ordered schedule, skipped tasks,
           time totals, and any conflict warnings.

        Args:
            use_time_sort: When True, sort free tasks shortest-first (good for
                maximising the number of tasks completed).  When False (default),
                sort by required-first then descending priority value.

        Returns:
            A ``DailyPlan`` describing what to do, when, and why.
        """
        active = [t for t in self._tasks if not (t.frequency.value == Frequency.ONCE.value and t.is_complete)]

        # Detect conflicts among pinned tasks and resolve them:
        # - Two+ required at the same time → warn, schedule all (required can't be dropped)
        # - Required + optional at the same time → skip the optional silently
        warnings: list[str] = []
        pinned_by_time: dict[str, list[Task]] = {}
        for t in active:
            if t.time:
                pinned_by_time.setdefault(t.time, []).append(t)

        bumped_to_free: set[int] = set()  # ids of optional pinned tasks displaced by a required task
        for time_slot, tasks in pinned_by_time.items():
            required_at_slot = [t for t in tasks if t.is_required]
            optional_at_slot = [t for t in tasks if not t.is_required]
            if len(required_at_slot) > 1:
                names = ", ".join(f"'{t.title}'" for t in required_at_slot)
                warnings.append(
                    f"Conflict at {time_slot}: multiple required tasks scheduled at the same time ({names})"
                )
            if required_at_slot and optional_at_slot:
                # Required wins; optional tasks at this slot are skipped entirely
                for t in optional_at_slot:
                    bumped_to_free.add(id(t))

        # Pinned tasks are anchored to a specific clock time; free tasks fill the gaps
        pinned = sorted(
            [t for t in active if t.time and id(t) not in bumped_to_free],
            key=lambda t: self._time_str_to_minutes(t.time)
        )
        free = [t for t in active if not t.time]
        if use_time_sort:
            free = sorted(free, key=lambda t: (not t.is_required, t.duration_minutes))
        else:
            free = sorted(free, key=lambda t: (t.is_required, t.priority_value()), reverse=True)

        scheduled: list[ScheduledTask] = []
        skipped: list[Task] = [t for t in active if t.time and id(t) in bumped_to_free]
        minutes_used = 0
        current_minute = self.start_hour * 60

        # Reserve budget for all required tasks so optional tasks only use what's left
        total_required_minutes = sum(
            t.duration_minutes for t in active if t.is_required and id(t) not in bumped_to_free
        )
        optional_budget = max(0, self.available_minutes - total_required_minutes)
        optional_minutes_used = 0

        pinned_idx = 0
        free_idx = 0

        def _schedule_free(task: Task) -> bool:
            """Schedule a free task at current_minute. Returns True if scheduled."""
            nonlocal minutes_used, current_minute, optional_minutes_used
            if task.is_required:
                fits = self._fits_in_time(task, minutes_used)
                reason = (
                    "Required task" if fits
                    else "Required task (exceeds available time — must still complete)"
                )
                scheduled.append(ScheduledTask(task=task, start_time=self._format_time(current_minute), reason=reason))
                minutes_used += task.duration_minutes
                current_minute = min(current_minute + task.duration_minutes, self.MAX_CLOCK_MINUTES)
                return True
            # Optional task: only schedule if it fits within the budget left after all required tasks
            if optional_minutes_used + task.duration_minutes <= optional_budget:
                scheduled.append(ScheduledTask(task=task, start_time=self._format_time(current_minute), reason=f"Priority: {task.priority}"))
                minutes_used += task.duration_minutes
                optional_minutes_used += task.duration_minutes
                current_minute = min(current_minute + task.duration_minutes, self.MAX_CLOCK_MINUTES)
                return True
            skipped.append(task)
            return False

        while pinned_idx < len(pinned) or free_idx < len(free):
            next_pinned_start = (
                self._time_str_to_minutes(pinned[pinned_idx].time)
                if pinned_idx < len(pinned) else self.MAX_CLOCK_MINUTES
            )

            # Fill the gap before the next pinned task with free tasks
            while free_idx < len(free):
                task = free[free_idx]
                if current_minute + task.duration_minutes <= next_pinned_start:
                    _schedule_free(task)
                    free_idx += 1
                else:
                    break

            # Schedule the pinned task at its clock time
            if pinned_idx < len(pinned):
                task = pinned[pinned_idx]
                pinned_start = self._time_str_to_minutes(task.time)
                # Jump forward to the pinned time if we're not there yet
                if current_minute < pinned_start:
                    current_minute = pinned_start
                if task.is_required:
                    fits = self._fits_in_time(task, minutes_used)
                    reason = (
                        f"Required task · pinned at {task.time}" if fits
                        else f"Required task · pinned at {task.time} (exceeds available time — must still complete)"
                    )
                    scheduled.append(ScheduledTask(task=task, start_time=task.time, reason=reason))
                    minutes_used += task.duration_minutes
                    current_minute = min(pinned_start + task.duration_minutes, self.MAX_CLOCK_MINUTES)
                elif optional_minutes_used + task.duration_minutes <= optional_budget:
                    scheduled.append(ScheduledTask(task=task, start_time=task.time, reason=f"Priority: {task.priority} · pinned at {task.time}"))
                    minutes_used += task.duration_minutes
                    optional_minutes_used += task.duration_minutes
                    current_minute = min(pinned_start + task.duration_minutes, self.MAX_CLOCK_MINUTES)
                else:
                    skipped.append(task)
                pinned_idx += 1

        # Schedule any remaining free tasks after all pinned tasks
        while free_idx < len(free):
            _schedule_free(free[free_idx])
            free_idx += 1

        return DailyPlan(scheduled, skipped, minutes_used, self.available_minutes, warnings)

    def _sort_by_priority(self) -> list[Task]:
        """Sort tasks required-first, then by descending priority value.

        Uses a single composite key ``(is_required, priority_value)`` sorted in
        reverse so that ``True`` (required) and higher numeric priority both
        sort to the front.  This is the default free-task ordering used by
        ``generate_plan`` when ``use_time_sort=False``.

        Returns:
            A new sorted list; ``_tasks`` is not mutated.
        """
        # Primary: is_required (True first), secondary: priority_value (high first)
        return sorted(self._tasks, key=lambda t: (t.is_required, t.priority_value()), reverse=True)

    def _fits_in_time(self, task: Task, minutes_used: int) -> bool:
        """Return True if the task fits within the remaining available minutes."""
        return minutes_used + task.duration_minutes <= self.available_minutes

    @staticmethod
    def _time_str_to_minutes(time_str: str) -> int:
        """Convert an HH:MM string to total minutes from midnight."""
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    @staticmethod
    def _format_time(total_minutes: int) -> str:
        """Convert total minutes from midnight to an HH:MM string."""
        hours = (total_minutes // 60) % 24
        mins = total_minutes % 60
        return f"{hours:02d}:{mins:02d}"


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: list[str] = None):
        """Initialize an Owner.

        Args:
            name: The owner's display name.
            available_minutes: Daily time budget (minutes) available for pet care.
            preferences: Optional list of scheduling preferences.  The first
                entry that matches a key in ``Scheduler.START_HOUR_BY_PREFERENCE``
                ("morning", "afternoon", "evening") sets the schedule start hour.
        """
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
                    task.is_complete = False if task.frequency.value == Frequency.ONCE.value else None
                return
        raise ValueError(f"Task '{title}' not found")

    def set_available_time(self, minutes: int):
        """Update the owner's daily available time budget in minutes."""
        self.available_minutes = minutes

    def _resolve_start_hour(self) -> int:
        """Derive the schedule start hour from the owner's time-of-day preferences.

        Iterates through ``self.preferences`` in order and returns the hour
        mapped by ``Scheduler.START_HOUR_BY_PREFERENCE`` for the first match
        ("morning" → 8, "afternoon" → 13, "evening" → 17).  Falls back to 8
        if no recognised preference is found.

        Returns:
            Start hour as an integer (0–23).
        """
        for pref in self.preferences:
            hour = Scheduler.START_HOUR_BY_PREFERENCE.get(pref.lower())
            if hour is not None:
                return hour
        return 8  # default

    def schedule_day(self, sort_by_time: bool = False) -> DailyPlan:
        """Create and return a DailyPlan for all of this owner's tasks.

        Constructs a fresh ``Scheduler`` seeded with the owner's time budget
        and preferred start hour, loads every task from ``self.tasks``, then
        delegates to ``Scheduler.generate_plan``.

        Args:
            sort_by_time: Passed through to ``generate_plan``.  When True,
                free tasks are ordered shortest-first; when False (default),
                they are ordered required-first then by descending priority.

        Returns:
            A ``DailyPlan`` ready to display or explain.
        """
        scheduler = Scheduler(self.available_minutes, start_hour=self._resolve_start_hour())
        for task in self.tasks:
            scheduler.add_task(task)
        return scheduler.generate_plan(use_time_sort=sort_by_time)

    @property
    def pets(self) -> list[Pet]:
        """Return a copy of the owner's pet list."""
        return list(self._pets)

    def __repr__(self):
        """Return a concise string representation of the owner."""
        return f"Owner({self.name!r}, {len(self._pets)} pet(s))"
