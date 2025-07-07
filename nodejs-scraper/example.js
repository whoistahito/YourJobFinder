#!/usr/bin/env node

/**
 * Example usage of the Google Jobs Scraper
 * 
 * This script demonstrates how to use the Node.js Google Jobs scraper
 * with various search parameters.
 */

const { scrapeGoogleJobs } = require('./integration');

async function main() {
    console.log('Google Jobs Scraper - Example Usage\n');

    // Example 1: Basic search
    console.log('=== Example 1: Basic Software Engineer Jobs ===');
    try {
        const jobs1 = await scrapeGoogleJobs({
            searchTerm: 'software engineer',
            location: 'San Francisco, CA',
            resultsWanted: 5,
            simulatedMode: true // Set to false for real scraping
        });

        console.log(`Found ${jobs1.length} software engineer jobs`);
        if (jobs1.length > 0) {
            console.log('\nFirst job:');
            console.log(`- Title: ${jobs1[0].title}`);
            console.log(`- Company: ${jobs1[0].company}`);
            console.log(`- Location: ${jobs1[0].location}`);
            console.log(`- URL: ${jobs1[0].job_url}`);
            if (jobs1[0].min_amount) {
                console.log(`- Salary: $${jobs1[0].min_amount.toLocaleString()} - $${jobs1[0].max_amount.toLocaleString()} ${jobs1[0].currency}`);
            }
        }
    } catch (error) {
        console.error('Example 1 failed:', error.message);
    }

    console.log('\n' + '='.repeat(50) + '\n');

    // Example 2: Remote jobs
    console.log('=== Example 2: Remote Data Science Jobs ===');
    try {
        const jobs2 = await scrapeGoogleJobs({
            searchTerm: 'data scientist',
            isRemote: true,
            resultsWanted: 3,
            simulatedMode: true
        });

        console.log(`Found ${jobs2.length} remote data science jobs`);
        jobs2.forEach((job, index) => {
            console.log(`\n${index + 1}. ${job.title} at ${job.company}`);
            console.log(`   Location: ${job.location} (Remote: ${job.is_remote})`);
            console.log(`   Posted: ${new Date(job.date_posted).toLocaleDateString()}`);
        });
    } catch (error) {
        console.error('Example 2 failed:', error.message);
    }

    console.log('\n' + '='.repeat(50) + '\n');

    // Example 3: Specific location with job type
    console.log('=== Example 3: Product Manager Jobs in Specific Location ===');
    try {
        const jobs3 = await scrapeGoogleJobs({
            searchTerm: 'product manager',
            location: 'New York, NY',
            jobType: 'full-time',
            resultsWanted: 4,
            simulatedMode: true
        });

        console.log(`Found ${jobs3.length} product manager jobs in New York`);
        
        // Group by company
        const jobsByCompany = jobs3.reduce((acc, job) => {
            if (!acc[job.company]) {
                acc[job.company] = [];
            }
            acc[job.company].push(job);
            return acc;
        }, {});

        console.log('\nJobs by company:');
        Object.entries(jobsByCompany).forEach(([company, companyJobs]) => {
            console.log(`\n${company}: ${companyJobs.length} job(s)`);
            companyJobs.forEach(job => {
                console.log(`  - ${job.title}`);
            });
        });
    } catch (error) {
        console.error('Example 3 failed:', error.message);
    }

    console.log('\n' + '='.repeat(50) + '\n');

    // Example 4: Pagination example
    console.log('=== Example 4: Pagination Demo ===');
    try {
        // Get first 3 jobs (page 1)
        const page1 = await scrapeGoogleJobs({
            searchTerm: 'javascript developer',
            location: 'Seattle, WA',
            resultsWanted: 3,
            offset: 0,
            simulatedMode: true
        });

        // Get next 2 jobs (page 2)
        const page2 = await scrapeGoogleJobs({
            searchTerm: 'javascript developer',
            location: 'Seattle, WA',
            resultsWanted: 2,
            offset: 3,
            simulatedMode: true
        });

        console.log(`Page 1: ${page1.length} jobs`);
        console.log(`Page 2: ${page2.length} jobs`);
        console.log(`Total unique jobs: ${[...page1, ...page2].length}`);

    } catch (error) {
        console.error('Example 4 failed:', error.message);
    }

    console.log('\nExample script completed!');
    console.log('\nTo use with real Google scraping, set simulatedMode to false');
    console.log('Note: Real scraping may be rate-limited and require proxies');
}

// Run the examples
if (require.main === module) {
    main().catch(console.error);
}

module.exports = main;