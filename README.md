# 🎯 ATS Résumé Analyzer

An AI-powered résumé analysis tool that helps job seekers optimize their résumés for Applicant Tracking Systems (ATS) and improve their job application success rate.

## ✨ Features

- **📄 Multi-format Support**: Upload PDF, DOCX, or image files
- **🤖 AI-Powered Analysis**: Uses OpenAI GPT-4 for intelligent résumé evaluation
- **📊 Comprehensive Scoring**: Get detailed scores for coverage, experience, and education fit
- **⚠️ ATS Compatibility**: Identifies formatting issues that might cause ATS rejections
- **💡 Actionable Suggestions**: Receive specific recommendations to improve your résumé
- **🎨 Modern UI**: Clean, responsive interface built with Next.js and Tailwind CSS

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** (App Router) with TypeScript
- **Tailwind CSS** for styling
- **React Hook Form** with Zod validation
- **PDF.js** for PDF rendering and preview

### Backend
- **FastAPI** (Python 3.11) with Pydantic v2
- **OpenAI GPT-4** for intelligent analysis
- **spaCy** and **sentence-transformers** for NLP
- **PyMuPDF** and **python-docx** for document parsing
- **SQLAlchemy** with SQLite/PostgreSQL support

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- OpenAI API key

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ats-analyzer.git
   cd ats-analyzer
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Configure environment variables**
   ```bash
   # In the project root, copy the example file
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Start the development servers**
   
   **Backend (Terminal 1):**
   ```bash
   cd backend
   export OPENAI_API_KEY="your-api-key-here"
   source venv/bin/activate
   export PYTHONPATH=/path/to/your/project/backend
   uvicorn ats_analyzer.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   
   **Frontend (Terminal 2):**
   ```bash
   cd frontend
   npm run dev
   ```

6. **Open your browser**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

## 📱 Usage

1. **Upload your résumé** - Support for PDF, DOCX, and image formats
2. **Paste the job description** - Copy the job posting you're applying for
3. **Click "Analyze"** - Get comprehensive analysis in seconds
4. **Review results** - See your scores, missing skills, and improvement suggestions
5. **Optimize and repeat** - Make changes and re-analyze until you're satisfied

## 🏗️ Project Structure

```
ats-analyzer/
├── frontend/                 # Next.js frontend
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities and API client
│   └── public/              # Static assets
├── backend/                 # FastAPI backend
│   ├── ats_analyzer/        # Main application
│   │   ├── api/            # API routes and DTOs
│   │   ├── core/           # Configuration and utilities
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   └── requirements.txt     # Python dependencies
├── vercel.json             # Vercel deployment config
└── DEPLOYMENT.md           # Deployment guide
```

## 🌐 Deployment

This application is ready for deployment on Vercel with both frontend and backend.

### Deploy to Vercel

1. Push your code to GitHub
2. Connect your GitHub repo to Vercel
3. Add environment variables in Vercel dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `ENVIRONMENT`: `production`
4. Deploy!

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `DATABASE_URL` | Database connection string | SQLite |
| `ENVIRONMENT` | Environment (development/production) | development |
| `ALLOWED_ORIGINS` | CORS allowed origins | localhost |
| `MAX_FILE_SIZE` | Maximum upload file size | 10MB |

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests (if added)
cd frontend
npm test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- spaCy for NLP capabilities
- Next.js and FastAPI teams for excellent frameworks
- The open-source community for various libraries used

## 📞 Support

If you encounter any issues or have questions:

1. Check the [DEPLOYMENT.md](DEPLOYMENT.md) guide
2. Look through existing [GitHub Issues](https://github.com/yourusername/ats-analyzer/issues)
3. Create a new issue if needed

---

**Made with ❤️ for job seekers everywhere**
