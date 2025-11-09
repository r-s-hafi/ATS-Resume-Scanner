def get_score(resume_keywords: dict, job_description_keywords: dict) -> dict:
    matches = []
    missing = []
    results = {}

    #add words that are in both sets of keywords to matches, otherwise add them to missing
    for word, count in resume_keywords.items():
        if word in job_description_keywords:
            matches.append(resume_keywords[word]['display_form'])
        else:
            missing.append(resume_keywords[word]['display_form'])

    #take the matching score to be the number of matches divided by the number of keywords in the job description
    score = 0
    if len(job_description_keywords) > 0:
        score = len(matches) / len(job_description_keywords) * 100

    #return results as a dictionary
    results = {
        'score': f"{round(score, None)}%",
        'matches': matches,
    }

    return results