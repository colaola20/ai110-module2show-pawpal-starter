# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Core actions: 
1. Add a Pet
    The user can add their pets and information about them like age, species, special needs
2. Add / Manage Care Tasks
    The use can add tasks like moorning walk, feeding, grooming with specific information and possible priority, so they can be scheduled in the today's schedule.
3. Generate Today's Schedule
    The user generates daily care plan based on care tasks, so it's easy to understand and follow along.

┌─────────────────────────────────────────────────────────────────────────┐
│                            PawPal+ UML Design                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐          ┌──────────────────────┐
│        Owner         │          │        Pet           │
├──────────────────────┤          ├──────────────────────┤
│ - name: str          │  1    1+ │ - name: str          │
│ - available_minutes: │◄────────►│ - species: str       │
│   int                │  owns    │ - age: int           │
│ - preferences:       │          │ - special_needs:     │
│   list[str]          │          │   list[str]          │
│ - tasks: list[Task]  │          └──────────────────────┘
├──────────────────────┤
│ + add_pet()          │
│ + add_task()         │
│ + set_available_     │
│   time()             │
│ + schedule_day()     │
└──────────────────────┘
       │          │
       │ manages  │ uses to schedule daily care
       │ (0..*)   │
       ▼          ▼
┌────────────┐   ┌──────────────────────────────────────────┐
│    Task    │   │                Scheduler                 │
├────────────┤   ├──────────────────────────────────────────┤
│ - title:   │   │ - available_minutes: int                 │
│   str      │fed├──────────────────────────────────────────┤
│ - duration_│─► │ + add_task(task: Task)                   │
│   minutes: │   │ + generate_plan() : DailyPlan            │
│   int      │   │ - _sort_by_priority() : list[Task]       │
│ - priority:│   │ - _fits_in_time(task) : bool             │
│   str      │   └──────────────────────────────────────────┘
│ - is_      │            │
│   required:│            │ produces
│   bool     │            ▼
├────────────┤  ┌──────────────────────────────────────────┐
│ + priority_│  │                DailyPlan                 │
│   value()  │  ├──────────────────────────────────────────┤
│   : int    │  │ - scheduled_tasks: list[ScheduledTask]   │
└────────────┘  │ - skipped_tasks: list[Task]              │
                │ - total_minutes_used: int                │
                ├──────────────────────────────────────────┤
                │ + display() : str                        │
                │ + explain() : str                        │
                └──────────────────────────────────────────┘
                            │
                            │ contains
                            ▼
                ┌──────────────────────────────────────────┐
                │             ScheduledTask                │
                ├──────────────────────────────────────────┤
                │ - task: Task                             │
                │ - start_time: str                        │
                │ - reason: str                            │
                └──────────────────────────────────────────┘


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
