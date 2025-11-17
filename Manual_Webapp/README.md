# Manual Test Web Application

This is a standalone demo application that uses the ParalaX Web Framework.

## Structure

```
Manual_Webapp/
├── main.py                 # Application entry point
├── website/                # Application-specific website folder
│   ├── config.json         # Application configuration
│   ├── auth/               # Authentication data (users, permissions)
│   └── assets/             # Custom application assets
├── demo_support/           # Demo blueprints showcasing framework features
├── flask_session/          # Runtime session data (gitignored)
└── logs/                   # Application logs (gitignored)
```

## Running

From the framework root directory:

```bash
.venv\Scripts\activate
python Manual_Webapp/main.py
```

Or from Manual_Webapp directory:

```bash
cd Manual_Webapp
python main.py
```

Then open http://localhost:5001

## Default Credentials

- **Admin**: username='admin', password='admin'
- **Guest**: username='GUEST', password='' (passwordless)

## Features Demonstrated

- All Displayer components (layouts, forms, tables, charts, etc.)
- Threading and background tasks
- Scheduler functionality
- Authorization and permissions
- File manager
- Settings management
- And more...
