# AI-Powered Document Processing Bot

A Telegram bot that uses AI to process and generate documents based on user input and uploaded templates.

## Features

- **AI-Powered Document Processing**: Uses GPT-4All for natural language understanding
- **Document Template Management**: Upload and manage document templates
- **Multi-Format Support**: Works with .txt, .docx, and .pdf files
- **Natural Language Interface**: Generate documents using natural language
- **Local Processing**: All processing happens on your machine for privacy

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install spaCy language model:
   ```
   python -m spacy download en_core_web_sm
   ```
4. Create a folder name models and put yours .gguf format ai model file.

5. Paste your Telegram bot taken in `.env` file :
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ```

## Usage

1. Start the bot:
   ```
   python Bot.py
   ```

2. In Telegram:
   - Use `/start` to begin
   - Use `/upload` to upload a document template
   - Use `/ai` to chat with the AI assistant
   - Use `/help` to see available commands

## How It Works

1. **Upload Templates**: Upload document templates in .txt, .docx, or .pdf format
2. **AI Processing**: The bot analyzes the document structure and extracts key fields
3. **Natural Language Queries**: Users can request documents using natural language
4. **Document Generation**: The bot generates customized documents based on user input

## Deployment

### Local Development
1. Follow the setup instructions above
2. Run `python Bot_enhanced.py`

### Railway Deployment
1. Push code to GitHub
2. Connect to Railway (https://railway.app)
3. Set environment variables: `BOT_TOKEN` and `GROQ_API_KEY`
4. Deploy automatically

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## License

MIT
