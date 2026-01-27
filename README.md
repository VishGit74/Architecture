A simple Flask web application that allows users to look up capital cities by country name and add new country-capital pairs.
Show Image
Show Image
Show Image
Features

Look up capitals - Enter a country name to find its capital city
Add new entries - Add country-capital pairs to expand the database
Browse countries - View all available countries in an expandable list
Click to search - Click any country in the list to instantly look up its capital
Case-insensitive search - "japan", "Japan", and "JAPAN" all work

Tech Stack
ComponentTechnologyBackendPython / FlaskFrontendHTML, CSS, JavaScriptHostingAWS EC2 (Ubuntu)Data StorageIn-memory dictionary (database coming soon)
Project Structure
Architecture/
├── app.py              # Flask application with API routes
├── templates/
│   └── index.html      # Frontend UI
├── .gitignore          # Git ignore rules
└── README.md           # This file
Local Setup
Prerequisites

Python 3.8 or higher
pip (Python package manager)

Installation

Clone the repository

bash   git clone git@github.com:VishGit74/Architecture.git
   cd Architecture

Create a virtual environment (recommended)

bash   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies

bash   pip install flask

Run the application

bash   python app.py

Open in browser

   http://127.0.0.1:5000
EC2 Deployment
Prerequisites

AWS account
EC2 instance running Ubuntu
Security group allowing inbound traffic on port 5000 (or 80)

Deployment Steps

SSH into your EC2 instance

bash   ssh -i your-key.pem ubuntu@your-ec2-public-ip

Update system and install Python

bash   sudo apt update
   sudo apt install python3 python3-pip python3-venv -y

Clone the repository

bash   git clone git@github.com:VishGit74/Architecture.git
   cd Architecture

Set up virtual environment

bash   python3 -m venv venv
   source venv/bin/activate
   pip install flask

Run the application

bash   # For development/testing (accessible externally)
   flask run --host=0.0.0.0 --port=5000

Access the app

   http://your-ec2-public-ip:5000
API Endpoints
MethodEndpointDescriptionRequest BodyGET/Serves the main HTML page-POST/get_capitalReturns capital for a countrycountry (form data)GET/get_countriesReturns list of all countries-POST/add_capitalAdds a new country-capital paircountry, capital (form data)
Example API Usage
Get capital:
bashcurl -X POST http://localhost:5000/get_capital -d "country=Japan"
# Response: {"success": true, "capital": "Tokyo", "country": "Japan"}
Add new country:
bashcurl -X POST http://localhost:5000/add_capital -d "country=Finland&capital=Helsinki"
# Response: {"success": true, "message": "Added Finland with capital Helsinki."}
List all countries:
bashcurl http://localhost:5000/get_countries
# Response: ["United States", "United Kingdom", "France", ...]
Current Limitations

Data is stored in memory and resets when the server restarts
No authentication or rate limiting
Single-server deployment

Roadmap
See Country_Capital_App_Backlog.docx for the full development roadmap, including:

 SQLite database for persistence
 S3 integration for capital city images
 PostgreSQL on RDS
 CI/CD pipeline with GitHub Actions
 API versioning and documentation
 Production deployment with load balancing

Contributing

Create a feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request

License
This project is for learning purposes.
