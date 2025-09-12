# AI Document Assistant Bot

A powerful Telegram bot that generates professional documents using AI (Groq API) with automatic data extraction and enhanced PDF formatting.

## 🚀 Features

- **AI-Powered Document Generation**: Uses Groq's Llama3-70B model for intelligent document creation
- **Smart Data Extraction**: Automatically extracts names, addresses, and other details from user input
- **Professional PDF Generation**: Creates formatted PDFs with proper styling, headers, and signatures
- **Multiple Document Types**: Supports affidavits, letters, contracts, certificates, applications, and custom documents
- **Interactive Chat Interface**: Natural language conversation with AI assistant
- **Session Management**: Automatic timeout handling and user state management
- **Cloud Deployment Ready**: Configured for Railway deployment with proper environment handling

## 📋 Supported Document Types

- **Affidavit**: Legal affidavit documents with proper formatting
- **Formal Letter**: Business and official letters with Indian format
- **Contract/Agreement**: Professional contracts with clear terms
- **Certificate**: Official certificates with proper formatting
- **Application Form**: Indian government applications with To/From/Subject structure
- **Custom Document**: Any other document type based on user requirements

## 🛠️ Setup

### Prerequisites
- Python 3.11+
- Telegram Bot Token (from @BotFather)
- Groq API Key (from https://console.groq.com)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Telegram-Bot-main
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Edit `.env` file:
   ```env
   BOT_TOKEN="your_telegram_bot_token_here"
   GROQ_API_KEY="your_groq_api_key_here"
   ```

4. **Run the bot**
   ```bash
   python Bot_enhanced.py
   ```
   
   Or use the batch file (Windows):
   ```bash
   start_bot.bat
   ```

## 🔄 Workflow

### User Journey

```
User starts bot (/start) → Main Menu
                            ├── Chat with AI → General AI Chat → AI Response + PDF
                            ├── Generate Document → Select Document Type → User describes requirements
                            │                                           ↓
                            │                      AI extracts data automatically → Need more info?
                            │                                           ↓              ├── Yes → Ask questions
                            │                      Generate document ←──────────────────┴── No
                            │                                           ↓
                            │                      Send text + Professional PDF
                            └── Help → Show commands and features
```

### Technical Workflow

1. **User Input Processing**
   - Message received and parsed
   - User timer reset for session management
   - Document type determined from context

2. **Data Extraction**
   - Smart regex patterns extract names, addresses
   - Context-aware field mapping
   - Progressive data collection across messages

3. **AI Processing**
   - Groq API integration with Llama3-70B
   - Document-specific system prompts
   - Intelligent content generation

4. **PDF Generation**
   - ReportLab-based professional formatting
   - Automatic header/footer generation
   - Signature sections and proper styling

5. **Response Delivery**
   - Text response for immediate viewing
   - Professional PDF for download
   - Session continuation or menu return

## 💬 Bot Commands

- `/start` - Initialize bot and show main menu
- `/menu` - Return to main menu anytime
- `/help` - Show help information
- `/cancel` - Cancel current operation and restart

## 📱 Usage Examples

### Example 1: Affidavit Generation
```
User: "I need an affidavit for address proof. My name is John Doe, I live at 123 Main Street, New Delhi 110001"

Bot: Generates professional affidavit with:
- Proper legal formatting
- Extracted name and address
- Current date
- Signature section
- Professional PDF output
```

### Example 2: Application Letter
```
User: "Create application for sick leave. I am Sarah Smith, employee ID 12345, need 3 days leave due to fever"

Bot: Creates formal application with:
- To/From/Subject format
- Professional language
- Proper Indian format
- All details included
```

## 🚀 Deployment

### Local Development
```bash
python Bot_enhanced.py
```

### Railway Deployment

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy bot"
   git push origin main
   ```

2. **Deploy on Railway**
   - Connect GitHub repository
   - Set environment variables: `BOT_TOKEN`, `GROQ_API_KEY`
   - Automatic deployment with `Procfile`

3. **Monitor**
   - Check Railway dashboard for logs
   - Test bot with `/start` command

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 📁 Project Structure

```
Telegram-Bot-main/
├── Bot_enhanced.py          # Main bot application
├── requirements.txt         # Python dependencies
├── .env                    # Environment variables
├── Procfile                # Railway deployment config
├── runtime.txt             # Python version specification
├── start_bot.bat           # Windows startup script
├── DEPLOYMENT.md           # Deployment guide
├── generated/              # Generated PDF output directory
└── README.md              # This file
```

## 🔧 Technical Details

### Dependencies
- `python-telegram-bot>=20.0` - Telegram Bot API
- `groq>=0.4.1` - Groq AI API client
- `reportlab>=3.6.0` - PDF generation
- `python-dotenv>=0.19.0` - Environment management
- `requests>=2.25.0` - HTTP requests

### AI Model
- **Model**: Llama3-70B-8192 (via Groq)
- **Temperature**: 0.3 (balanced creativity/accuracy)
- **Max Tokens**: 2000
- **Provider**: Groq Cloud API

### Session Management
- **Timeout**: 10 minutes of inactivity
- **State Persistence**: User data maintained during session
- **Auto-cleanup**: Timers and data cleared on timeout/cancel

## 🔒 Privacy & Security

- All processing happens via secure Groq API
- No data stored permanently on servers
- Generated files are temporary
- Environment variables for sensitive data
- Session-based data handling

## 📄 License

MIT License - Feel free to use and modify for your needs.
