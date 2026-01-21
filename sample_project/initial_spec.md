# Simple Todo List App

## Overview

A web-based todo list application for managing personal tasks. Clean, simple interface focused on getting things done.

---

## Target Users

- **Individual users** managing personal tasks
- **Students** organizing assignments and deadlines
- **Professionals** tracking work items

**Key user needs:**
- Quick task entry
- Easy task completion
- Simple filtering
- Mobile access

---

## Core Features

### 1. User Authentication

- Email/password registration
- Login with session persistence
- Logout

### 2. Todo Management

**Create todos:**
- Title (required)
- Description (optional)
- Due date (optional)
- Priority: Low, Medium, High

**Edit todos:**
- Update any field
- Save changes

**Delete todos:**
- Remove completed or unwanted todos
- Confirmation before delete

**Complete todos:**
- Mark as complete/incomplete
- Visual indication of completion

### 3. Todo List Display

**List view:**
- Show all todos
- Display: title, due date, priority
- Sort by: date added, due date, priority
- Filter by: all, active, completed

**Counter:**
- Show count: "5 tasks remaining"

### 4. User Interface

**Layout:**
- Clean, minimal design
- Input form at top
- List of todos below
- Filters above list

**Interactions:**
- Click checkbox to complete
- Click task to edit
- Hover effects for actions

**Responsive:**
- Mobile-friendly (phone, tablet)
- Touch-optimized for mobile

---

## Design Requirements

### Accessibility
- WCAG AA compliance
- Keyboard navigation support
- Screen reader friendly
- Focus indicators visible
- Proper heading hierarchy

### Performance
- Fast initial load (<2 seconds)
- Smooth interactions
- No unnecessary re-renders

### Usability
- Intuitive for first-time users
- No tutorial needed
- Clear visual hierarchy
- Obvious call-to-action

---

## Technical Stack

- **Frontend:** React + TypeScript
- **Backend:** Node.js + Express (simple REST API)
- **Database:** SQLite (simple storage)
- **Authentication:** JWT tokens in httpOnly cookies
- **Styling:** CSS (no framework needed for simple app)

---

## Out of Scope

❌ Collaboration features (single-user only)
❌ Subtasks or nested todos
❌ File attachments
❌ Notifications/reminders
❌ Multiple lists/projects

Keep it **simple and focused** on core todo functionality.

---

## Success Criteria

✅ User can create, edit, delete todos
✅ User can mark todos complete
✅ User can filter and sort todos
✅ Works well on mobile
✅ Accessible (WCAG AA)
✅ Fast and responsive
