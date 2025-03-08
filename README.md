# College Fest Management System

A web application for managing college fest events, registrations, and interactive quizzes.

## Features

1. **Event Management**
   - View upcoming events
   - Event registration
   - Capacity tracking
   - Event details and venue information

2. **User System**
   - User registration and authentication
   - User profiles
   - Dashboard with personal activities
   - Admin access for management

3. **Quiz System**
   - Interactive MCQ quizzes
   - Immediate results and scoring
   - Quiz attempt tracking
   - Score history

4. **Announcements**
   - Real-time announcements
   - Priority-based notification system
   - Latest updates on homepage

## Technology Stack

- Backend: Python Flask
- Database: SQLite
- Frontend: HTML, Bootstrap 5
- Authentication: Flask-Login

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/Hackathon_NM.git
   cd Hackathon_NM
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python backend.py
   ```

4. Access the application at `http://localhost:5000`

## Default Admin Account
- Username: admin
- Password: admin123

## Project Structure

- `backend.py`: Main application file with routes and models
- `templates/`: HTML templates
  - `base.html`: Base template with navigation
  - `index.html`: Homepage
  - `events.html`: Events listing
  - `quizzes.html`: Quiz system
  - And more...

## Database Schema

- Users (Authentication and profiles)
- Events (Fest events information)
- EventRegistrations (User event registrations)
- Quizzes (Interactive challenges)
- Questions (Quiz questions and answers)
- Announcements (System notifications)

## Contributing

This project was created as part of a hackathon. Feel free to fork and enhance it further! 