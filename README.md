# FleetFlow

FleetFlow is a full-stack Fleet Management and Logistics System built to manage vehicles, drivers, shipments, trips, fuel records, maintenance, attendance, notifications, and reports from one centralized platform.

The application supports role-based access for Admin, Fleet Manager, Dispatcher, and Driver users. It provides shipment tracking, driver and vehicle assignment, route planning, GPS tracking, fuel monitoring, maintenance reminders, analytics, and PDF/Excel report generation.


## ✨ Features

- JWT-based authentication and role-based access control
- User registration, login, email verification, and profile management
- Vehicle registration, availability, and fleet management
- Driver registration, attendance, licence, and performance tracking
- Shipment creation, assignment, and delivery status tracking
- Trip scheduling, dispatch management, and driver-vehicle allocation
- Route calculation, ETA estimation, and live GPS tracking
- Fuel refill records, mileage tracking, and fuel analytics
- Vehicle maintenance scheduling, service records, and reminders
- Notifications and dashboard analytics
- PDF and Excel report generation

## 🧰 Technology Stack

### Frontend

- React
- Vite
- JavaScript / JSX
- React Router
- Axios
- React Context API
- Leaflet and React Leaflet
- Recharts
- CSS

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- Uvicorn
- JWT Authentication
- Passlib and Bcrypt

### Database and Background Services

- PostgreSQL
- Redis
- Celery
- FastAPI-Mail

### Maps, Routing, and Deployment

- OpenStreetMap
- Nominatim Geocoding
- OSRM Route Service
- Railway
- Git and GitHub

## 📁 Project Structure

```text
FleetFlow/
├── backend/
│   ├── alembic/
│   │   └── versions/              # Database migration files
│   ├── app/
│   │   ├── core/                  # Security and dependencies
│   │   ├── crud/                  # Database operations
│   │   ├── models/                # SQLAlchemy database models
│   │   │   ├── user.py
│   │   │   ├── driver.py
│   │   │   ├── vehicle.py
│   │   │   ├── shipment.py
│   │   │   ├── trip.py
│   │   │   ├── gps_tracking.py
│   │   │   ├── fuel_record.py
│   │   │   ├── maintenance.py
│   │   │   ├── vehicle_maintenance.py
│   │   │   ├── notification.py
│   │   │   └── attendance.py
│   │   ├── routers/               # FastAPI route modules
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── vehicle.py
│   │   │   ├── driver.py
│   │   │   ├── shipment.py
│   │   │   ├── trip.py
│   │   │   ├── gps_tracking.py
│   │   │   ├── maintenance.py
│   │   │   ├── fuel_record.py
│   │   │   ├── attendance.py
│   │   │   ├── analytics.py
│   │   │   ├── reports.py
│   │   │   └── notification.py
│   │   ├── schemas/               # Pydantic request and response schemas
│   │   ├── services/              # Application services
│   │   └── tasks/                 # Celery background tasks
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── celery_app.py
│   ├── mail.py
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/                   # Axios API configuration
│   │   ├── assets/
│   │   ├── components/
│   │   ├── context/               # Authentication context
│   │   ├── layouts/
│   │   ├── pages/                 # Application pages
│   │   ├── routes/                # Protected routes
│   │   ├── services/              # API service functions
│   │   ├── styles/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md
