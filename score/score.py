import json
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI

from fastapi.responses import HTMLResponse
from models import Resume, Job

load_dotenv()
key = os.getenv('OPEN_AI_KEY')
client = AsyncOpenAI(api_key=key)

async def catch_keywords(unmatched_job_keywords: list, resume_keywords: list, user_session: dict) -> dict:
    """
    Uses OpenAI to find semantic matches between job keywords and resume keywords
    that weren't caught by exact lemma matching.
    """
    
    if not unmatched_job_keywords or not resume_keywords:
        return user_session
    
    resume_lemmas = []
    job_lemmas = []

    for entry in unmatched_job_keywords:
        job_lemmas.append(entry)
    # Extract just the lemmas for easier processing
   # job_lemmas = [entry['lemma'] for entry in unmatched_job_keywords]
    
    for entry in resume_keywords:
        resume_lemmas.append(entry)
    #resume_lemmas = [entry['lemma'] for entry in resume_keywords]
    
    prompt = f"""You are a keyword matching assistant for an ATS (Applicant Tracking System).

Your task: Identify semantic matches between job posting keywords and resume keywords that weren't caught by exact text matching.

Job Keywords (unmatched): {job_lemmas}
Resume Keywords (all): {resume_lemmas}

Instructions:
1. For each job keyword, determine if ANY resume keyword is semantically equivalent or a close variant
2. Consider variations like: singular/plural (pipe/piping), verb forms (design/designed), abbreviations (API/Application Programming Interface)
3. Only match keywords that are genuinely related in a professional context
4. Be strict - don't match keywords that are merely in the same field but represent different concepts

Return ONLY a JSON array of matches in this exact format:
[
  {{"job_keyword": "pipe", "resume_keyword": "piping"}},
  {{"job_keyword": "design", "resume_keyword": "designed"}}
]

If no semantic matches exist, return an empty array: []

Do not include any explanation, only the JSON array."""

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o-mini for better reasoning at lower cost
            messages=[
                {"role": "system", "content": "You are a precise keyword matching assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1  # Low temperature for more consistent results
        )
        
        response = completion.choices[0].message.content.strip()
        
        # Parse JSON response
        matches = json.loads(response)

        #Add matches from matches json to semantic _matches dictionary where the key is the keyword and the count is the value
        semantic_matches = {}
        for match in matches:
            if match['job_keyword'] not in semantic_matches:
                semantic_matches[match['job_keyword']] = 1
            else:
                semantic_matches[match['job_keyword']] += 1

        user_session['matched_keywords'].update(semantic_matches)

        
        if unmatched_job_keywords:
            for word in unmatched_job_keywords:
                if word['lemma'] not in semantic_matches:
                    user_session['unmatched_keywords'].append(word['lemma'])

        
        return user_session

    except json.JSONDecodeError as e:
        print(f"JSON decode error in catch_keywords: {e}")
        print(f"Response was: {response}")
        return user_session
    except Exception as e:
        print(f"Error in catch_keywords: {e}")
        return user_session






async def score_resume(user_session: dict) -> dict:
    #unpack dictionary input into resume and job variables if they exist
    if not user_session['resume']:
        return """
            <div> Hey make sure you have a resume uploaded
            </div>
            """
    else:
        resume = user_session['resume']
    
    if not user_session['job']:
        return """
            <div> Hey make sure you have a job uploaded
            </div>
            """
    else:
        job = user_session['job']

    #give the resume a score based upon the number of keywords in job.keywords and resume.keywords

    job_keyword_count = 0
    matched_job_keywords = {}  # Track which job keywords were matched
    unmatched_job_keywords = []
    
    # First pass: exact lemma matching
    for job_entry in job.keywords:
        job_keyword_count += 1
        matched = False
        #add keyword to keyword dictionary if matches a resume keyword, return dictionary matched_job_keywords where the key is the keyword and the value is the count
        for resume_entry in resume.keywords:
            #print(f"job keyword: {job_entry['lemma']}, resume keyword: {resume_entry['lemma']}")
            if job_entry['lemma'] == resume_entry['lemma']:
                if job_entry['lemma'] not in matched_job_keywords.keys():
                    matched_job_keywords[job_entry['lemma']] = 1
                    matched = True
                else:
                    job_entry['lemma'] += 1
                break
                
        #add to the unmatched list if the keyword is not found in the resume
        if not matched:
            unmatched_job_keywords.append(job_entry)

    #Add the matched keywords to the user_session dictionary
    user_session['matched_keywords'] = matched_job_keywords
    
    #If there are any unmatched keywords remaining after the first pass, call gpt to double check similar keywords
    #adds matched keywords to the user_session dict
    print(f'here it is before gpt {user_session}')

    if unmatched_job_keywords:
        print(f"\n=== Checking {len(unmatched_job_keywords)} unmatched keywords with OpenAI ===")

    
        user_session = await catch_keywords(unmatched_job_keywords, resume.keywords, user_session)



    print(f'here it is after gpt {user_session}')

    return user_session
    
    # user_session['total job keywords'] = job_keyword_count
    # user_session['match percentage'] = round((len(user_session['matched_keywords']) / job_keyword_count * 100), 1) if job_keyword_count > 0 else 0

    # print(f"\n=== FINAL SCORE ===")
    # print(f"Total keywords in job: {job_keyword_count}")
    # print(f"Total matches: {len(user_session['matched_keywords'])}/{job_keyword_count} ({user_session['match percentage']}%)")
    # print(f"===================\n")
    # print(f"Here's what your resume doesn't have: {unmatched_job_keywords}")


    html_content = f"""
            <h1>Your Score Is..{round((len(user_session['matched_keywords']) / job_keyword_count * 100), 1) if job_keyword_count > 0 else 0}
            </h1>
            """

    return HTMLResponse(html_content)


#