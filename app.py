from flask import Flask, render_template, request, jsonify, url_for, Response
from textblob import TextBlob
import csv
import json
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import requests
import re
from io import StringIO, BytesIO
import pandas as pd

app = Flask(__name__)

# Google Perspective API Key
PERSPECTIVE_API_KEY = "AIzaSyBNq734U4_QvcRoFi73Z3usULIcur0efe8"
PERSPECTIVE_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"

# Download NLTK's VADER lexicon once
nltk.download('vader_lexicon', quiet=True)
sia = SentimentIntensityAnalyzer()

# In-memory posts + comments
posts = [
    {"image": "sample_post1.jpg", "comments": []},
    {"image": "sample_post2.jpg", "comments": []},
    {"image": "sample_post3.jpg", "comments": []}
]

auto_delete_settings = {"Negative": False, "TMI": False, "Lewd": False}

# TMI/lewd detectors
phone_pattern = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{1,4}\)[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{4}\b")
email_pattern = re.compile(r"[\w_.+-]+@[\w-]+\.[\w.-]+")
def detect_tmi(comment):
    return bool(phone_pattern.search(comment) or email_pattern.search(comment))
def detect_lewd(comment):
    kws = ["nude","sex","porn","dick","boobs","ass","fuck","horny","cum","threesome","blowjob","pussy"]
    return any(w in comment.lower() for w in kws)

# Sentiment + toxicity
def classify_toxicity(comment):
    is_tmi = detect_tmi(comment)
    is_lewd = detect_lewd(comment)
    tb_score = TextBlob(comment).sentiment.polarity
    vd_score = sia.polarity_scores(comment)['compound']
    combined = (tb_score + vd_score) / 2
    confidence = round(abs(combined), 2)

    if is_tmi:
        sentiment = "TMI"
    elif is_lewd:
        sentiment = "Lewd"
    elif combined >= 0.75:
        sentiment = "Highly Positive"
    elif combined >= 0.4:
        sentiment = "Positive"
    elif combined >= 0.1:
        sentiment = "Mildly Positive"
    elif combined >= -0.1:
        sentiment = "Neutral"
    elif combined >= -0.4:
        sentiment = "Mildly Negative"
    elif combined >= -0.75:
        sentiment = "Negative"
    else:
        sentiment = "Highly Negative"

    tox = round(sia.polarity_scores(comment)['neg'] * 100, 2)
    try:
        res = requests.post(
            PERSPECTIVE_URL,
            params={"key": PERSPECTIVE_API_KEY},
            json={"comment": {"text": comment}, "languages": ["en"], "requestedAttributes": {"TOXICITY": {}}}
        )
        jd = res.json()
        if "attributeScores" in jd:
            tox = round(jd["attributeScores"]["TOXICITY"]["summaryScore"]["value"] * 100, 2)
    except Exception:
        pass

    return sentiment, confidence, tox

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_posts')
def get_posts():
    return jsonify(posts=posts)

@app.route('/add_comment', methods=['POST'])
def add_comment():
    comment = request.form.get('comment', '').strip()
    idx = request.form.get('postIndex')
    if not comment or idx is None or not idx.isdigit():
        return jsonify(success=False)
    idx = int(idx)
    if idx < 0 or idx >= len(posts):
        return jsonify(success=False)

    sentiment, conf, tox = classify_toxicity(comment)
    # auto-delete with reason
    if auto_delete_settings.get(sentiment) or (sentiment.endswith("Negative") and auto_delete_settings.get("Negative")):
        return jsonify(
            success=True,
            posts=posts,
            counts=get_counts().get_json(),
            message=f"Comment not allowed: {sentiment}"
        )

    posts[idx]['comments'].append({
        'text': comment,
        'sentiment': sentiment,
        'confidence': conf,
        'toxicity': tox
    })
    return jsonify(success=True, posts=posts, counts=get_counts().get_json())

@app.route('/delete_comment', methods=['POST'])
def delete_comment():
    d = request.json
    pi, ci = d.get('postIndex'), d.get('commentIndex')
    if pi is not None and ci is not None:
        posts[pi]['comments'].pop(ci)
        return jsonify(success=True, posts=posts, counts=get_counts().get_json())
    return jsonify(success=False)

@app.route('/update_auto_delete', methods=['POST'])
def update_auto_delete():
    global auto_delete_settings
    settings = request.json.get('settings', {})
    auto_delete_settings.update(settings)
    # purge existing
    for post in posts:
        post['comments'] = [
            c for c in post['comments']
            if not (
                auto_delete_settings.get(c['sentiment'])
                or (c['sentiment'].endswith("Negative") and auto_delete_settings.get("Negative"))
            )
        ]
    return jsonify(success=True, settings=auto_delete_settings, posts=posts, counts=get_counts().get_json())

@app.route('/delete_all_by_type', methods=['POST'])
def delete_all_by_type():
    ct = request.json.get("commentType")
    for post in posts:
        post['comments'] = [c for c in post['comments'] if c['sentiment'] != ct]
    return jsonify(success=True, posts=posts, counts=get_counts().get_json())

@app.route('/clear_all_comments', methods=['POST'])
def clear_all():
    for post in posts:
        post['comments'].clear()
    return jsonify(success=True, posts=posts, counts=get_counts().get_json())

@app.route('/export_comments')
def export_comments():
    sio = StringIO()
    w = csv.writer(sio)
    w.writerow(["postIndex","commentIndex","text","sentiment","confidence","toxicity"])
    for i, post in enumerate(posts):
        for j, c in enumerate(post['comments']):
            w.writerow([i, j, c['text'], c['sentiment'], c['confidence'], c['toxicity']])
    out = sio.getvalue()
    return Response(out,
        mimetype='text/csv',
        headers={'Content-Disposition':'attachment; filename=comments.csv'}
    )

@app.route('/export_excel')
def export_excel():
    # Build DataFrame of all comments
    rows = []
    for i, post in enumerate(posts):
        for j, c in enumerate(post['comments']):
            rows.append({
                'Post Index': i,
                'Comment Index': j,
                'Text': c['text'],
                'Sentiment': c['sentiment'],
                'Confidence': c['confidence'],
                'Toxicity': c['toxicity']
            })
    df = pd.DataFrame(rows)

    # Percentages sheet
    pct = df['Sentiment'].value_counts(normalize=True).mul(100).round(2)
    pct_df = pct.rename_axis('Sentiment').reset_index(name='Percentage')

    # Write to Excel in-memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Comments', index=False)
        pct_df.to_excel(writer, sheet_name='Percentages', index=False)
        writer.save()
    output.seek(0)

    return Response(output.read(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition':'attachment; filename=comments.xlsx'}
    )

@app.route('/get_counts')
def get_counts():
    c = {k:0 for k in ["Highly Positive","Positive","Mildly Positive","Neutral",
                        "Mildly Negative","Negative","Highly Negative","TMI","Lewd"]}
    for post in posts:
        for cm in post['comments']:
            c[cm['sentiment']] += 1
    return jsonify(c)

@app.route('/get_chart_data')
def get_chart_data():
    return get_counts()

if __name__ == '__main__':
    app.run(debug=True)
