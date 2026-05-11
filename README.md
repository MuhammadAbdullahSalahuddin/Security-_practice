# 🛡️ Security+ Practice Engine

A self-hosted, full-stack practice exam platform I built after passing the **CompTIA Security+ (SY0-701)** certification. I purchased a set of practice exams during my studies and wanted to make them freely available to anyone preparing for the same exam — because good study material shouldn't sit on a hard drive collecting dust.

Whether you're cramming the night before or building a structured study plan, I hope this helps. **Good luck — you've got this.** 🎯

---

## ✨ Features

- **Practice Mode** — Question-by-question with instant feedback, correct answer highlighting, and detailed explanations after each submission.
- **Exam Mode** — Simulates real exam conditions with a strict 1.5-hour countdown, free navigation between questions, and results only revealed on final submission. 85% to pass, just like the real thing.
- **Randomized Question Order** — Questions are shuffled on every session to prevent pattern memorization.
- **Results Breakdown** — Post-exam review with per-question breakdown, filtering by correct/incorrect, and explanations for every question.
- **Fully Self-Hosted** — No accounts, no tracking, no ads. Just you and the questions.

---

## 🧰 Requirements

Before you begin, make sure you have the following installed:

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started) (with Docker Compose — included in Docker Desktop)

That's it. Everything else (Python, Node.js, MongoDB, Nginx) runs inside containers.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Build and start the services

```bash
docker compose up --build
```

This will:
- Spin up a **MongoDB** instance and persist data in a Docker volume
- Build and run the **FastAPI** backend, seed the database with all practice questions
- Build the **Svelte** frontend and serve it via Nginx

The first build may take a few minutes while Docker pulls base images and installs dependencies.

### 3. Open the app

Once the containers are running, open your browser and navigate to:

```
http://localhost
```

You should see the Security+ Practice Engine home screen with all available practice sets listed.

---

## 🗂️ Project Structure

```
.
├── api/                  # FastAPI backend
│   └── mainapi.py
├── frontend/             # Svelte frontend
│   └── src/
├── quiz_screenshots/     # Practice set data (exam_data.json files)
│   └── Practice_set_1/
│       └── exam_1/
│           └── exam_data.json
├── seed.py               # Seeds MongoDB from the quiz_screenshots directory
├── Dockerfile.api
├── Dockerfile.frontend
├── docker-compose.yaml
└── nginx.conf
```

---

## ➕ Adding Your Own Questions

The app auto-discovers any `exam_data.json` file placed inside a correctly structured directory:

```
quiz_screenshots/
└── <practice_set_name>/
    └── <exam_name>/
        └── exam_data.json
```

Each `exam_data.json` should follow this schema:

```json
{
  "course": "Security+",
  "questions": [
    {
      "question_number": 1,
      "question_text": "Which of the following is an example of multi-factor authentication?",
      "all_options": [
        { "text": "Username and password" },
        { "text": "Password and PIN" },
        { "text": "Password and fingerprint scan" },
        { "text": "Two different passwords" }
      ],
      "correct_indices": [2],
      "explanation": "MFA requires two or more different factor types. A password (knowledge) combined with a fingerprint (biometric/inherence) satisfies this requirement."
    }
  ]
}
```

After adding new files, restart the containers to re-seed the database:

```bash
docker compose down && docker compose up --build
```

---

## 🛑 Stopping the App

```bash
docker compose down
```

To also remove the stored question data (MongoDB volume):

```bash
docker compose down -v
```

---

## 📋 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Svelte + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | MongoDB |
| Reverse Proxy | Nginx |
| Containerization | Docker + Docker Compose |

---

## 🙏 A Note

I passed Security+ and wanted to give back to the community that helped me get there. The practice questions included here are from a set I personally purchased and used during my studies. I'm sharing them freely in the spirit of open learning — not for commercial use.

If this repo helped you pass, drop a ⭐ on GitHub. And if you're still studying — **you'll get there. Good luck!** 💪
