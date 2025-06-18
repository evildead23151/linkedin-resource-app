# 🚀 Automated LinkedIn Resource Distributor

A full-stack web application that automates the distribution of resources from LinkedIn posts, built to solve a real-world problem of scale and deliver a seamless user experience.

![Project Demo GIF](https://user-images.githubusercontent.com/YOUR_USER_ID/YOUR_IMAGE_ID.gif)
_**(Instruction: Create a short GIF of the app flow and replace the link above. Use a tool like LICEcap or ScreenToGif.)**_

---

## The Problem: Getting Banned on LinkedIn

A few weeks ago, I started sharing valuable tech resources (roadmaps, cheatsheets, etc.) on LinkedIn. The response was incredible, but I was quickly overwhelmed with 50+ DMs asking for links. When I tried to reply to everyone manually, I hit a wall:

> **LinkedIn temporarily banned me from sending messages for "sharing too many links."** 🚫

I realized I needed a scalable system that could handle the demand without getting me flagged.

## The Solution: A Fully Automated System

I built this web application to solve my exact use case. It provides a central, professional-looking hub where users can request and instantly receive resources, completely hands-free.

**Live Demo:**
*   **Frontend:** [linkedin-resource-app1.onrender.com](https://linkedin-resource-app1.onrender.com/)
*   **Admin Panel:** [linkedin-resource-app.onrender.com/admin](https://linkedin-resource-app.onrender.com/admin) (Password Protected)

---

## ✨ Key Features

*   **Sleek Frontend Form:** A modern, responsive interface for users to enter their details.
*   **Automated Email Delivery:** Instantly sends the correct resource link to the user's email upon successful form submission.
*   **Dynamic Resource Management:** A secure, password-protected admin panel to add, edit, and delete LinkedIn posts and their associated resource links.
*   **Data Collection:** All submissions are logged to a persistent cloud database for future reference and analytics.
*   **Scalable Architecture:** Built with separate frontend and backend services, ready to handle growing traffic.

---

## 🛠️ Tech Stack & Architecture

This project was built with a modern, production-ready stack, focusing on free-tier-friendly services.

| Category         | Technology                                                                                                    | Role                                                                  |
| ---------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **Frontend**     | `HTML5`, `Tailwind CSS`, `JavaScript`                                                                         | For a responsive, modern, and interactive user interface.             |
| **Backend**      | `Flask` (Python Framework)                                                                                    | The core engine for handling API requests, business logic, and database interactions. |
| **Database**     | `Neon` (Serverless PostgreSQL)                                                                                | A persistent, scalable cloud database for storing posts and submissions. |
| **Admin Panel**  | `Flask-Admin`                                                                                                 | Provides a secure, auto-generated CRUD interface for managing the database. |
| **Email System** | `smtplib` (Python Standard Library)                                                                           | Connects to Gmail's SMTP server using a secure App Password for email delivery. |
| **Deployment**   | `Render` (Web Service + Static Site), `Gunicorn`                                                              | Hosted as two separate services for optimal performance and scalability. |

### System Architecture Diagram

```
graph TD
    A[User on Browser] -->|Fills Form| B(Frontend on Render Static Site);
    B -->|API Request (fetch)| C(Backend API on Render Web Service);
    subgraph "Admin-Only"
        D[Admin User] -->|Login| E(Secure /admin Panel);
        E -->|CRUD Operations| C;
    end
    C -->|Query/Write| F(Neon PostgreSQL DB);
    F -->|Returns Data| C;
    C -->|Sends Email| G(Gmail SMTP Server);
    C -->|Success/Error Response| B;
    B -->|Displays Message| A;
```

---

## 🚀 Getting Started (Local Setup)

To run this project on your local machine, follow these steps:

**1. Prerequisites:**
*   Python 3.10+
*   Git

**2. Clone the Repository:**
```
git clone https://github.com/evildead23151/linkedin-resource-app.git
cd linkedin-resource-app
```

**3. Set up the Backend:**
```
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install the required packages
pip install -r requirements.txt
```

**4. Configure Environment Variables:**
Create a file named `.env` in the `backend` directory and add the following, filling in your own credentials:
```
# Gmail Credentials
EMAIL_ADDRESS="your_email@gmail.com"
EMAIL_PASSWORD="your_16_digit_google_app_password"

# Admin Panel Credentials
ADMIN_USER="your_admin_username"
ADMIN_PASS="your_secret_admin_password"
```

**5. Initialize the Database & Run the Backend:**
```
# This will create a local database.db file and start the server
python app.py
```
The backend will be running at `http://127.0.0.1:5000`.

**6. Run the Frontend:**
Simply open the `frontend/index.html` file in your web browser. It's already configured to talk to your local backend.

---

## ☁️ Deployment

This application is deployed on **Render** using two separate services on the free tier:
1.  **Web Service:** Runs the Flask/Gunicorn backend.
    *   **Build Command:** `pip install -r backend/requirements.txt`
    *   **Start Command:** `gunicorn --chdir backend app:app`
    *   Connected to the Neon database via a `DATABASE_URL` environment variable.
2.  **Static Site:** Hosts the frontend.
    *   **Publish Directory:** `frontend`
    *   The `index.html` was updated to point its API calls to the live backend URL.

---

## Future Improvements

- [ ] Implement a rate-limiter to prevent API abuse.
- [ ] Add a simple analytics dashboard to the admin panel to track which resources are most popular.
- [ ] Add OAuth for admin login instead of Basic Auth.

---

## Acknowledgment

A huge thanks to **ChatGPT** for acting as a tireless debugging partner and mentor throughout this project. While I wrote and understood every line of code, its support was instrumental in overcoming tricky deployment bugs and refining the architecture.

_This project was built in just a few evenings and stands as a testament to solving your own problems with code._
```
