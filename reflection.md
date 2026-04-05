# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Core actions:
1. Add a Pet — user registers their pet(s) with name, species, age, and any special needs.
2. Add / Manage Care Tasks — user creates tasks (morning walk, feeding, grooming) with a title, duration, priority, required flag, frequency, and which pet the task is for.
3. Generate Today's Schedule — the Owner delegates to a Scheduler, which sorts tasks by priority and fits them into the available time window, always including required tasks.

**Frequency** (enum)
- Values: ONCE, DAILY, WEEKLY — describes how often a task recurs.

**Pet**
- name: str
- species: str
- age: int
- special_needs: list[str]

**Task**
- title: str
- duration_minutes: int
- priority: str — one of "high", "medium", "low" (validated on creation; maps to 3/2/1 for sorting)
- is_required: bool
- frequency: Frequency
- pet: Pet | None — links this task to a specific pet; None means it applies generally

**ScheduledTask** (dataclass — wraps Task with schedule context)
- task: Task
- start_time: str — "HH:MM", 24-hour clock, capped at 23:59
- reason: str — explains why this task was included

**DailyPlan** (holds the generated schedule; can display and explain it)
- scheduled_tasks: list[ScheduledTask]
- skipped_tasks: list[Task]
- total_minutes_used: int
- available_minutes: int
- is_over_budget: bool — True when required tasks push past the available time budget
- display() -> str
- explain() -> str

**Scheduler** (pure scheduling logic, no owner state)
- available_minutes: int
- tasks: list[Task]
- add_task(task)
- generate_plan() -> DailyPlan — sorts tasks, greedily assigns time slots starting at 08:00
- _sort_by_priority() — sorts by (is_required DESC, priority_value DESC)
- _fits_in_time(task, minutes_used) -> bool

**Owner** (entry point; manages pets, tasks, and triggers scheduling)
- name: str
- available_minutes: int
- preferences: list[str] — stored but not yet wired into Scheduler (known gap, see 1b)
- pets: list[Pet] (read-only property)
- add_pet(pet) / add_task(task) / remove_task(title) / edit_task(title, **kwargs)
- set_available_time(minutes)
- schedule_day() -> DailyPlan — creates a Scheduler, feeds it tasks, returns the plan



**b. Design changes**

- Did your design change during implementation?
    Yes.
- If yes, describe at least one change and why you made it.
    The tasks weren't connected to pets which wouldn't work as owner could have mmore than one pets. Owner's preferences were never acounted for in the Scheduler. generate_plan() wasn't checking task's frequency. Required tasks could exceed owner's available time. 
    All changes were required, so the ystem make sense and works correctly.
    

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    Scheduler tries to fit all tasks according to owner's time availabilities. 
    It also considers if a task is required. If it's it will be always included even if it exceeds availibilities. Alghough it'll give warning if so.
    It also tries to fit tasks acording to it's priority. Tasks with high priority will be scheduled first.

- How did you decide which constraints mattered most?
    The way the system is designed, it made sense to rely on owner's time availability and if the task is required first.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
    if the task is required it can exceed owner's time availability. In this case it's a trade off between available time and task urgency.
- Why is that tradeoff reasonable for this scenario?
    Sometime something needs to be done no matter if we have time for it. For example, if a pet is sick, we have to go to the veterinarian even if we don't have time for it.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
