# Job Scraper

## Overview

Job Scraper is an automated job search assistant that helps users find relevant job opportunities across multiple job platforms without the hassle of manual searching. The system periodically scrapes job listings from LinkedIn, Indeed, and Google Jobs based on user-defined criteria, filters the results for relevance, and delivers personalized job notifications directly to users' email inboxes.

## Features

- **Multi-platform Scraping**: Collects job listings from LinkedIn, Indeed, and Google Jobs
- **Personalized Job Alerts**: Users can specify job title, location, and job type preferences
- **Smart Filtering**: Uses LLM-based validation to ensure job titles are relevant to user searches
- **Duplicate Prevention**: Tracks previously sent job listings to prevent duplicate notifications
- **Salary Information**: Prioritizes displaying salary information when available
- **Automated Scheduling**: Runs daily job searches automatically
- **User Management**: Simple API for adding and removing job search profiles
- **Welcome Emails**: Sends welcome messages to new users

## Technology Stack

- **Python**: Core programming language
- **Flask**: Web framework for the API endpoints
- **SQLAlchemy**: ORM for database interactions
- **Pandas**: Data manipulation and processing
- **Schedule**: Task scheduling
- **JobSpy**: Custom job scraping module
- **LLM Integration**: For job title and location validation
- **Node.js**: Alternative implementation for Google Jobs scraper

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL or other compatible database
- SMTP server for sending emails

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/whoistahito/Job-Scraper.git
   cd Job-Scraper
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your database:
   - Create a PostgreSQL database
   - Update the `credential.py` file with your database connection details

4. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

### Configuration

Create a `credential.py` file with the following structure:

```python
class Credential:
    def __init__(self):
        self.db_username = "your_db_username"
        self.db_password = "your_db_password"
        self.db_host = "your_db_host"
        self.db_name = "your_db_name"
        self.email_username = "your_email"
        self.email_password = "your_email_password"
        self.email_smtp = "smtp.example.com"
        
    def get_db_uri(self):
        return f"postgresql://{self.db_username}:{self.db_password}@{self.db_host}/{self.db_name}"
```

## Usage

### Running the Application

Start the Flask server:
```
python app.py
```

Start the job scraper service:
```
python main.py
```

### API Endpoints

#### Add a user
```
POST /user
{
  "email": "user@example.com",
  "position": "Software Engineer",
  "location": "Berlin, Germany",
  "jobType": "full-time"
}
```

#### Delete a user
```
DELETE /user
{
  "email": "user@example.com",
  "position": "Software Engineer",
  "location": "Berlin, Germany"
}
```

### Special Search Features

- For remote positions, set location as "remote"
- For working student positions, set job_type as "working student"

## How It Works

1. Users register their job search preferences through the API
2. The system periodically checks for new job listings matching user criteria
3. Job listings are validated for relevance using LLM
4. New, relevant jobs are formatted into HTML email cards
5. Users receive personalized emails with job opportunities
6. The system tracks which jobs have been sent to prevent duplicates

## Additional Components

### Node.js Google Jobs Scraper

A Node.js implementation of the Google Jobs scraper is available in the `nodejs-scraper/` directory. This provides an alternative scraping solution with the following features:

- **Pure Node.js Implementation**: Independent scraper written in JavaScript
- **Simulated Mode**: Testing mode that generates mock job data
- **Compatible Interface**: Designed to work with the existing Python system
- **Comprehensive Examples**: Multiple usage examples and integration patterns

To use the Node.js scraper:

```bash
cd nodejs-scraper
npm install
node example.js
```

See `nodejs-scraper/README.md` for detailed documentation.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/whoistahito/Job-Scraper/issues).

## Acknowledgments

The JobSpy package used in this project is based on the cullenwatson/JobSpy and iw4p/proxy-scraper repository and has been adapted for this project. 

## License

This project is licensed under the MIT License - see the LICENSE file for details.