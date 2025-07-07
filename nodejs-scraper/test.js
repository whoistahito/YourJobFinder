/**
 * Test script for Google Jobs Scraper
 */

const GoogleJobsScraper = require('./google-scraper');

async function testScraper() {
    console.log('Testing Google Jobs Scraper...\n');
    
    // Test with simulated mode first to verify the basic structure
    console.log('=== Running tests in simulated mode ===');
    const scraper = new GoogleJobsScraper({
        maxRetries: 2,
        retryDelay: 1000,
        simulatedMode: true
    });
    
    // Test case 1: Basic search
    console.log('=== Test 1: Basic Software Engineer search ===');
    const scraperInput1 = {
        searchTerm: 'software engineer',
        location: 'San Francisco',
        resultsWanted: 5,
        offset: 0
    };
    
    try {
        const results1 = await scraper.scrape(scraperInput1);
        console.log(`Found ${results1.jobs.length} jobs`);
        
        if (results1.jobs.length > 0) {
            console.log('\nSample job:');
            console.log(JSON.stringify(results1.jobs[0], null, 2));
        }
    } catch (error) {
        console.error('Test 1 failed:', error.message);
    }
    
    console.log('\n=== Test 2: Remote work search ===');
    const scraperInput2 = {
        searchTerm: 'data scientist',
        location: 'remote',
        resultsWanted: 3,
        offset: 0
    };
    
    try {
        const results2 = await scraper.scrape(scraperInput2);
        console.log(`Found ${results2.jobs.length} remote jobs`);
        
        if (results2.jobs.length > 0) {
            console.log('\nSample remote job:');
            console.log(JSON.stringify(results2.jobs[0], null, 2));
        }
    } catch (error) {
        console.error('Test 2 failed:', error.message);
    }
    
    console.log('\n=== Test 3: Specific company search ===');
    const scraperInput3 = {
        searchTerm: 'product manager',
        location: 'Mountain View',
        resultsWanted: 2,
        offset: 0
    };
    
    try {
        const results3 = await scraper.scrape(scraperInput3);
        console.log(`Found ${results3.jobs.length} jobs`);
        
        if (results3.jobs.length > 0) {
            console.log('\nSample job:');
            console.log(JSON.stringify(results3.jobs[0], null, 2));
        }
    } catch (error) {
        console.error('Test 3 failed:', error.message);
    }
    
    // Test with real mode (will fail in this environment but shows the structure)
    console.log('\n=== Attempting real mode test (may fail due to network restrictions) ===');
    const realScraper = new GoogleJobsScraper({
        maxRetries: 1,
        retryDelay: 1000,
        simulatedMode: false
    });
    
    try {
        const realResults = await realScraper.scrape({
            searchTerm: 'javascript developer',
            location: 'New York',
            resultsWanted: 1,
            offset: 0
        });
        console.log(`Real mode found ${realResults.jobs.length} jobs`);
    } catch (error) {
        console.log('Real mode test failed (expected in restricted environment):', error.message);
    }
    
    console.log('\nTesting completed!');
}

// Run the test if this file is executed directly
if (require.main === module) {
    testScraper().catch(console.error);
}

module.exports = testScraper;