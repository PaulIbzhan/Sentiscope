# Sentiscope: Toxicity-Based Comment Analysis & Moderation

## Overview
**Sentiscope** is a full-stack web application that demonstrates real-time sentiment analysis, toxicity detection, and automated moderation workflows for user comments. It integrates hybrid NLP models, custom rule-based filters, dynamic data visualization, and export capabilities in a polished, three-pane interface.

## Features
- **Sentiment & Toxicity Classification**  
  - Seven-level sentiment grading (Highly Positive → Highly Negative) using TextBlob + NLTK VADER  
  - “TMI” detection (phone numbers & email addresses)  
  - “Lewd” detection (custom keyword list)  
  - Google Perspective API integration for refined toxicity scoring  

- **Configurable Auto-Delete**  
  - Toggle filters for Negative, TMI, and Lewd content  
  - Instant removal of matching new and existing comments  

- **Bulk Operations**  
  - Delete all comments of a specific category with one click  
  - Clear all comments across all posts  

- **Live Visualization**  
  - Chart.js pie chart showing real-time distribution of all nine sentiment categories  
  - Auto-refresh every five seconds  

- **Data Export**  
  - Download all comments as CSV  
  - Download a multi-sheet Excel workbook with:  
    - **Comments** sheet containing every comment’s metadata  
    - **Percentages** sheet showing the sentiment percentage breakdown  

## Architecture
1. **Frontend** (HTML / CSS / JavaScript / Chart.js)  
   - Three-pane layout: Sidebar, Main Feed, Control Panel  
   - Dynamic DOM injection & event binding for all create/read/delete operations  
   - Asynchronous REST calls to keep the UI reactive and avoid page reloads  

2. **Backend** (Flask / Python)  
   - In-memory data store (list of posts → each with comments)  
   - RESTful API endpoints for CRUD, filtering, and exports  
   - NLP pipeline: TMI → Lewd → combined polarity → toxicity estimation  

3. **Data Flow**  
   - User action → POST to `/add_comment` → server classification & filtering → updated data returned → client re-renders feed & chart  

## Getting Started

### Prerequisites
- Python 3.8+  
- pip (for Python packages)  
- (Optional) Node.js & npm for front-end tooling  

### Installation
1. **Clone the repository**  
2. **Install Python dependencies**  
   ```bash
   pip install -r requirements.txt
