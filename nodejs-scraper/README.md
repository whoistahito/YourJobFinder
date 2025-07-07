# Google Jobs Scraper - Node.js Implementation

This is a Node.js implementation of the Google Jobs scraper, ported from the Python version in JobSpy.

## Features

- Scrapes Google Jobs search results
- Handles pagination automatically
- Includes retry logic for failed requests
- Extracts job details including title, company, location, and URL
- Prevents duplicate job listings
- Configurable search parameters

## Installation

1. Navigate to the nodejs-scraper directory:
```bash
cd nodejs-scraper
```

2. Install dependencies:
```bash
npm install
```

## Usage

### Basic Usage

```javascript
const GoogleJobsScraper = require('./google-scraper');

const scraper = new GoogleJobsScraper();

const scraperInput = {
    searchTerm: 'software engineer',
    location: 'San Francisco',
    resultsWanted: 10,
    offset: 0
};

scraper.scrape(scraperInput).then(results => {
    console.log(`Found ${results.jobs.length} jobs`);
    results.jobs.forEach(job => {
        console.log(`${job.title} at ${job.company} in ${job.location}`);
    });
});
```

### Configuration Options

```javascript
const scraper = new GoogleJobsScraper({
    maxRetries: 3,      // Number of retries for failed requests
    retryDelay: 2000,   // Delay between retries in milliseconds
    proxies: null       // Proxy configuration (not implemented yet)
});
```

### Scraper Input Parameters

- `searchTerm` (string): The job title or keywords to search for
- `location` (string): Location to search jobs in (e.g., "San Francisco", "remote")
- `resultsWanted` (number): Number of job results to retrieve (max 900)
- `offset` (number): Starting position for results (for pagination)

## Testing

Run the test script to verify the scraper is working:

```bash
npm test
```

Or run it directly:

```bash
node test.js
```

## Output Format

Each job object contains:

```javascript
{
    title: "Software Engineer",
    company: "Google",
    location: "Mountain View, CA",
    url: "https://careers.google.com/...",
    datePosted: "2024-01-15T10:30:00.000Z",
    description: "",
    jobType: null,
    isRemote: false,
    emails: []
}
```

## Limitations

- This is a simplified implementation focused on core functionality
- Job data extraction is basic and may need refinement for production use
- Google's structure can change, requiring updates to parsing logic
- Rate limiting and anti-bot measures may affect scraping success

## Dependencies

- `axios`: HTTP client for making requests
- `cheerio`: Server-side HTML parsing
- `user-agents`: Random user agent generation

## License

MIT License