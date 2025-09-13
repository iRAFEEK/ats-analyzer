import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FileDrop from '@/components/FileDrop'

// Mock the utils
jest.mock('@/lib/utils', () => ({
    cn: (...args: any[]) => args.filter(Boolean).join(' '),
    formatFileSize: (bytes: number) => `${bytes} bytes`,
    validateFile: (file: File) => ({ valid: true }),
}))

describe('FileDrop', () => {
    const mockOnFileSelect = jest.fn()
    const mockOnFileRemove = jest.fn()

    beforeEach(() => {
        mockOnFileSelect.mockClear()
        mockOnFileRemove.mockClear()
    })

    it('renders upload area when no file selected', () => {
        render(<FileDrop onFileSelect={mockOnFileSelect} />)

        expect(screen.getByText('Drop your résumé here')).toBeInTheDocument()
        expect(screen.getByText('or click to browse files')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument()
    })

    it('shows selected file when file is provided', () => {
        const mockFile = new File(['test'], 'resume.pdf', { type: 'application/pdf' })

        render(
            <FileDrop
                onFileSelect={mockOnFileSelect}
                selectedFile={mockFile}
                onFileRemove={mockOnFileRemove}
            />
        )

        expect(screen.getByText('resume.pdf')).toBeInTheDocument()
        expect(screen.getByLabelText('Remove file')).toBeInTheDocument()
    })

    it('calls onFileSelect when file is selected via input', async () => {
        const user = userEvent.setup()
        render(<FileDrop onFileSelect={mockOnFileSelect} />)

        const mockFile = new File(['test'], 'resume.pdf', { type: 'application/pdf' })
        const input = screen.getByRole('button', { name: /choose file/i }).parentElement?.querySelector('input')

        if (input) {
            await user.upload(input, mockFile)
            expect(mockOnFileSelect).toHaveBeenCalledWith(mockFile)
        }
    })

    it('calls onFileRemove when remove button is clicked', async () => {
        const user = userEvent.setup()
        const mockFile = new File(['test'], 'resume.pdf', { type: 'application/pdf' })

        render(
            <FileDrop
                onFileSelect={mockOnFileSelect}
                selectedFile={mockFile}
                onFileRemove={mockOnFileRemove}
            />
        )

        const removeButton = screen.getByLabelText('Remove file')
        await user.click(removeButton)

        expect(mockOnFileRemove).toHaveBeenCalled()
    })

    it('handles drag and drop events', async () => {
        render(<FileDrop onFileSelect={mockOnFileSelect} />)

        const dropZone = screen.getByText('Drop your résumé here').closest('div')
        const mockFile = new File(['test'], 'resume.pdf', { type: 'application/pdf' })

        if (dropZone) {
            // Simulate drag over
            fireEvent.dragOver(dropZone, {
                dataTransfer: {
                    files: [mockFile],
                },
            })

            // Simulate drop
            fireEvent.drop(dropZone, {
                dataTransfer: {
                    files: [mockFile],
                },
            })

            expect(mockOnFileSelect).toHaveBeenCalledWith(mockFile)
        }
    })

    it('disables interactions when disabled prop is true', () => {
        const mockFile = new File(['test'], 'resume.pdf', { type: 'application/pdf' })

        render(
            <FileDrop
                onFileSelect={mockOnFileSelect}
                selectedFile={mockFile}
                onFileRemove={mockOnFileRemove}
                disabled={true}
            />
        )

        const removeButton = screen.getByLabelText('Remove file')
        expect(removeButton).toBeDisabled()
    })

    it('shows error message for invalid files', () => {
        // Mock validateFile to return invalid
        jest.doMock('@/lib/utils', () => ({
            cn: (...args: any[]) => args.filter(Boolean).join(' '),
            formatFileSize: (bytes: number) => `${bytes} bytes`,
            validateFile: (file: File) => ({ valid: false, error: 'File too large' }),
        }))

        render(<FileDrop onFileSelect={mockOnFileSelect} />)

        const dropZone = screen.getByText('Drop your résumé here').closest('div')
        const mockFile = new File(['test'], 'large-file.pdf', { type: 'application/pdf' })

        if (dropZone) {
            fireEvent.drop(dropZone, {
                dataTransfer: {
                    files: [mockFile],
                },
            })

            // Should not call onFileSelect for invalid file
            expect(mockOnFileSelect).not.toHaveBeenCalled()
        }
    })
})
