import {
    formatScore,
    getScoreColor,
    formatFileSize,
    truncateText,
    validateFile,
    formatSimilarity,
} from '@/lib/utils'

describe('Utils', () => {
    describe('formatScore', () => {
        it('formats score with percentage', () => {
            expect(formatScore(85)).toBe('85%')
            expect(formatScore(0)).toBe('0%')
            expect(formatScore(100)).toBe('100%')
        })
    })

    describe('getScoreColor', () => {
        it('returns correct color classes for different score ranges', () => {
            expect(getScoreColor(90)).toBe('text-green-600')
            expect(getScoreColor(80)).toBe('text-green-600')
            expect(getScoreColor(70)).toBe('text-yellow-600')
            expect(getScoreColor(60)).toBe('text-yellow-600')
            expect(getScoreColor(50)).toBe('text-red-600')
            expect(getScoreColor(0)).toBe('text-red-600')
        })
    })

    describe('formatFileSize', () => {
        it('formats bytes correctly', () => {
            expect(formatFileSize(0)).toBe('0 Bytes')
            expect(formatFileSize(1024)).toBe('1 KB')
            expect(formatFileSize(1048576)).toBe('1 MB')
            expect(formatFileSize(1073741824)).toBe('1 GB')
            expect(formatFileSize(500)).toBe('500 Bytes')
            expect(formatFileSize(1536)).toBe('1.5 KB')
        })
    })

    describe('truncateText', () => {
        it('truncates text when longer than max length', () => {
            const longText = 'This is a very long text that should be truncated'
            expect(truncateText(longText, 20)).toBe('This is a very long ...')
        })

        it('returns original text when shorter than max length', () => {
            const shortText = 'Short text'
            expect(truncateText(shortText, 20)).toBe('Short text')
        })

        it('returns original text when exactly max length', () => {
            const text = 'Exactly twenty chars'
            expect(truncateText(text, 20)).toBe('Exactly twenty chars')
        })
    })

    describe('formatSimilarity', () => {
        it('formats similarity as percentage', () => {
            expect(formatSimilarity(0.85)).toBe('85%')
            expect(formatSimilarity(0.0)).toBe('0%')
            expect(formatSimilarity(1.0)).toBe('100%')
            expect(formatSimilarity(0.123)).toBe('12%')
        })
    })

    describe('validateFile', () => {
        it('validates PDF files correctly', () => {
            const pdfFile = new File(['test'], 'resume.pdf', { type: 'application/pdf' })
            const result = validateFile(pdfFile)
            expect(result.valid).toBe(true)
            expect(result.error).toBeUndefined()
        })

        it('validates DOCX files correctly', () => {
            const docxFile = new File(['test'], 'resume.docx', {
                type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            })
            const result = validateFile(docxFile)
            expect(result.valid).toBe(true)
        })

        it('validates image files correctly', () => {
            const imageFile = new File(['test'], 'resume.png', { type: 'image/png' })
            const result = validateFile(imageFile)
            expect(result.valid).toBe(true)
        })

        it('rejects files that are too large', () => {
            // Create a file larger than 10MB
            const largeContent = new Array(11 * 1024 * 1024).fill('x').join('')
            const largeFile = new File([largeContent], 'large.pdf', { type: 'application/pdf' })

            const result = validateFile(largeFile)
            expect(result.valid).toBe(false)
            expect(result.error).toBe('File size must be less than 10MB')
        })

        it('rejects unsupported file types', () => {
            const textFile = new File(['test'], 'resume.txt', { type: 'text/plain' })
            const result = validateFile(textFile)
            expect(result.valid).toBe(false)
            expect(result.error).toBe('File type not supported. Please upload PDF, DOCX, or image files.')
        })
    })
})
