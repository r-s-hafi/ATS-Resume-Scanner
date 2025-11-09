from pydoc import text
from fastapi import FastAPI, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles
from models import Resume, Job

from parse.parse_plaintext import get_text_from_pdf, clean_text, extract_keywords_and_phrases
from parse.parse_job import parse_job
from format.format import format_resume
from score.score import score_resume
from reword.reword import reword_bullet

app = FastAPI()
templates = Jinja2Templates('./templates')

# Mount static files
app.mount("/static", StaticFiles(directory="templates"), name="static")

user_session= {
    "resume": Resume(),
    "job": Job(),
    "resume_html": "",	
    "matched_keywords": {},
    "unmatched_keywords": [],
    "current_keyword": ""
}

@app.get("/")
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"text": ""})

@app.post("/handle-resume-file")
async def handle_resume_file(resume_file: UploadFile = File(...)):
    
    resume_contents = await resume_file.read()

    resume = Resume()
    
    # extract text from the PDF
    resume.plaintext = get_text_from_pdf(resume_contents)

    #this is actually what is returned as an html response, the other stuff below is just to process the resume and extract keywords
    formatted_resume = await format_resume(resume.plaintext, resume)

    # Store the HTML string content (decode the bytes from the response)
    user_session['resume_html'] = formatted_resume.body.decode('utf-8')

    #extract important words/phrases
    resume.keywords = extract_keywords_and_phrases(resume.plaintext)

    #enter the current resume into the user session
    user_session['resume'] = resume


    return formatted_resume

@app.post("/handle-job-description")
async def handle_job_description(job_description_text: str = Form())-> HTMLResponse:
    
    job = Job()
    #remove common words, spaces, bullets, etc
    job.plaintext = clean_text(job_description_text)
    #extract only the important words from the job description text
    job.keywords = extract_keywords_and_phrases(job.plaintext)
    #fill in job.html with job description and wrap keywords in span element
    job = parse_job(job)
    #enter the current job into the user session
    user_session['job'] = job

    #reset unmatched keywords list (if the user spams the get insights button)
    user_session['unmatched_keywords'] = []

    #scores the compatibility of the resume and the job description based on the job and resume entered into user_session
    result = await score_resume(user_session)
    if result:
        user_session.update(result)

    score = f'{round((len(user_session['matched_keywords']) / len(job.keywords) * 100)) if len(job.keywords) > 0 else 0}%'

    #really weird return statement BUT it basically:
    #first returns the formatted job html (highlights keywords) to original target (.job-description)
    #second returns the user's score to the score-display div by using hx-swap-oob
    unmatched_keywords_html = "<p>"
    for keyword_entry in user_session['unmatched_keywords']:
        print('unmatched keyword: ', keyword_entry)
        unmatched_keywords_html += f"{keyword_entry}, "
    unmatched_keywords_html = unmatched_keywords_html[:-2]
    unmatched_keywords_html += "</p>"
    
    matched_keywords_html = "<p>"
    for keyword_entry in user_session['matched_keywords'].keys():
        matched_keywords_html += f"{keyword_entry}, "
    matched_keywords_html = matched_keywords_html[:-2]
    matched_keywords_html += "</p>"

    if user_session['unmatched_keywords']:
        first_keyword_prompt = user_session['unmatched_keywords'][0]


        #returns the score and score details, matched and unmatched keyworrds, and begins the unmatched keyword prompting loop
        return HTMLResponse(f"""
                            {job.html}
                            <div id="score-display" hx-swap-oob="true">
                                <div id="score-details">
                                    <div id="score-details-text">
                                        <h2>Score: {score}</h2>
                                        <p>Matched {len(user_session['matched_keywords'])} {'keyword' if len(user_session['matched_keywords']) == 1 else 'keywords'} out of {len(job.keywords)} {'keyword' if len(job.keywords) == 1 else 'keywords'}.</p>
                                    </div>
                                </div>
                                <div id="keywords-identified">
                                    <div id="keywords-identified-details">
                                        <div class="keyword-details" id="total-keywords">
                                            <div class="keyword-details-text">
                                                <h3>Matched keywords</h3>
                                            </div>
                                            <div class="keyword-details-content">
                                                {matched_keywords_html}
                                            </div>
                                        </div>
                                        <div class="keyword-details" id="matched-keywords">
                                            <div class="keyword-details-text">
                                                <h3>Unmatched keywords</h3>
                                            </div>
                                            <div class="keyword-details-content">
                                                {unmatched_keywords_html}   
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div id="suggestion-container">
                                    <div class="reword-prompt">
                                        Have you encountered the keyword "{first_keyword_prompt}" in your experiences?
                                    </div>
                                    <div class="suggestion-response">
                                        <form hx-post="/reword" hx-trigger="submit" hx-target=".resume">
                                            <input type="hidden" name="keyword" value="{first_keyword_prompt}">
                                            <div class="suggestion-buttons">
                                                <button type="submit" name="reword_answer" value="Yes" class="button">Yes</button>
                                                <button type="submit" name="reword_answer" value="No" class="button">No</button>
                                            </div>
                                            <div class="htmx-indicator">
                                                <div class="loading-content">
                                                    <div class="spinner"></div>
                                                    <p>Thinking... This may take a few seconds.</p>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            </div>
        """)
    else:
        return HTMLResponse(f"""
                            {user_session['resume_html']}
                            <div id="job-description" hx-swap-oob="true">
                                <div class="reword-prompt">
                                    No unmatched keywords detected. Please either enter a longer job description or export.
                                </div>
                            </div>
                            """)
    
#handles rewording after the user responds yes/no to if theyve encountered the keyword
@app.post("/reword")
async def reword(reword_answer: str = Form(), keyword: str = Form()) -> HTMLResponse:

    #if the user would like to keep the reworded bullet   
    if reword_answer == "Yes":
        #sets user_session[resume_html_new] as the reworded html, preserves original html as user_session[resume_html]
        await reword_bullet(keyword, user_session)

        #If there are still unmatched keywords, remove the most recent one and set the new first one to be the one that is in the user prompt
        if user_session['unmatched_keywords']:
            user_session['current_keyword'] = user_session['unmatched_keywords'][0]
            user_session['unmatched_keywords'].pop(0)

        #Return html asking user if they accept the change or not
            
        return HTMLResponse(f"""
                                {user_session['resume_html_new']}
                                <div id="suggestion-container" hx-swap-oob="true">
                                    <div class="reword-prompt">
                                        Keep this reword?
                                    </div>
                                    <div class="suggestion-response">
                                        <form hx-post="/confirm" hx-trigger="submit" hx-target=".resume">
                                            <div class="suggestion-buttons">
                                                <button type="submit" name="confirm_answer" value="Yes" class="button">Yes</button>
                                                <button type="submit" name="confirm_answer" value="No" class="button">No</button>
                                            </div>
                                            <div class="htmx-indicator">
                                                <div class="loading-content">
                                                    <div class="spinner"></div>
                                                    <p>Thinking... This may take a few seconds.</p>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>)
                                """)

    #if the user has not encountered the keyword in their experience
    elif reword_answer == "No":
        #remove current keyword from the list
        user_session['unmatched_keywords'].pop(0)

        #if there are still unmatched keywords left to prompt the user with
        if user_session['unmatched_keywords']:
            first_keyword_prompt = user_session['unmatched_keywords'][0]
            return HTMLResponse(f"""
                                {user_session['resume_html']}
                                <div id="suggestion-container" hx-swap-oob="true">
                                    <div class="reword-prompt">
                                        Have you encountered the keyword "{first_keyword_prompt}" in your experiences?
                                    </div>
                                    <div class="suggestion-response">
                                        <form hx-post="/reword" hx-trigger="submit" hx-target=".resume">
                                            <input type="hidden" name="keyword" value="{first_keyword_prompt}">
                                            <div class="suggestion-buttons">
                                                <button type="submit" name="reword_answer" value="Yes" class="button">Yes</button>
                                                <button type="submit" name="reword_answer" value="No" class="button">No</button>
                                            </div>
                                            <div class="htmx-indicator">
                                                <div class="loading-content">
                                                    <div class="spinner"></div>
                                                    <p>Thinking... This may take a few seconds.</p>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                                """)

        #if there are no more unmatched keywords left
        else:
            return HTMLResponse(f"""
                                {user_session['resume_html']}
                                <div id="suggestion-container" hx-swap-oob="true">
                                    <div class="reword-prompt">
                                        No more unmatched keywords detected. Please either continue to edit resume below or export.
                                    </div>
                                </div>
                                """)

            
#handles resume formatting and resetting the prompt after the user responds yes/no to if they want to keep the bullet
@app.post("/confirm")
async def confirm(confirm_answer: str = Form()) -> HTMLResponse:
    
    #if the user confirms they'd like to keep the bullet, update the html response and prompt with next keyword
    if confirm_answer == "Yes":
        #adds the current keyword to the match keywords dictionary and recalculates the score
        user_session['matched_keywords'][user_session['current_keyword']] = 1
        job = user_session['job']
        score = f'{round((len(user_session['matched_keywords']) / len(job.keywords) * 100)) if len(job.keywords) > 0 else 0}%'

        unmatched_keywords_html = "<p>"
        for keyword_entry in user_session['unmatched_keywords']:
            unmatched_keywords_html += f"{keyword_entry}, "
        unmatched_keywords_html = unmatched_keywords_html[:-2]
        unmatched_keywords_html += "</p>"
        
        matched_keywords_html = "<p>"
        for keyword_entry in user_session['matched_keywords'].keys():
            matched_keywords_html += f"{keyword_entry}, "
        matched_keywords_html = matched_keywords_html[:-2]
        matched_keywords_html += "</p>"

        if user_session['unmatched_keywords']:
            first_keyword_prompt = user_session['unmatched_keywords'][0]
            user_session['resume_html'] = user_session['resume_html_new']



            return HTMLResponse(f"""
                                {user_session['resume_html']}
                                <div id="keywords-identified" hx-swap-oob="true">
                                <div id="keywords-identified-details">
                                    <div class="keyword-details" id="total-keywords">
                                        <div class="keyword-details-text">
                                            <h3>Matched keywords</h3>
                                        </div>
                                        <div class="keyword-details-content">
                                            {matched_keywords_html}
                                        </div>
                                    </div>
                                    <div class="keyword-details" id="matched-keywords">
                                        <div class="keyword-details-text">
                                            <h3>Unmatched keywords</h3>
                                        </div>
                                        <div class="keyword-details-content">
                                            {unmatched_keywords_html}   
                                        </div>
                                    </div>
                                </div>
                            </div>
                                <div id="score-details-text" hx-swap-oob="true">
                                    <h2>Score: {score}</h2>
                                    <p>Matched {len(user_session['matched_keywords'])} {'keyword' if len(user_session['matched_keywords']) == 1 else 'keywords'} out of {len(job.keywords)} {'keyword' if len(job.keywords) == 1 else 'keywords'}.</p>
                                </div>
                                <div id="suggestion-container" hx-swap-oob="true">
                                    <div class="reword-prompt">
                                        Have you encountered the keyword "{first_keyword_prompt}" in your experiences?
                                    </div>
                                    <div class="suggestion-response">
                                        <form hx-post="/reword" hx-trigger="submit" hx-target=".resume">
                                            <input type="hidden" name="keyword" value="{first_keyword_prompt}">
                                            <div class="suggestion-buttons">
                                                <button type="submit" name="reword_answer" value="Yes" class="button">Yes</button>
                                                <button type="submit" name="reword_answer" value="No" class="button">No</button>
                                            </div>
                                            <div class="htmx-indicator">
                                                <div class="loading-content">
                                                    <div class="spinner"></div>
                                                    <p>Thinking... This may take a few seconds.</p>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                                """)

        #if the user would like to keep the last bullet update and they have no unmatched keywords left
        else:
            return HTMLResponse(f"""
                                {user_session['resume_html']}
                                <div id="score-details-text" hx-swap-oob="true">
                                    <h2>Score: {score}</h2>
                                    <p>Matched {len(user_session['matched_keywords'])} {'keyword' if len(user_session['matched_keywords']) == 1 else 'keywords'} out of {len(job.keywords)} {'keyword' if len(job.keywords) == 1 else 'keywords'}.</p>
                                </div>
                                <div id="suggestion-container" hx-swap-oob="true">
                                    <div class="reword-prompt">
                                        No more unmatched keywords detected. Please either continue to edit resume below or export.
                                    </div>
                                </div>
                                """)
    #if the user wouldn't like to keep the reworded bullet, return the html without the reword and reprompt with the next keyword
    elif confirm_answer == "No":
        #if this is not the last keyword in the list
        if user_session['unmatched_keywords']:
            first_keyword_prompt = user_session['unmatched_keywords'][0]
            return HTMLResponse(f"""
                                    {user_session['resume_html']}
                                    <div id="suggestion-container" hx-swap-oob="true">
                                        <div class="reword-prompt">
                                            Have you encountered the keyword "{first_keyword_prompt}" in your experiences?
                                        </div>
                                        <div class="suggestion-response">
                                            <form hx-post="/reword" hx-trigger="submit" hx-target=".resume">
                                                <input type="hidden" name="keyword" value="{first_keyword_prompt}">
                                                <div class="suggestion-buttons">
                                                    <button type="submit" name="reword_answer" value="Yes" class="button">Yes</button>
                                                    <button type="submit" name="reword_answer" value="No" class="button">No</button>
                                                </div>
                                                <div class="htmx-indicator">
                                                    <div class="loading-content">
                                                        <div class="spinner"></div>
                                                        <p>Thinking... This may take a few seconds.</p>
                                                    </div>
                                                </div>
                                            </form>
                                        </div>
                                    </div>
                                    """)

        #if this is the last keyword in the list
        else:
            return HTMLResponse(f"""
                                {user_session['resume_html']}
                                <div id="suggestion-container" hx-swap-oob="true">
                                    <div class="reword-prompt">
                                        No more unmatched keywords detected. Please either continue to edit resume below or export.
                                    </div>
                                </div>
                                """)