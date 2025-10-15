from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)
app.secret_key = 'ResuMate@MCS'

COHERE_API_KEY = os.environ.get('COHERE_API_KEY', 'Ty8rnnDkH4qi3YRJeX2RL15qZxVURr64psQi5i8H')
co = None

try:
    import cohere
    if COHERE_API_KEY:
        co = cohere.Client(COHERE_API_KEY)
        print("AI connected successfully")
    else:
        print("Using basic responses - add Cohere API key for AI features")
except ImportError:
    print("Install cohere for AI features: pip install cohere")
except Exception as e:
    print(f"AI connection failed: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_resume():
    data = request.get_json() if request.is_json else request.form
    
    name = data.get('name', '')
    email = data.get('email', '')
    phone = data.get('phone', '')
    summary = data.get('summary', '')
    experience = data.get('experience', '')
    education = data.get('education', '')
    skills = data.get('skills', '')
    job_description = data.get('job_description', '')
    
    improved_summary = improve_text(summary, 'summary') if summary else summary
    improved_experience = improve_text(experience, 'experience') if experience else experience
    
    result = {
        'name': name,
        'email': email,
        'phone': phone,
        'summary': improved_summary,
        'experience': improved_experience,
        'education': education,
        'skills': skills,
        'ats_score': calculate_ats_score(f"{summary} {experience} {skills}", job_description)
    }
    
    return jsonify(result)

def improve_text(text, section_type):
    if not text.strip():
        return text
    
    if co:
        try:
            if section_type == 'summary':
                prompt = f"Make this resume summary more professional and impactful. Keep it under 80 words and focus on achievements: {text}"
            else:
                prompt = f"Rewrite these work experiences with stronger action verbs and specific achievements. Add numbers where possible: {text}"
            
            response = co.generate(
                model='command',
                prompt=prompt,
                max_tokens=180,
                temperature=0.6
            )
            
            improved = response.generations[0].text.strip()
            print(f"AI enhanced {section_type}")
            return improved
            
        except Exception as e:
            print(f"AI enhancement failed for {section_type}: {e}")
    
    if section_type == 'summary':
        return f"Experienced professional with proven track record in delivering exceptional results and driving innovation. {text}"
    else:
        lines = text.split('\n')
        improved_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('•'):
                improved_lines.append('• ' + line)
            elif line:
                improved_lines.append(line)
        return '\n'.join(improved_lines)

def calculate_ats_score(resume_text, job_description):
    if not job_description.strip():
        return {"score": 72, "matches": ["Paste a job description to see detailed keyword analysis"]}
    
    jd_words = set(word.lower() for word in job_description.split() if len(word) > 3)
    resume_words = set(word.lower() for word in resume_text.split() if len(word) > 3)
    
    common_words = {'and', 'the', 'for', 'with', 'you', 'are', 'have', 'will', 'can', 'this', 'that', 'from', 'they', 'were', 'been', 'your', 'our', 'their', 'work', 'team', 'company'}
    jd_words -= common_words
    resume_words -= common_words
    
    matches = jd_words.intersection(resume_words)
    
    if len(jd_words) == 0:
        score = 72
    else:
        score = min(int(len(matches) / len(jd_words) * 100 * 1.4), 94)
    
    return {
        "score": max(score, 35),
        "matches": list(matches)[:12]
    }

@app.route('/interview', methods=['POST'])
def mock_interview():
    data = request.get_json() if request.is_json else request.form
    job_title = data.get('job_title', 'Software Developer')
    
    basic_questions = [
        f"Walk me through your background and why you're interested in this {job_title} role.",
        "Tell me about a challenging project where you had to overcome significant obstacles.",
        "What specific achievements are you most proud of in your career so far?",
        "How do you handle tight deadlines and competing priorities?",
        f"What excites you most about working as a {job_title} in our industry?"
    ]
    
    if co:
        try:
            response = co.generate(
                model='command',
                prompt=f"Create 5 thoughtful interview questions for a {job_title} role. Mix behavioral and technical aspects. Make them realistic and specific to the position:",
                max_tokens=160,
                temperature=0.7
            )
            
            ai_text = response.generations[0].text.strip()
            questions = []
            for line in ai_text.split('\n'):
                clean_line = line.strip('123456789. ').strip()
                if clean_line and len(clean_line) > 10:
                    questions.append(clean_line)
            
            if len(questions) >= 3:
                print(f"Generated interview questions for {job_title}")
                return jsonify({"questions": questions[:5]})
                
        except Exception as e:
            print(f"Interview generation failed: {e}")
    
    return jsonify({"questions": basic_questions})

@app.route('/interview_feedback', methods=['POST'])
def interview_feedback():
    data = request.get_json() if request.is_json else request.form
    answers = data.get('answers', [])
    job_title = data.get('job_title', 'Professional')
    
    feedback_list = []
    
    if co:
        try:
            for i, answer in enumerate(answers):
                if not answer.strip():
                    feedback_list.append("This question needs an answer to provide meaningful feedback.")
                    continue
                
                response = co.generate(
                    model='command',
                    prompt=f"You are an experienced hiring manager. Analyze this interview answer for a {job_title} position and give constructive, specific feedback. Be encouraging but honest about areas for improvement: '{answer}'",
                    max_tokens=120,
                    temperature=0.5
                )
                
                ai_feedback = response.generations[0].text.strip()
                if ai_feedback:
                    feedback_list.append(ai_feedback)
                else:
                    feedback_list.append("Your answer shows good understanding. Consider adding specific examples with measurable outcomes.")
                
        except Exception as e:
            print(f"AI feedback generation failed: {e}")
            return get_basic_feedback(answers)
    else:
        return get_basic_feedback(answers)
    
    return jsonify({"feedback": feedback_list})

def get_basic_feedback(answers):
    feedback = []
    for answer in answers:
        if not answer.strip():
            feedback.append("Please provide an answer to receive feedback.")
        elif len(answer.split()) < 8:
            feedback.append("Your answer is quite brief. Try to expand with specific examples and details about your experience.")
        elif len(answer.split()) > 100:
            feedback.append("Great detail! Consider making your response more concise while keeping the key points.")
        else:
            feedback.append("Good response structure. To make it even stronger, try adding specific numbers or outcomes that demonstrate your impact.")
    
    return jsonify({"feedback": feedback})

if __name__ == '__main__':
    print("Starting ResuMate...")
    app.run(debug=True, port=5000, host='0.0.0.0')

