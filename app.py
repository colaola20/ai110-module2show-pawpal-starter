import streamlit as st
from datetime import time as dt_time
from pawpal_system import Frequency, Task, Pet, Owner

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session state initialization ──────────────────────────────────────────────

def _init_state():
    if "owner" not in st.session_state:
        st.session_state.owner = None
    if "pets" not in st.session_state:
        st.session_state.pets = []
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "plan" not in st.session_state:
        st.session_state.plan = None
    if "editing_task_idx" not in st.session_state:
        st.session_state.editing_task_idx = None
    if "editing_pet_idx" not in st.session_state:
        st.session_state.editing_pet_idx = None
    if "new_task_use_time" not in st.session_state:
        st.session_state.new_task_use_time = False

_init_state()


# ── Header ────────────────────────────────────────────────────────────────────

st.title("🐾 PawPal+")
st.caption("Your daily pet care planning assistant")
st.divider()

# ── Layout: two main columns ───────────────────────────────────────────────────

left, right = st.columns([1, 1], gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN – setup
# ══════════════════════════════════════════════════════════════════════════════

with left:

    # ── Owner setup ──────────────────────────────────────────────────────────
    st.subheader("👤 Owner")

    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.slider(
        "Available time today (minutes)", min_value=15, max_value=480, value=180, step=15
    )
    time_pref = st.selectbox(
        "Preferred start time",
        options=["morning", "afternoon", "evening"],
        help="morning = 8 AM  |  afternoon = 1 PM  |  evening = 5 PM",
    )

    if st.button("💾 Save owner", use_container_width=True):
        st.session_state.owner = Owner(
            name=owner_name,
            available_minutes=available_minutes,
            preferences=[time_pref],
        )
        # Re-attach existing pets and tasks
        for pet in st.session_state.pets:
            st.session_state.owner.add_pet(pet)
        for task in st.session_state.tasks:
            st.session_state.owner.add_task(task)
        st.session_state.plan = None
        st.success(f"Owner **{owner_name}** saved ({available_minutes} min, {time_pref})")

    st.divider()

    # ── Pet management ────────────────────────────────────────────────────────
    st.subheader("🐶 Pets")

    with st.form("add_pet_form", clear_on_submit=True):
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            pet_name = st.text_input("Name", value="Mochi")
        with p_col2:
            pet_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
        with p_col3:
            pet_age = st.number_input("Age", min_value=0, max_value=30, value=2)
        pet_needs = st.text_input(
            "Special needs (comma-separated)", placeholder="e.g. medication, diet"
        )
        add_pet = st.form_submit_button("➕ Add pet", use_container_width=True)

    if add_pet:
        needs = [n.strip() for n in pet_needs.split(",") if n.strip()]
        new_pet = Pet(name=pet_name, species=pet_species, age=pet_age, special_needs=needs)
        st.session_state.pets.append(new_pet)
        if st.session_state.owner:
            st.session_state.owner.add_pet(new_pet)
        st.session_state.plan = None
        st.success(f"Added pet **{pet_name}**")

    if st.session_state.pets:
        for i, pet in enumerate(st.session_state.pets):
            cols = st.columns([3, 1, 1])
            needs_str = ", ".join(pet.special_needs) if pet.special_needs else "none"
            cols[0].markdown(
                f"**{pet.name}** · {pet.species} · age {pet.age} · needs: *{needs_str}*"
            )
            if cols[1].button("✏️", key=f"edit_pet_{i}", help="Edit pet"):
                st.session_state.editing_pet_idx = i
                st.rerun()
            if cols[2].button("🗑️", key=f"del_pet_{i}", help="Remove pet"):
                removed = st.session_state.pets.pop(i)
                # Remove tasks that belonged to this pet
                st.session_state.tasks = [
                    t for t in st.session_state.tasks if t.pet is not removed
                ]
                if st.session_state.editing_pet_idx == i:
                    st.session_state.editing_pet_idx = None
                st.session_state.plan = None
                st.rerun()

            # ── Inline edit form ──────────────────────────────────────────────
            if st.session_state.editing_pet_idx == i:
                with st.form(key=f"edit_pet_form_{i}"):
                    st.markdown(f"**Edit pet: {pet.name}**")
                    ep_col1, ep_col2, ep_col3 = st.columns(3)
                    with ep_col1:
                        new_pet_name = st.text_input("Name", value=pet.name)
                    with ep_col2:
                        new_pet_species = st.selectbox(
                            "Species", ["dog", "cat", "rabbit", "bird", "other"],
                            index=["dog", "cat", "rabbit", "bird", "other"].index(pet.species)
                            if pet.species in ["dog", "cat", "rabbit", "bird", "other"] else 4
                        )
                    with ep_col3:
                        new_pet_age = st.number_input(
                            "Age", min_value=0, max_value=30, value=pet.age
                        )
                    new_pet_needs = st.text_input(
                        "Special needs (comma-separated)",
                        value=", ".join(pet.special_needs) if pet.special_needs else ""
                    )
                    save_col, cancel_col = st.columns(2)
                    save_pet_edit = save_col.form_submit_button("💾 Save changes", use_container_width=True)
                    cancel_pet_edit = cancel_col.form_submit_button("✕ Cancel", use_container_width=True)

                if save_pet_edit:
                    pet.name = new_pet_name
                    pet.species = new_pet_species
                    pet.age = int(new_pet_age)
                    pet.special_needs = [n.strip() for n in new_pet_needs.split(",") if n.strip()]
                    st.session_state.editing_pet_idx = None
                    st.session_state.plan = None
                    st.rerun()

                if cancel_pet_edit:
                    st.session_state.editing_pet_idx = None
                    st.rerun()
    else:
        st.info("No pets yet. Add one above.")

    st.divider()

    # ── Task management ───────────────────────────────────────────────────────
    st.subheader("📋 Tasks")

    pet_options = {p.name: p for p in st.session_state.pets}
    pet_choices = ["(all pets)"] + list(pet_options.keys())

    st.checkbox("Set specific time", key="new_task_use_time")

    with st.form("add_task_form", clear_on_submit=True):
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            task_title = st.text_input("Task title", value="Morning Walk")
            task_duration = st.number_input(
                "Duration (min)", min_value=1, max_value=240, value=20
            )
            task_priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with t_col2:
            task_required = st.checkbox("Required", value=True)
            task_frequency = st.selectbox(
                "Frequency", [f.value for f in Frequency], index=0
            )
            task_pet_name = st.selectbox("Assigned to", pet_choices)
            task_time_pick = st.time_input(
                "Start time", value=dt_time(8, 0),
                disabled=not st.session_state.new_task_use_time
            )

        add_task = st.form_submit_button("➕ Add task", use_container_width=True)

    if add_task:
        assigned_pet = pet_options.get(task_pet_name) if task_pet_name != "(all pets)" else None
        freq = Frequency(task_frequency)
        pinned_time = task_time_pick.strftime("%H:%M") if st.session_state.new_task_use_time else None
        new_task = Task(
            title=task_title,
            duration_minutes=int(task_duration),
            priority=task_priority,
            is_required=task_required,
            frequency=freq,
            pet=assigned_pet,
            time=pinned_time,
        )
        st.session_state.tasks.append(new_task)
        if st.session_state.owner:
            st.session_state.owner.add_task(new_task)
        st.session_state.plan = None
        st.success(f"Added task **{task_title}**")

    if st.session_state.tasks:
        for i, task in enumerate(st.session_state.tasks):
            t_cols = st.columns([4, 1, 1, 1])
            pet_label = f" [{task.pet.name}]" if task.pet else " [all]"
            freq_label = task.frequency.value
            req_label = "required" if task.is_required else "optional"
            status = ""
            if task.frequency == Frequency.ONCE:
                status = " ✅" if task.is_complete else " ⏳"
            time_label = f" · ⏰ {task.time}" if task.time else ""
            t_cols[0].markdown(
                f"**{task.title}**{pet_label} · {task.duration_minutes} min · "
                f"{task.priority} · {freq_label} · {req_label}{time_label}{status}"
            )
            # Mark-complete button for one-time tasks
            if task.frequency == Frequency.ONCE and not task.is_complete:
                if t_cols[1].button("✅", key=f"done_{i}", help="Mark complete"):
                    task.mark_complete()
                    st.session_state.plan = None
                    st.rerun()
            else:
                t_cols[1].empty()

            if t_cols[2].button("✏️", key=f"edit_task_{i}", help="Edit task"):
                st.session_state.editing_task_idx = i
                st.rerun()

            if t_cols[3].button("🗑️", key=f"del_task_{i}", help="Remove task"):
                removed_task = st.session_state.tasks.pop(i)
                if st.session_state.owner:
                    st.session_state.owner.remove_task(removed_task.title)
                if st.session_state.editing_task_idx == i:
                    st.session_state.editing_task_idx = None
                st.session_state.plan = None
                st.rerun()

            # ── Inline edit form ──────────────────────────────────────────────
            if st.session_state.editing_task_idx == i:
                _use_time_key = f"edit_use_time_{i}"
                if _use_time_key not in st.session_state:
                    st.session_state[_use_time_key] = bool(task.time)
                st.checkbox("Set specific time", key=_use_time_key)

                with st.form(key=f"edit_task_form_{i}"):
                    st.markdown(f"**Edit task: {task.title}**")
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        new_title = st.text_input("Task title", value=task.title)
                        new_duration = st.number_input(
                            "Duration (min)", min_value=1, max_value=240,
                            value=task.duration_minutes
                        )
                        new_priority = st.selectbox(
                            "Priority", ["low", "medium", "high"],
                            index=["low", "medium", "high"].index(task.priority)
                        )
                    with e_col2:
                        new_required = st.checkbox("Required", value=task.is_required)
                        new_frequency = st.selectbox(
                            "Frequency", [f.value for f in Frequency],
                            index=[f.value for f in Frequency].index(task.frequency.value)
                        )
                        current_pet_name = task.pet.name if task.pet else "(all pets)"
                        new_pet_name = st.selectbox(
                            "Assigned to", pet_choices,
                            index=pet_choices.index(current_pet_name) if current_pet_name in pet_choices else 0
                        )
                        _existing = dt_time(*map(int, task.time.split(":"))) if task.time else dt_time(8, 0)
                        new_time_pick = st.time_input(
                            "Start time", value=_existing,
                            disabled=not st.session_state[_use_time_key]
                        )
                    save_col, cancel_col = st.columns(2)
                    save_edit = save_col.form_submit_button("💾 Save changes", use_container_width=True)
                    cancel_edit = cancel_col.form_submit_button("✕ Cancel", use_container_width=True)

                if save_edit:
                    task.title = new_title
                    task.duration_minutes = int(new_duration)
                    task.priority = new_priority
                    task.is_required = new_required
                    task.frequency = Frequency(new_frequency)
                    task.pet = pet_options.get(new_pet_name) if new_pet_name != "(all pets)" else None
                    task.time = new_time_pick.strftime("%H:%M") if st.session_state[_use_time_key] else None
                    st.session_state.editing_task_idx = None
                    st.session_state.plan = None
                    st.rerun()

                if cancel_edit:
                    st.session_state.editing_task_idx = None
                    st.rerun()
    else:
        st.info("No tasks yet. Add one above.")


# ══════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN – schedule
# ══════════════════════════════════════════════════════════════════════════════

with right:
    st.subheader("📅 Daily Schedule")

    can_generate = (
        st.session_state.owner is not None and len(st.session_state.tasks) > 0
    )

    if not can_generate:
        st.info("Save an owner and add at least one task, then generate the schedule.")

    sort_by_time = st.checkbox(
        "Sort by time (shortest tasks first)",
        value=False,
        disabled=not can_generate,
        help="When checked, tasks are ordered by duration instead of priority before scheduling.",
    )

    # Pet filter: show tasks for a specific pet (plus unassigned tasks) or all
    filter_pet_choices = ["All pets"] + [p.name for p in st.session_state.pets]
    filter_pet_name = st.selectbox(
        "Filter by pet",
        options=filter_pet_choices,
        disabled=not can_generate,
        help="Schedule only tasks assigned to this pet (plus tasks assigned to all pets).",
    )

    if st.button(
        "⚙️ Generate schedule",
        use_container_width=True,
        disabled=not can_generate,
    ):
        # Rebuild owner to pick up any time/preference changes that weren't saved
        owner = st.session_state.owner
        owner.available_minutes = available_minutes
        owner.preferences = [time_pref]
        # Filter tasks by selected pet before scheduling
        all_tasks = list(st.session_state.tasks)
        if filter_pet_name == "All pets":
            owner.tasks = all_tasks
        else:
            owner.tasks = [
                t for t in all_tasks
                if t.pet is None or t.pet.name == filter_pet_name
            ]
        st.session_state.plan = owner.schedule_day(sort_by_time=sort_by_time)

    plan = st.session_state.plan

    if plan:
        # ── Summary metrics ───────────────────────────────────────────────────
        m1, m2, m3 = st.columns(3)
        m1.metric("Scheduled tasks", len(plan.scheduled_tasks))
        m2.metric("Skipped tasks", len(plan.skipped_tasks))
        budget_pct = min(100, int(plan.total_minutes_used / plan.available_minutes * 100))
        m3.metric(
            "Time used",
            f"{plan.total_minutes_used} / {plan.available_minutes} min",
            delta=f"{budget_pct}%",
            delta_color="inverse" if plan.is_over_budget else "normal",
        )

        if plan.is_over_budget:
            over = plan.total_minutes_used - plan.available_minutes
            st.warning(
                f"⚠️ Schedule exceeds available time by **{over} min** "
                "(required tasks were forced in)"
            )

        for w in plan.warnings:
            st.warning(f"⚠️ {w}")

        st.divider()

        # ── Scheduled tasks ───────────────────────────────────────────────────
        st.markdown("#### Scheduled")
        for st_task in plan.scheduled_tasks:
            pet_label = f"  [{st_task.task.pet.name}]" if st_task.task.pet else ""
            req_badge = "🔴" if st_task.task.is_required else "🟡"
            with st.container():
                c1, c2 = st.columns([1, 3])
                c1.markdown(f"**{st_task.start_time}**")
                c2.markdown(
                    f"{req_badge} **{st_task.task.title}**{pet_label} "
                    f"· {st_task.task.duration_minutes} min  \n"
                    f"_{st_task.reason}_"
                )

        # ── Skipped tasks ─────────────────────────────────────────────────────
        if plan.skipped_tasks:
            st.divider()
            st.markdown("#### Skipped (not enough time)")
            for t in plan.skipped_tasks:
                pet_label = f" [{t.pet.name}]" if t.pet else ""
                st.markdown(f"- **{t.title}**{pet_label} · {t.duration_minutes} min · {t.priority}")

        # ── Raw text output (collapsible) ────────────────────────────────────
        with st.expander("View raw schedule text"):
            st.code(plan.display(), language=None)

        with st.expander("View schedule explanation"):
            st.code(plan.explain(), language=None)
