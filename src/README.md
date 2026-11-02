# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- View schedules, participant lists, and remaining capacity
- Allow teachers to sign students up for or unregister them from activities
- Let visitors view activities and participants without changing registrations

## Teacher Access

Create a teacher account before starting the application:

```bash
python -m src.manage_teachers teacher
```

The command prompts for a password and stores only a salted password hash in
`src/teachers.json`. That file is ignored by Git and must not be committed.
The app uses an HTTP-only session cookie that expires after 12 hours. Set a
stable `SESSION_SECRET` environment variable when running multiple workers or
when sessions should remain valid after an application restart. Without it,
sessions are invalidated when the app process restarts.

Activity reads remain public. Signup and unregister requests require a valid
teacher session.

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| GET    | `/auth/me`                                                        | Get the current teacher login status                                |
| POST   | `/auth/login`                                                     | Log in with a teacher username and password                         |
| POST   | `/auth/logout`                                                    | Log out the current teacher                                         |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up a student (teacher login required)                          |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher login required)                    |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity and registration data is stored in memory and resets when the server
restarts. Teacher password hashes are stored in the local `src/teachers.json`
file and persist across restarts.
