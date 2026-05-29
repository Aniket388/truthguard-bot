# truthguard-bot
Telegram= @TruthGuard0bot

https://truthguard-bot.onrender.com

AI-Powered Fact Checking & Deepfake Detection Platform

Overview

This project is an AI-powered misinformation detection platform designed to help users verify news, identify fake content, and detect AI-generated images through familiar messaging applications such as WhatsApp and Telegram.

The platform combines Large Language Models (LLMs), web search capabilities, and image analysis techniques to provide real-time fact-checking and media verification. Users can simply share a news article, image, screenshot, or question with the bot and receive a detailed analysis indicating whether the content appears factual, misleading, manipulated, or potentially fake.

The primary goal of this project is to make fact-checking accessible to everyone, including people who may not be familiar with search engines, fact-checking websites, or AI tools.

---

Problem Statement

The rapid growth of AI-generated content and the widespread circulation of misinformation on social media have made it increasingly difficult for users to distinguish between authentic and manipulated information.

Traditional fact-checking methods often require users to manually search for sources and verify claims, which can be time-consuming and inaccessible for many people.

This project addresses these challenges by providing an automated, easy-to-use verification system directly inside popular messaging platforms.

---

Features

1. AI-Generated Image Detection

The system analyzes images using convolution-based image processing techniques and machine learning models to determine whether an image is likely:

- AI-generated
- Digitally manipulated
- Authentic

The analysis considers multiple visual patterns and image artifacts commonly found in synthetic media.

---

2. Fact Checking Engine

Users can submit:

- News articles
- Social media posts
- Claims
- Questions about current events

The platform retrieves information from trusted sources using web search and compares evidence across multiple references before generating a response.

---

3. Multi-Modal Input Support

The platform supports:

Text Input

- News articles
- Headlines
- Claims
- User questions

Image Input

- News screenshots
- Social media screenshots
- Infographics
- Photographs

The system extracts relevant information and performs verification automatically.

---

4. Explainable Results

Instead of only providing a verdict, the system also explains:

- Why a claim is likely true or false
- Supporting evidence
- Contradicting evidence
- Confidence level of the prediction

---

5. WhatsApp Integration

Users can verify content directly through WhatsApp by:

1. Sharing text or images.
2. Sending claims for verification.
3. Receiving instant fact-checking results.

This removes the need for dedicated applications or technical knowledge.

---

6. Telegram Integration

Telegram integration provides:

- Instant verification
- Image analysis
- News validation
- Source-backed responses

Users can simply forward content to the bot and receive an analysis.

---

System Architecture

User
   │
   ▼
WhatsApp / Telegram Bot
   │
   ▼
Input Processing Layer
   │
   ├── Text Analysis
   ├── OCR Extraction
   └── Image Processing
   │
   ▼
Verification Engine
   │
   ├── LLM Analysis
   ├── Web Search Retrieval
   ├── Source Comparison
   └── Credibility Scoring
   │
   ▼
Result Generation
   │
   ▼
User Response

---

Technology Stack

Artificial Intelligence

- Large Language Models (LLMs)
- Retrieval-Augmented Generation (RAG)
- Natural Language Processing (NLP)

Computer Vision

- Convolution-based image analysis
- AI-generated image detection
- Image feature extraction

Search & Verification

- Tavily Search API
- Multi-source information retrieval
- Evidence aggregation

Messaging Platforms

- Telegram Bot API
- WhatsApp Business API

Backend

- Python
- FastAPI / Flask
- REST APIs

Database (Optional)

- PostgreSQL
- MongoDB
- SQLite

---

Workflow

News Verification

1. User submits a news article or claim.
2. The system extracts important entities and statements.
3. Tavily Search retrieves supporting information.
4. The LLM compares multiple sources.
5. A credibility score is generated.
6. Final verdict is returned.

---

Image Verification

1. User uploads an image.
2. Image processing pipeline extracts visual features.
3. Detection model analyzes synthetic artifacts.
4. Confidence score is generated.
5. Result is returned as:

- Likely Authentic
- Suspicious
- AI Generated

---

Example Use Cases

Example 1

Input

Government announces free electricity for all citizens.

Output

Verdict: Potentially False

Reason:
No reliable government announcement or trusted news source
supports this claim.

Confidence: 87%

---

Example 2

Input

Image of a celebrity allegedly endorsing a cryptocurrency.

Output

Verdict: AI Generated / Manipulated

Reason:
Detected visual inconsistencies and synthetic generation patterns.

Confidence: 91%

---

Key Advantages

- Easy to use
- Works inside popular messaging apps
- Supports both images and text
- Real-time verification
- Evidence-backed responses
- Reduces misinformation spread
- Accessible to non-technical users

---

Future Improvements

- Video deepfake detection
- Voice cloning detection
- Regional language support
- Multilingual fact-checking
- Browser extension
- Mobile application
- Community reporting system
- Real-time misinformation monitoring

---

Potential Impact

This project aims to make digital information verification accessible to everyone. By integrating advanced AI systems with commonly used communication platforms, users can verify information quickly without requiring technical expertise.

The platform can help:

- Reduce misinformation spread
- Improve media literacy
- Increase trust in verified information
- Provide accessible fact-checking tools for underserved communities

---

Author

Aniket

AI-Powered Fact Checking & Deepfake Detection Platform

Built to make trustworthy information accessible through everyday messaging platforms.t3