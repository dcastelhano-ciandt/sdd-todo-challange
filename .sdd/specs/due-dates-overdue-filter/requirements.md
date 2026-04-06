# Requirements Document

## Introduction

This document defines the requirements for the **Due Dates + Overdue Filter** feature of the Todo App. The feature enables users to assign a deadline (due date) to individual tasks, and provides a dedicated overdue filter that surfaces tasks whose due dates have passed. The goal is to help users stay on top of time-sensitive work by making overdue items visually prominent and easily accessible.

## Requirements

### Requirement 1: Assign Due Date to a Task

**Objective:** As a user, I want to assign an optional due date to any task, so that I can track deadlines and plan my work accordingly.

#### Acceptance Criteria

1. When a user creates a new task, the Todo App shall allow the user to optionally set a due date for that task.
2. When a user views an existing task, the Todo App shall allow the user to add, edit, or remove the due date at any time.
3. When a user selects a due date, the Todo App shall accept dates in a standard calendar format (day, month, year) and reject invalid dates.
4. If a user submits an invalid date value, the Todo App shall display a descriptive error message and prevent saving the task until a valid date is provided or the field is cleared.
5. The Todo App shall store the due date together with the task so that it persists across sessions and page reloads.
6. When a user removes the due date from a task, the Todo App shall save the task without a due date and treat it as having no deadline.

---

### Requirement 2: Display Due Date on Task Items

**Objective:** As a user, I want to see the due date of each task in the task list, so that I can quickly understand which tasks are time-sensitive.

#### Acceptance Criteria

1. While a task has a due date assigned, the Todo App shall display the due date as a formatted, human-readable label on the task item in the task list.
2. While a task does not have a due date, the Todo App shall display no due date label on that task item, without visual clutter.
3. The Todo App shall display due dates in a consistent format throughout the application (e.g., "Apr 10, 2026" or locale-equivalent).

---

### Requirement 3: Overdue Task Detection

**Objective:** As a user, I want the app to automatically detect overdue tasks, so that I am always aware of tasks that have passed their deadline without manual tracking.

#### Acceptance Criteria

1. The Todo App shall consider a task overdue when its due date is earlier than the current date and the task has not been marked as complete.
2. The Todo App shall not consider a completed task overdue, regardless of its due date.
3. While a task is overdue, the Todo App shall apply a distinct visual indicator (such as a color highlight, icon, or label) to that task item to differentiate it from non-overdue tasks.
4. When the current date advances past a task's due date, the Todo App shall update the task's overdue status automatically without requiring a page reload.

---

### Requirement 4: Overdue Filter

**Objective:** As a user, I want to filter the task list to show only overdue tasks, so that I can focus on and address the most urgent outstanding items.

#### Acceptance Criteria

1. The Todo App shall provide a clearly labeled "Overdue" filter option accessible from the task list view.
2. When a user activates the overdue filter, the Todo App shall display only tasks that are both past their due date and not yet completed.
3. When a user deactivates the overdue filter, the Todo App shall restore the full task list according to any other active filter or sort settings.
4. While the overdue filter is active, the Todo App shall display a visible indication that the list is currently filtered.
5. If no overdue tasks exist when the overdue filter is activated, the Todo App shall display an empty state message informing the user that there are no overdue tasks.

---

### Requirement 5: Overdue Count Badge

**Objective:** As a user, I want to see how many overdue tasks I have at a glance, so that I can quickly gauge the urgency of my workload.

#### Acceptance Criteria

1. The Todo App shall display a numeric badge or counter showing the total count of overdue (incomplete, past-due) tasks.
2. When the count of overdue tasks changes (e.g., a task is completed, a due date is edited, or the date advances), the Todo App shall update the overdue count badge immediately.
3. If there are no overdue tasks, the Todo App shall hide the overdue count badge or display zero, without cluttering the interface.

---

### Requirement 6: Due Date Sorting

**Objective:** As a user, I want to sort my task list by due date in ascending or descending order, so that I can prioritize tasks that are due soonest or browse by latest deadline.

#### Acceptance Criteria

1. The Todo App shall provide a "Sort by due date" option in the task list view, with ascending (ASC) and descending (DESC) directions.
2. The Todo App shall apply due date sorting on the backend by accepting a `sort_by=due_date` and `sort_dir=asc|desc` query parameter on the `GET /api/v1/tasks` endpoint, so that sorting is performed at the database level.
3. The Todo App frontend shall send the `sort_by` and `sort_dir` parameters to the API when the user selects a sort option, and re-fetch the task list accordingly.
4. The Todo App shall use ascending order (earliest due date first — oldest tasks come first) as the default sort direction when due date sorting is first activated.
5. When a user selects sort by due date ascending (ASC), the Todo App shall order tasks so that the task with the earliest due date appears first.
6. When a user selects sort by due date descending (DESC), the Todo App shall order tasks so that the task with the latest due date appears first.
7. While sorting by due date, the Todo App shall place tasks without a due date at the end of the list, after all tasks with a due date, in both ASC and DESC directions.
8. When a user removes or changes the sort selection, the Todo App shall revert to the previous or default sort order.

---

### Requirement 7: Accessibility and Usability

**Objective:** As a user, I want due date and overdue indicators to be accessible and understandable, so that I can use the feature effectively regardless of how I interact with the application.

#### Acceptance Criteria

1. The Todo App shall convey overdue status through both color and a non-color indicator (such as an icon or text label), so that the information is accessible to users with color vision deficiencies.
2. The Todo App shall provide an accessible label or tooltip on due date and overdue elements so that screen readers can announce due date information to assistive technology users.
3. The Todo App shall allow a user to set or edit a due date using only keyboard navigation, without requiring pointer device interaction.
