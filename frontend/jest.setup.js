import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/navigation', () => ({
    useRouter() {
        return {
            push: jest.fn(),
            replace: jest.fn(),
            prefetch: jest.fn(),
            back: jest.fn(),
            forward: jest.fn(),
            refresh: jest.fn(),
        }
    },
    usePathname() {
        return '/'
    },
    useSearchParams() {
        return new URLSearchParams()
    },
}))

// Mock API calls
global.fetch = jest.fn()

// Mock file API
global.File = class MockFile {
    constructor(bits, name, options = {}) {
        this.bits = bits
        this.name = name
        this.size = bits.reduce((acc, bit) => acc + bit.length, 0)
        this.type = options.type || ''
        this.lastModified = Date.now()
    }
}

global.FormData = class MockFormData {
    constructor() {
        this.data = new Map()
    }

    append(key, value) {
        this.data.set(key, value)
    }

    get(key) {
        return this.data.get(key)
    }
}

// Suppress console errors in tests
const originalError = console.error
beforeAll(() => {
    console.error = (...args) => {
        if (
            typeof args[0] === 'string' &&
            args[0].includes('Warning: ReactDOM.render is no longer supported')
        ) {
            return
        }
        originalError.call(console, ...args)
    }
})

afterAll(() => {
    console.error = originalError
})
