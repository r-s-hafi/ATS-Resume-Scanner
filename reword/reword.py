from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer
import numpy as np

# Lazy load the model only when needed (avoid slow startup)
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

load_dotenv()
key = os.getenv('OPEN_AI_KEY')
client = AsyncOpenAI(api_key=key)


async def get_best_bullet(keyword: str, bullets: list) -> str:
    model = get_model()  # Load model only when this function is called
    best_score = 0
    best_bullet = ''
    for bullet in bullets:
        
        if bullet == '':
            continue

        #turns the bullet and the keyword into embeddings, vectors with 384 dimensions that maps the semantic meaning of the text to a vector
        bullet_embedding = model.encode(bullet)
        keyword_embedding = model.encode(keyword)
    
        #takes the dot product of the two vectors and divides by the product of the length of the two vectors to normalize
        similarity = np.dot(bullet_embedding, keyword_embedding) / (
            np.linalg.norm(bullet_embedding) * np.linalg.norm(keyword_embedding))

        #scales the score to a percantage out of 100
        score = similarity * 100

        if score > best_score:
            best_score = score
            best_bullet = bullet
    
    print(f"the best bullet for the keyword: {keyword} \n {best_bullet}")
    return best_bullet



async def reword_bullet(keyword: str, user_session: dict) -> dict:
    soup = BeautifulSoup(user_session['resume_html'], 'html.parser')
    
    content_divs = soup.find_all('div', class_='section-content')
    
    #Unwrap the content in each div, pass them into bullet list
    bullets = []
    for i, div in enumerate(content_divs):
        div_text = div.get_text().strip()
        if '•' in div_text:
            for bullet in div_text.split('•'):
                bullets.append(bullet)
        else:
            bullets.append(div_text)
    
    best_bullet = await get_best_bullet(keyword, bullets)
    
    # If no suitable bullet found, return unchanged
    if not best_bullet or best_bullet.strip() == '':
        return user_session
    
    try:
        prompt = f"""You are a professional resume editor. Your task is to reword the following resume bullet point to naturally incorporate the keyword "{keyword}".

CRITICAL RULES:
1. Only reword based on what is already stated - DO NOT add new accomplishments, technologies, or responsibilities that aren't implied by the original text
2. DO NOT exaggerate numbers, scope, or impact
3. The keyword must fit naturally - if it doesn't make sense with the original bullet's context, just make minimal changes
4. Keep the same level of responsibility and impact as the original
5. Maintain professional resume language and tone
6. Return ONLY the reworded bullet point, nothing else

Original bullet point:
{best_bullet.strip()}

Keyword to incorporate: {keyword}

Reworded bullet point:"""

        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional resume editor. You reword resume bullet points truthfully and professionally. Never exaggerate or add false information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        reworded_bullet = completion.choices[0].message.content.strip()
        
        # Replace the old bullet with the new one in the HTML
        user_session['resume_html_new'] = user_session['resume_html'].replace(
            best_bullet.strip(), 
            '<span class="reworded-bullet">' + reworded_bullet + '</span>'
        )
        
        print(f"\n{'='*60}")
        print(f"Original: {best_bullet.strip()}")
        print(f"Reworded: {reworded_bullet}")
        print(f"{'='*60}\n")
        
        return user_session

    except json.JSONDecodeError as e:
        print(f"JSON decode error in reword_bullet: {e}")
        print(f"Response was: {reworded_bullet}")
        return user_session
    except Exception as e:
        print(f"Error in reword_bullet: {e}")
        return user_session
