/**
 * Integration utility for Google Jobs Scraper
 * This module provides integration functions to work with the existing Python job scraper system
 */

const GoogleJobsScraper = require('./google-scraper');

class JobScraperIntegration {
    constructor(options = {}) {
        this.scraper = new GoogleJobsScraper(options);
    }

    /**
     * Scrape jobs with Python-compatible interface
     * @param {Object} params - Search parameters
     * @returns {Array} Array of job objects
     */
    async scrapeJobs(params) {
        const {
            searchTerm,
            location = 'Worldwide',
            jobType = null,
            resultsWanted = 10,
            hoursOld = 120,
            isRemote = false,
            offset = 0
        } = params;

        const scraperInput = {
            searchTerm: searchTerm,
            location: isRemote ? 'remote' : location,
            resultsWanted: resultsWanted,
            offset: offset
        };

        const result = await this.scraper.scrape(scraperInput);
        
        // Transform jobs to match Python format
        return result.jobs.map(job => this.transformJobToPythonFormat(job));
    }

    /**
     * Transform job object to match Python JobPost format
     */
    transformJobToPythonFormat(job) {
        return {
            site: 'google',
            title: job.title,
            company: job.company,
            job_url: job.url,
            location: job.location,
            date_posted: job.datePosted,
            job_type: job.jobType,
            is_remote: job.isRemote,
            description: job.description,
            emails: job.emails,
            min_amount: job.salary?.min || null,
            max_amount: job.salary?.max || null,
            currency: job.salary?.currency || null,
            interval: job.salary?.interval || null
        };
    }

    /**
     * Create a scraper instance compatible with the main.py usage
     */
    static createCompatibleScraper(options = {}) {
        return new JobScraperIntegration(options);
    }
}

/**
 * Main function to be called from Node.js scripts
 * @param {Object} params - Scraping parameters
 * @returns {Promise<Array>} Promise resolving to array of jobs
 */
async function scrapeGoogleJobs(params) {
    const integration = new JobScraperIntegration({
        simulatedMode: params.simulatedMode || false
    });
    
    return await integration.scrapeJobs(params);
}

module.exports = {
    GoogleJobsScraper,
    JobScraperIntegration,
    scrapeGoogleJobs
};