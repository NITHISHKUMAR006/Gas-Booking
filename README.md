<div align="center">
  <img src="https://placehold.co/1200x400/0f111a/ff6b2b?text=GasBook+LPG+Management" alt="GasBook Cover">

  <h1>⛽ GasBook (LPG Management System)</h1>
  <p>A modern, full-stack application designed to streamline LPG cylinder bookings, inventory management, and customer relations.</p>

  <a href="https://gas.nithishkps.workers.dev" target="_blank">
    <img src="https://img.shields.io/badge/Live_Deployment-GasBook-ff6b2b?style=for-the-badge&logo=vercel" alt="Live Deployment">
  </a>
  <br><br>

  [![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
  [![Flask](https://img.shields.io/badge/Flask-latest-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
  [![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat&logo=mysql&logoColor=white)](https://mysql.com)
  [![Docker](https://img.shields.io/badge/Docker-compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
</div>

<br>

## ✨ Features

GasBook eliminates manual entry and automates the flow of an LPG distribution center.
- **Modern UI/UX:** Gemini-inspired dynamic interface built with vanilla HTML/CSS. Features a 3-dot collapsible sidebar, top-right profile dropdown, responsive design, and CSS variables for theming.
- **Theme Toggle:** Completely interactive Day/Night mode relying on dynamic SVG icons.
- **Customer Management:** Comprehensive CRUD operations to manage, add, and monitor loyal tracking behaviors (like total bookings and revenue spent).
- **Booking & Delivery:** Log new cylinder requests, assign drivers/delivery boys, and visually monitor dispatch states (Pending -> Out for Delivery -> Delivered).
- **Live Inventory:** Automated stock subtraction upon delivered requests. Warns of low-stock and supports instant 1-click refilling/restocking logic.
- **Analytics Dashboard:** Graphical, real-time overview providing summarized sales, revenue, and active orders.

## 🔗 Live Demo
Access the live deployed project here:  
**🌐 [https://gas.nithishkps.workers.dev](https://gas.nithishkps.workers.dev)**

> **Default Credentials:**
> - Username: `admin`  
> - Password: `admin123`

## 🛠️ Technology Stack
- **Frontend:** HTML5, CSS3 (Custom Design System, variables), Javascript (Fetch API, DOM manipulation).
- **Backend:** Python 3, Flask framework.
- **Database:** MySQL 8.
- **Deployment & Architecture:** Docker, Docker Compose, Gunicorn/Werkzeug.

## 🚀 Local Development Setup

To run GasBook natively on your machine, you must have [Docker](https://www.docker.com/) and Docker Compose installed. 

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NITHISHKUMAR006/Gas-Booking-System gasbook
   cd gasbook
   ```

2. **Spin up the Docker Containers:**
   The `docker-compose.yml` file handles both the Flask API and the MySQL database environment cleanly.
   ```bash
   docker-compose up --build -d
   ```

3. **Access the application:**
   The Python bootstrapper handles automatically injecting the default configurations and seeding the tables via `init.sql`. Simply navigate to your browser:
   ```
   http://localhost:5002
   ```

### Option B: Manual Local Run (Without Docker)

If you prefer to run the Flask application directly on your machine without Docker containers, ensure you have Python 3 and a local MySQL server installed.

1. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, you can install them manually: `pip install flask flask-cors python-dotenv mysql-connector-python`)*

2. **Database Setup:**
   - Make sure your local MySQL server is running.
   - You may need to create a database named `gasbook` and grant permissions to a user. Alternatively, ensure the credentials in your `config.env` accurately point to your local MySQL instance (e.g., `MYSQL_HOST=localhost`).
   - The application will attempt to auto-seed tables on startup if they don't exist.

3. **Run the Application:**
   ```bash
   python app.py
   ```
   Access the dashboard at `http://localhost:5002`.

## 📂 Project Structure

```text
📁 Gas-Booking-System/
├── 📁 src/
│   ├── index.html        # Login Page
│   ├── dashboard.html    # Core Application Dashboard
│   └── init.sql          # MySQL Schema & Seed generation
├── app.py                # Main Flask Routing & Controllers
├── config.env            # Environment Variables
├── docker-compose.yml    # Docker configurations
└── Dockerfile            # Container build instructions
```

## 🧑‍💻 Database Self-Healing
GasBook leverages a self-healing logic layer. If the local development MySQL Docker volume initializes before the tables are injected, `app.py` independently verifies the existence of the `users` table and forcefully executes `src/init.sql` upon booting, seamlessly escaping volume conflicts.

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
