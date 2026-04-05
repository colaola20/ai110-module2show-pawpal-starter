# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.


### Smart Scheduling
- An one-time task has to be mark complete by the owner in order to be complete hance scheduling a task isn't equivalent to its completion.
- Owner can filter tasks by pets before scheduling.
- Owners can sort tasks by task's duration before scheduling.
- If multiple required tasks are scheduled at the same time, the scheduler will produce a warning.
- If tasks aren't required and tasks' duration are exceeded owner availabilities, these tasks will be pushed to the next day.

### Testing PawPal+
- To run pytest: python -m pytest


Tests include:
- Testing mark as complete functionality for different types of tasks (one-time or daily/weekly)
- Testing that required tasks are scheduled even if the time exceeds owner's time availability.
- Testing that optional task are skipped when the time exceeds owner's time availability.
- Testing that complete tasks are excluded from feature scheduling.
- Testing that incomlete one-time tasks are included in the scheduling.
- Tetsing that optional tasks are bumped out when the time slot are being used for required tasks.
- Testing that all required tasks which have the same start time are being scheduled with a warning.
- Testing that optional tasks are being scheduled if there a time left over.
- Testing if owner time preferences work for tasks that don't have a specific start time.
- Testing multiple preferences setting for an owner.
- Testing unrecognized owner's preferences.
- Testing adding test count functionality