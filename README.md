# EduMind AI

A Flask learning assistant combining study planning, conversational feedback and student progress tracking.

Developed as a BEng Software Engineering final project, EduMind AI brings the study planner, progress dashboard and chatbot into one student workflow. Evaluation questionnaires and a lecturer interface support the research component.

**Technologies**  
Python · Flask · SQLAlchemy · MySQL · Groq

## Run locally

Create a Python virtual environment and install the dependencies with `python -m pip install -r requirements.txt`. Configure `SECRET_KEY`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` and `DB_NAME` for a local MySQL development database. Set `GROQ_API_KEY` to enable AI responses. The scripts in `database/` update an existing schema. With the application schema in place, run `python run.py` and open `http://127.0.0.1:5000`.

The `tests/` directory includes checks for authentication, planner workflows, evaluation and lecturer access.

## Author

Maleesha Dewmina Perera
