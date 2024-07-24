import requests
def get_perspective_score(text, api_key):
    url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
    params = {'key': api_key,}
    data = {'comment': {'text': text},
        'languages': ['en'],
        'requestedAttributes': {'TOXICITY': {}}}
    response = requests.post(url, params=params, json=data)
    result = response.json()
    if 'attributeScores' in result:
        toxicity_score = result['attributeScores']['TOXICITY']['summaryScore']['value']
        return toxicity_score
    else:
        return None
def analyze_comment_sensitivity(comment, api_key):
    sensitivity_score = get_perspective_score(comment, api_key)
    if sensitivity_score is not None:
        print(f"Comment: {comment}")
        print(f"Sensitivity Score: {sensitivity_score}")
        if sensitivity_score >= 0.7:
            print("This comment is likely to be sensitive.")

        if sensitivity_score >= 0.9:
            print("This comment sensitive.")
        else:
            print("This comment is not considered sensitive.")
    else:
        print("Failed to analyze comment sensitivity.")
api_key = 'AIzaSyBNq734U4_QvcRoFi73Z3usULIcur0efe8'
comment_to_analyze = input("Enter the comment to analyze: ")
analyze_comment_sensitivity(comment_to_analyze, api_key)
