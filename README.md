# MediFind 💊
### Medicine Availability & Pharmacy Finder

**Find medicines. Discover pharmacies. Check availability.**

MediFind is a web-based medicine availability and pharmacy finder built with FastAPI and MySQL. It helps customers search for medicines and discover pharmacies that have available stock, while allowing pharmacy owners to manage their inventory through a dedicated dashboard.

---

## ✨ Key Features

### 👤 Customer
- Search medicines by name or generic name.
- View pharmacies that have the requested medicine in stock.
- Check medicine quantity and price.
- View pharmacy address, landmark and contact information.
- Call pharmacies directly.
- Open pharmacy directions using Google Maps.

### 🏪 Pharmacy Owner
- Access a dedicated pharmacy dashboard.
- Add medicines to pharmacy inventory.
- Update available stock quantities.
- Manage medicine prices.

### 🛡️ Administrator
- Manage registered pharmacies.
- Manage medicine information.
- Manage pharmacy owners.
- Oversee platform operations.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Frontend | HTML5, CSS3, JavaScript |
| Templates | Jinja2 |
| Authentication | JWT |
| Server | Uvicorn |

---

## 🏗️ Project Architecture

```text
MediFind/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── security.py
│   │
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── templates/
│
├── static/
│   └── css/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Core Database Entities

- **User:** Stores customer, pharmacy owner and administrator accounts.
- **Pharmacy:** Stores pharmacy details, address and location.
- **Medicine:** Stores medicine names, brands, generic names and other details.
- **PharmacyInventory:** Connects pharmacies with medicines and stores stock quantity and price.

---

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Rashidfadhi/MediFind.git
cd MediFind
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
copy .env.example .env
```

Configure your MySQL database connection and application secret in `.env`, following the variable names in `.env.example`.

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep your actual `.env` file private. Never commit database credentials or secret keys.

### 5. Create the MySQL database

Create a database in MySQL and configure the database connection in your `.env` file.

### 6. Run the application

Load your environment variables into the terminal, then run:

```bash
uvicorn app.main:app --reload
```

### 7. Open MediFind

| Service | URL |
|---|---|
| Homepage | http://127.0.0.1:8000 |
| API Documentation | http://127.0.0.1:8000/docs |
| Admin Login | http://127.0.0.1:8000/web/login |

---

## 🔐 Initial Administrator Setup

Public registration creates customer accounts.

To promote an existing account to administrator, execute the following SQL using your own registered email:

```sql
UPDATE users
SET role = 'admin'
WHERE email = 'your-admin@example.com';
```

Pharmacy owners must register before being assigned to a pharmacy by the administrator.

---

## 🚀 Future Enhancements

- External medicine information API integration.
- Improved location-based pharmacy discovery.
- More advanced medicine search and filtering.
- Inventory update timestamps.
- Improved mobile responsiveness.
- Production deployment and testing.

*These are planned enhancements, not claims about currently implemented functionality.*

---

## 🎯 Project Objective

MediFind aims to simplify the process of finding medicines by connecting customers with local pharmacies through a centralized medicine search and availability platform.

---

## 👨‍💻 Developer

**Rashid Fadhi**

BSc Computer Science

GitHub: https://github.com/Rashidfadhi

---

**MediFind — Making medicine discovery simpler.**