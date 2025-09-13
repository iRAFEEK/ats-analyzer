import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('ATS Analyzer E2E', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should display the main page correctly', async ({ page }) => {
        // Check main heading
        await expect(page.getByRole('heading', { name: 'ATS Résumé Analyzer' })).toBeVisible();

        // Check privacy indicators
        await expect(page.getByText('Privacy-focused')).toBeVisible();
        await expect(page.getByText('No data stored')).toBeVisible();
        await expect(page.getByText('Instant results')).toBeVisible();

        // Check upload section
        await expect(page.getByText('1. Upload Your Résumé')).toBeVisible();
        await expect(page.getByText('Drop your résumé here')).toBeVisible();

        // Check JD section
        await expect(page.getByText('2. Paste Job Description')).toBeVisible();
        await expect(page.getByPlaceholder('Paste the job description here')).toBeVisible();

        // Check analyze button (should be disabled initially)
        const analyzeButton = page.getByRole('button', { name: /analyze résumé/i });
        await expect(analyzeButton).toBeVisible();
        await expect(analyzeButton).toBeDisabled();
    });

    test('should handle file upload', async ({ page }) => {
        // Create a temporary test file
        const testFilePath = path.join(__dirname, 'fixtures', 'sample-resume.pdf');

        // Upload file
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(testFilePath);

        // Verify file is selected
        await expect(page.getByText('sample-resume.pdf')).toBeVisible();
        await expect(page.getByLabelText('Remove file')).toBeVisible();
    });

    test('should validate job description input', async ({ page }) => {
        const jdTextarea = page.getByPlaceholder('Paste the job description here');

        // Test with short text (should show validation error)
        await jdTextarea.fill('Too short');
        await jdTextarea.blur();

        // The analyze button should still be disabled
        const analyzeButton = page.getByRole('button', { name: /analyze résumé/i });
        await expect(analyzeButton).toBeDisabled();
    });

    test('should enable analyze button when both file and JD are provided', async ({ page }) => {
        // Upload file
        const testFilePath = path.join(__dirname, 'fixtures', 'sample-resume.pdf');
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(testFilePath);

        // Fill job description with sufficient text
        const jdTextarea = page.getByPlaceholder('Paste the job description here');
        await jdTextarea.fill(`
      Senior Software Engineer Position
      
      We are looking for a Senior Software Engineer to join our team.
      
      Required Skills:
      - 5+ years of experience in software development
      - Proficiency in Python, JavaScript, and React
      - Experience with databases like PostgreSQL
      - Knowledge of cloud platforms (AWS preferred)
      - Strong problem-solving skills
      
      Preferred Skills:
      - Experience with Docker and Kubernetes
      - Knowledge of microservices architecture
      - Familiarity with CI/CD pipelines
    `);

        // Analyze button should now be enabled
        const analyzeButton = page.getByRole('button', { name: /analyze résumé/i });
        await expect(analyzeButton).toBeEnabled();
    });

    test('should show loading state during analysis', async ({ page }) => {
        // Mock the API to delay response
        await page.route('**/api/parse', async (route) => {
            await new Promise(resolve => setTimeout(resolve, 2000));
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    text: 'Sample resume text with Python and JavaScript experience',
                    sections: {
                        summary: 'Professional summary',
                        experience: 'Work experience',
                        education: 'Education background',
                        skills: 'Technical skills'
                    },
                    meta: {
                        filetype: 'pdf',
                        has_columns: false,
                        has_tables: false,
                        extractability_score: 0.9,
                        ocr_used: false
                    }
                })
            });
        });

        await page.route('**/api/analyze', async (route) => {
            await new Promise(resolve => setTimeout(resolve, 2000));
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    score: { overall: 85, coverage: 80, experience: 90, education: 85 },
                    missing: { required: ['Docker'], preferred: ['Kubernetes'] },
                    weakly_supported: ['React'],
                    suggestions: [
                        {
                            before: 'Built applications',
                            after: 'Built scalable applications using Docker containers',
                            rationale: 'Add specific technology mentions'
                        }
                    ],
                    ats: {
                        warnings: ['Multi-column layout detected'],
                        passes: ['Standard fonts used', 'Good text density']
                    },
                    evidence: [
                        {
                            skill: 'Python',
                            section: 'experience',
                            quote: 'Developed applications using Python',
                            similarity: 0.9
                        }
                    ]
                })
            });
        });

        // Set up the form
        const testFilePath = path.join(__dirname, 'fixtures', 'sample-resume.pdf');
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(testFilePath);

        const jdTextarea = page.getByPlaceholder('Paste the job description here');
        await jdTextarea.fill('Senior Software Engineer with Python and JavaScript experience required');

        // Click analyze
        const analyzeButton = page.getByRole('button', { name: /analyze résumé/i });
        await analyzeButton.click();

        // Check loading state
        await expect(page.getByText('Processing Document...')).toBeVisible();
        await expect(page.getByText('Parsing Document')).toBeVisible();

        // Wait for analysis to complete
        await expect(page.getByText('Analysis Results')).toBeVisible({ timeout: 10000 });
    });

    test('should display analysis results', async ({ page }) => {
        // Mock successful API responses
        await page.route('**/api/parse', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    text: 'John Doe - Senior Software Engineer with 5 years Python and JavaScript experience',
                    sections: {
                        summary: 'Professional summary',
                        experience: 'Work experience',
                        education: 'Education background',
                        skills: 'Technical skills'
                    },
                    meta: {
                        filetype: 'pdf',
                        has_columns: false,
                        has_tables: false,
                        extractability_score: 0.9,
                        ocr_used: false
                    }
                })
            });
        });

        await page.route('**/api/analyze', async (route) => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    score: { overall: 85, coverage: 80, experience: 90, education: 85 },
                    missing: { required: ['Docker'], preferred: ['Kubernetes'] },
                    weakly_supported: ['React'],
                    suggestions: [],
                    ats: {
                        warnings: ['Multi-column layout detected'],
                        passes: ['Standard fonts used', 'Good text density']
                    },
                    evidence: [
                        {
                            skill: 'Python',
                            section: 'experience',
                            quote: 'Developed applications using Python',
                            similarity: 0.9
                        }
                    ]
                })
            });
        });

        // Set up and submit form
        const testFilePath = path.join(__dirname, 'fixtures', 'sample-resume.pdf');
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(testFilePath);

        const jdTextarea = page.getByPlaceholder('Paste the job description here');
        await jdTextarea.fill('Senior Software Engineer with Python, JavaScript, Docker experience required');

        const analyzeButton = page.getByRole('button', { name: /analyze résumé/i });
        await analyzeButton.click();

        // Wait for and verify results
        await expect(page.getByText('Analysis Results')).toBeVisible();
        await expect(page.getByText('85')).toBeVisible(); // Overall score
        await expect(page.getByText('Skill Coverage')).toBeVisible();
        await expect(page.getByText('Experience Relevance')).toBeVisible();
        await expect(page.getByText('Education Fit')).toBeVisible();

        // Check ATS warnings
        await expect(page.getByText('ATS Compatibility Check')).toBeVisible();
        await expect(page.getByText('Multi-column layout detected')).toBeVisible();
        await expect(page.getByText('Standard fonts used')).toBeVisible();

        // Check evidence panel
        await expect(page.getByText('Skill Evidence & Analysis')).toBeVisible();
        await expect(page.getByText('Docker')).toBeVisible(); // Missing skill
        await expect(page.getByText('Python')).toBeVisible(); // Found skill
    });

    test('should handle API errors gracefully', async ({ page }) => {
        // Mock API error
        await page.route('**/api/parse', async (route) => {
            await route.fulfill({
                status: 400,
                contentType: 'application/json',
                body: JSON.stringify({
                    error: {
                        message: 'Failed to parse document',
                        code: 'PARSE_ERROR'
                    }
                })
            });
        });

        // Set up form
        const testFilePath = path.join(__dirname, 'fixtures', 'sample-resume.pdf');
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(testFilePath);

        const jdTextarea = page.getByPlaceholder('Paste the job description here');
        await jdTextarea.fill('Senior Software Engineer position with required skills');

        const analyzeButton = page.getByRole('button', { name: /analyze résumé/i });
        await analyzeButton.click();

        // Check error state
        await expect(page.getByText('Analysis Failed')).toBeVisible();
        await expect(page.getByText('Failed to parse document')).toBeVisible();
        await expect(page.getByRole('button', { name: /try again/i })).toBeVisible();
    });

    test('should allow resetting the form', async ({ page }) => {
        // Upload file and fill JD
        const testFilePath = path.join(__dirname, 'fixtures', 'sample-resume.pdf');
        const fileInput = page.locator('input[type="file"]');
        await fileInput.setInputFiles(testFilePath);

        const jdTextarea = page.getByPlaceholder('Paste the job description here');
        await jdTextarea.fill('Sample job description with sufficient length for validation');

        // Click reset
        const resetButton = page.getByRole('button', { name: /reset/i });
        await resetButton.click();

        // Verify form is reset
        await expect(page.getByText('sample-resume.pdf')).not.toBeVisible();
        await expect(jdTextarea).toHaveValue('');

        // Analyze button should be disabled again
        const analyzeButton = page.getByRole('button', { name: /analyze résumé/i });
        await expect(analyzeButton).toBeDisabled();
    });
});
