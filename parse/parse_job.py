from models import Job
import re

def parse_job(job: Job) -> Job:

    text = job.plaintext

    keyword_list = []

    for keyword in job.keywords:
        keyword_list.append(keyword['lemma'])

    #sort keywords by word length
    sorted_keywords = sorted(keyword_list, key=lambda x: len(x.split()), reverse = True)

   # print(sorted_keywords)
    
    # Find and wrap each keyword in the text
    for keyword in sorted_keywords:
        # Create regex pattern that matches keyword case-insensitively
        # Word boundaries ensure we match whole words/phrases only
        pattern = r'\b' + re.escape(keyword) + r'\b'
        
        # Replace all occurrences, preserving original case
        #Checks for keyword pattern within the text and wraps it in a span regardless of case (.group(0) returns the full regex)
        text = re.sub(pattern, lambda m: f'<span class="keyword">{m.group(0)}</span>', text, flags=re.IGNORECASE)
    
    job.html = '<div>' + text + '</div>'

    job.html = job.html + """
                <script>
                document.getElementById('job-description').style.display = 'block';
                </script>
                """

    return job