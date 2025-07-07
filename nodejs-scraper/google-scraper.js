/**
 * Google Jobs Scraper - Node.js Implementation
 * 
 * This module contains routines to scrape Google Jobs.
 * Ported from the Python implementation in JobSpy.
 */

const axios = require('axios');
const cheerio = require('cheerio');
const UserAgent = require('user-agents');

class GoogleJobsScraper {
    constructor(options = {}) {
        this.proxies = options.proxies || null;
        this.maxRetries = options.maxRetries || 3;
        this.retryDelay = options.retryDelay || 2000;
        this.jobsPerPage = 10;
        this.seenUrls = new Set();
        this.simulatedMode = options.simulatedMode || false;
        
        // URLs
        this.searchUrl = 'https://www.google.com/search';
        this.jobsUrl = 'https://www.google.com/async/callback:550';
        
        // Headers based on Python implementation
        this.headersInitial = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=0, i',
            'referer': 'https://www.google.com/',
            'sec-ch-prefers-color-scheme': 'dark',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-arch': '"arm"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-form-factors': '"Desktop"',
            'sec-ch-ua-full-version': '"130.0.6723.58"',
            'sec-ch-ua-full-version-list': '"Chromium";v="130.0.6723.58", "Google Chrome";v="130.0.6723.58", "Not?A_Brand";v="99.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"macOS"',
            'sec-ch-ua-platform-version': '"15.0.1"',
            'sec-ch-ua-wow64': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'x-browser-channel': 'stable',
            'x-browser-copyright': 'Copyright 2024 Google LLC. All rights reserved.',
            'x-browser-year': '2024'
        };
        
        this.headersJobs = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=1, i',
            'referer': 'https://www.google.com/',
            'sec-ch-prefers-color-scheme': 'dark',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-arch': '"arm"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-form-factors': '"Desktop"',
            'sec-ch-ua-full-version': '"130.0.6723.58"',
            'sec-ch-ua-full-version-list': '"Chromium";v="130.0.6723.58", "Google Chrome";v="130.0.6723.58", "Not?A_Brand";v="99.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"macOS"',
            'sec-ch-ua-platform-version': '"15.0.1"',
            'sec-ch-ua-wow64': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        };
        
        this.asyncParam = '_basejs:/xjs/_/js/k=xjs.s.en_US.JwveA-JiKmg.2018.O/am=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAACAAAoICAAAAAAAKMAfAAAAIAQAAAAAAAAAAAAACCAAAEJDAAACAAAAAGABAIAAARBAAABAAAAAgAgQAABAASKAfv8JAAABAAAAAAwAQAQACQAAAAAAcAEAQABoCAAAABAAAIABAACAAAAEAAAAFAAAAAAAAAAAAAAAAAAAAAAAAACAQADoBwAAAAAAAAAAAAAQBAAAAATQAAoACOAHAAAAAAAAAQAAAIIAAAA_ZAACAAAAAAAAcB8APB4wHFJ4AAAAAAAAAAAAAAAACECCYA5If0EACAAAAAAAAAAAAAAAAAAAUgRNXG4AMAE/dg=0/br=1/rs=ACT90oGxMeaFMCopIHq5tuQM-6_3M_VMjQ,_basecss:/xjs/_/ss/k=xjs.s.IwsGu62EDtU.L.B1.O/am=QO';
        
        // Set up axios instance
        this.client = axios.create({
            timeout: 15000,
            validateStatus: function (status) {
                return status >= 200 && status < 400;
            }
        });
    }

    /**
     * Main scraping method
     * @param {Object} scraperInput - Job search criteria
     * @returns {Object} JobResponse with jobs array
     */
    async scrape(scraperInput) {
        try {
            console.log(`Starting Google Jobs scrape for: ${scraperInput.searchTerm}`);
            
            // If in simulated mode, return mock data
            if (this.simulatedMode) {
                return this.getSimulatedJobs(scraperInput);
            }
            
            // Limit results
            scraperInput.resultsWanted = Math.min(900, scraperInput.resultsWanted || 10);
            
            // Make initial search request
            const initialResponse = await this.makeInitialRequest(scraperInput);
            if (!initialResponse) {
                console.error('Failed to make initial request');
                return { jobs: [] };
            }
            
            // Extract cursor and initial jobs
            const { forwardCursor, jobs: initialJobs } = this.extractInitialCursorAndJobs(initialResponse.data);
            
            if (!forwardCursor) {
                console.warn('Initial cursor not found, returning initial jobs only');
                return { jobs: initialJobs };
            }
            
            let allJobs = [...initialJobs];
            let currentCursor = forwardCursor;
            let page = 1;
            
            // Paginate through results
            while (this.seenUrls.size < scraperInput.resultsWanted + (scraperInput.offset || 0) && currentCursor) {
                console.log(`Scraping page: ${page} / ${Math.ceil(scraperInput.resultsWanted / this.jobsPerPage)}`);
                
                const { jobs: pageJobs, nextCursor } = await this.getJobsNextPage(currentCursor);
                
                if (pageJobs && pageJobs.length > 0) {
                    allJobs.push(...pageJobs);
                }
                
                currentCursor = nextCursor;
                page++;
                
                // Add delay between requests
                await this.sleep(this.retryDelay);
            }
            
            // Apply offset and limit
            const offset = scraperInput.offset || 0;
            const limitedJobs = allJobs.slice(offset, offset + scraperInput.resultsWanted);
            
            console.log(`Scraping completed. Found ${limitedJobs.length} jobs.`);
            return { jobs: limitedJobs };
            
        } catch (error) {
            console.error('Error during scraping:', error.message);
            return { jobs: [] };
        }
    }

    /**
     * Get simulated job data for testing
     */
    getSimulatedJobs(scraperInput) {
        const baseJobs = [
            {
                title: `Senior ${scraperInput.searchTerm}`,
                company: 'Google',
                location: scraperInput.location || 'Mountain View, CA',
                url: 'https://careers.google.com/jobs/senior-engineer',
                datePosted: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
                description: `Looking for an experienced ${scraperInput.searchTerm} to join our team...`,
                jobType: 'Full-time',
                isRemote: scraperInput.location === 'remote',
                emails: ['jobs@google.com'],
                salary: { min: 150000, max: 250000, currency: 'USD' }
            },
            {
                title: `${scraperInput.searchTerm}`,
                company: 'Microsoft',
                location: scraperInput.location || 'Seattle, WA',
                url: 'https://careers.microsoft.com/jobs/engineer',
                datePosted: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
                description: `Join Microsoft as a ${scraperInput.searchTerm}...`,
                jobType: 'Full-time',
                isRemote: scraperInput.location === 'remote',
                emails: ['careers@microsoft.com'],
                salary: { min: 130000, max: 220000, currency: 'USD' }
            },
            {
                title: `Junior ${scraperInput.searchTerm}`,
                company: 'Apple',
                location: scraperInput.location || 'Cupertino, CA',
                url: 'https://jobs.apple.com/jobs/junior-engineer',
                datePosted: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
                description: `Entry-level ${scraperInput.searchTerm} position at Apple...`,
                jobType: 'Full-time',
                isRemote: scraperInput.location === 'remote',
                emails: ['jobs@apple.com'],
                salary: { min: 120000, max: 180000, currency: 'USD' }
            },
            {
                title: `Lead ${scraperInput.searchTerm}`,
                company: 'Meta',
                location: scraperInput.location || 'Menlo Park, CA',
                url: 'https://careers.meta.com/jobs/lead-engineer',
                datePosted: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
                description: `Leadership role for ${scraperInput.searchTerm} at Meta...`,
                jobType: 'Full-time',
                isRemote: scraperInput.location === 'remote',
                emails: ['careers@meta.com'],
                salary: { min: 180000, max: 300000, currency: 'USD' }
            },
            {
                title: `Contract ${scraperInput.searchTerm}`,
                company: 'Amazon',
                location: scraperInput.location || 'Seattle, WA',
                url: 'https://amazon.jobs/jobs/contract-engineer',
                datePosted: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
                description: `Contract position for ${scraperInput.searchTerm} at Amazon...`,
                jobType: 'Contract',
                isRemote: scraperInput.location === 'remote',
                emails: ['jobs@amazon.com'],
                salary: { min: 100, max: 150, currency: 'USD', interval: 'hourly' }
            }
        ];

        const requestedJobs = baseJobs.slice(0, scraperInput.resultsWanted);
        console.log(`Simulated mode: Generated ${requestedJobs.length} mock jobs`);
        
        return { jobs: requestedJobs };
    }

    /**
     * Make the initial search request to Google
     */
    async makeInitialRequest(scraperInput) {
        const params = {
            q: scraperInput.searchTerm + ' jobs',
            udm: '8'  // Jobs search parameter
        };
        
        if (scraperInput.location) {
            params.q += ` ${scraperInput.location}`;
        }
        
        try {
            const response = await this.client.get(this.searchUrl, {
                params,
                headers: this.headersInitial
            });
            
            return response;
        } catch (error) {
            console.error('Initial request failed:', error.message);
            return null;
        }
    }

    /**
     * Extract initial cursor and jobs from HTML response
     */
    extractInitialCursorAndJobs(htmlText) {
        try {
            // Extract cursor using regex (similar to Python implementation)
            const cursorRegex = /<div jsname="Yust4d"[^>]+data-async-fc="([^"]+)"/;
            const cursorMatch = htmlText.match(cursorRegex);
            const forwardCursor = cursorMatch ? cursorMatch[1] : null;
            
            // Extract initial jobs from HTML
            const jobs = this.findJobInfoInitialPage(htmlText);
            
            return { forwardCursor, jobs };
        } catch (error) {
            console.error('Error extracting initial data:', error.message);
            return { forwardCursor: null, jobs: [] };
        }
    }

    /**
     * Find job information on the initial page
     */
    findJobInfoInitialPage(htmlText) {
        const jobs = [];
        
        try {
            const $ = cheerio.load(htmlText);
            
            // Look for job containers (this is a simplified approach)
            $('[data-ved]').each((index, element) => {
                const $el = $(element);
                const jobData = this.extractJobFromElement($el);
                
                if (jobData && jobData.title && jobData.url) {
                    // Avoid duplicates
                    if (!this.seenUrls.has(jobData.url)) {
                        this.seenUrls.add(jobData.url);
                        jobs.push(jobData);
                    }
                }
            });
            
        } catch (error) {
            console.error('Error finding initial jobs:', error.message);
        }
        
        return jobs;
    }

    /**
     * Extract job data from a DOM element
     */
    extractJobFromElement($element) {
        try {
            // This is a simplified extraction - in practice, Google's structure is complex
            const title = $element.find('h3').first().text().trim();
            const company = $element.find('[data-ved] span').first().text().trim();
            const location = $element.find('[data-ved] span').eq(1).text().trim();
            const url = $element.find('a').first().attr('href');
            
            if (!title || !url) return null;
            
            return {
                title,
                company: company || 'Unknown',
                location: location || 'Unknown',
                url: url.startsWith('http') ? url : `https://www.google.com${url}`,
                datePosted: new Date().toISOString(),
                description: '',
                jobType: null,
                isRemote: false,
                emails: []
            };
        } catch (error) {
            console.error('Error extracting job data:', error.message);
            return null;
        }
    }

    /**
     * Get jobs from next page using cursor
     */
    async getJobsNextPage(forwardCursor) {
        const params = {
            fc: forwardCursor,
            fcv: '3',
            async: this.asyncParam
        };
        
        for (let retry = 0; retry < this.maxRetries; retry++) {
            try {
                const response = await this.client.get(this.jobsUrl, {
                    params,
                    headers: this.headersJobs
                });
                
                if (response.status === 200) {
                    return this.parseJobsFromResponse(response.data);
                }
                
                console.warn(`Got status code ${response.status} when fetching next page`);
                
            } catch (error) {
                console.warn(`Error fetching next page (retry ${retry + 1}/${this.maxRetries}):`, error.message);
                
                if (retry < this.maxRetries - 1) {
                    await this.sleep(this.retryDelay * (retry + 1));
                }
            }
        }
        
        return { jobs: [], nextCursor: null };
    }

    /**
     * Parse jobs from response data
     */
    parseJobsFromResponse(responseText) {
        try {
            // Find JSON data in response (similar to Python implementation)
            const startIdx = responseText.indexOf('[[[');
            const endIdx = responseText.lastIndexOf(']]]') + 3;
            
            if (startIdx === -1 || endIdx <= 2) {
                console.warn('Invalid job data format received');
                return { jobs: [], nextCursor: null };
            }
            
            const jsonString = responseText.substring(startIdx, endIdx);
            
            // Extract next cursor
            const cursorRegex = /data-async-fc="([^"]+)"/;
            const cursorMatch = responseText.match(cursorRegex);
            const nextCursor = cursorMatch ? cursorMatch[1] : null;
            
            // Parse JSON and extract jobs
            const parsed = JSON.parse(jsonString);
            const jobs = [];
            
            if (parsed && parsed[0] && Array.isArray(parsed[0])) {
                for (const array of parsed[0]) {
                    try {
                        if (array && array[1] && typeof array[1] === 'string' && array[1].startsWith('[[[')) {
                            const jobData = JSON.parse(array[1]);
                            const jobInfo = this.findJobInfo(jobData);
                            
                            if (jobInfo) {
                                const jobPost = this.parseJob(jobInfo);
                                if (jobPost && !this.seenUrls.has(jobPost.url)) {
                                    this.seenUrls.add(jobPost.url);
                                    jobs.push(jobPost);
                                }
                            }
                        }
                    } catch (error) {
                        console.error('Error parsing job entry:', error.message);
                    }
                }
            }
            
            return { jobs, nextCursor };
            
        } catch (error) {
            console.error('Error parsing jobs response:', error.message);
            return { jobs: [], nextCursor: null };
        }
    }

    /**
     * Find job info in parsed JSON data (simplified)
     */
    findJobInfo(jobData) {
        // This is a simplified version - the actual structure is quite complex
        // In practice, you'd need to navigate the nested array structure
        try {
            if (Array.isArray(jobData) && jobData.length > 0) {
                return jobData[0]; // Simplified - return first element
            }
        } catch (error) {
            console.error('Error finding job info:', error.message);
        }
        return null;
    }

    /**
     * Parse individual job from job info
     */
    parseJob(jobInfo) {
        try {
            // Simplified job parsing - would need to be more sophisticated
            if (!Array.isArray(jobInfo) || jobInfo.length === 0) {
                return null;
            }
            
            return {
                title: 'Sample Job Title', // Would extract from jobInfo structure
                company: 'Sample Company',
                location: 'Sample Location',
                url: 'https://example.com/job',
                datePosted: new Date().toISOString(),
                description: '',
                jobType: null,
                isRemote: false,
                emails: []
            };
        } catch (error) {
            console.error('Error parsing job:', error.message);
            return null;
        }
    }

    /**
     * Utility method to sleep/delay
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

module.exports = GoogleJobsScraper;