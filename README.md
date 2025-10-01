# Dismissal Checker

A Flask web application that helps manage the school dismissal plan, track teacher assignments, and record attendance with automatic warning tracking.

## Features

- Import teacher data from `.xls` files (NUM, Full name, Mobile, Email columns).
- Store dismissal plan assignments for each weekday in a SQLite database.
- View the dismissal plan for any day and record attendance for each assignment.
- Automatically increment or decrement teacher warning counts based on attendance records.
- Review the teacher directory and current warning totals.

## Getting started

### Requirements

- Python 3.11+
- The dependencies listed in `requirements.txt`

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Database setup

The project ships with a dismissal plan stored in `data/dismissal_plan.json`. Load it into the database with the provided Flask CLI command:

```bash
flask --app app:create_app load-plan
```

The first time you run the command, the SQLite database file (`dismissal_checker.db`) will be created automatically.

### Running the application

```bash
flask --app app:create_app run
```

Navigate to <http://127.0.0.1:5000/> to view the current day's plan, import teachers, and record attendance.

### Importing teachers

1. Navigate to **Import Teachers** in the navigation bar.
2. Upload an `.xls` file that contains the teacher roster with the following columns:
   - `NUM`
   - `Full name`
   - `Mobile`
   - `Email`
3. After uploading, the teachers will be stored in the database and automatically linked to the dismissal plan (if names match).

### Recording attendance

1. Open the plan for a specific day.
2. Choose the desired date (defaults to today).
3. Mark each assignment as **Present** or **Absent** and submit the form.
4. Teachers marked absent will have their warning count incremented; removing an absence decreases the warning total.

### Additional CLI utilities

- `flask --app app:create_app clear-attendance` — Remove all attendance records (use `--day` to limit to a specific weekday).
- `flask --app app:create_app today-plan` — Print the assignments scheduled for the current day to the terminal.

## Notes

- The default SQLite database is stored at `dismissal_checker.db` in the project root. Set the `DATABASE_URL` environment variable to use a different database.
- The application accepts classic `.xls` spreadsheets. Ensure your Excel exporter saves in this format or convert as needed.
