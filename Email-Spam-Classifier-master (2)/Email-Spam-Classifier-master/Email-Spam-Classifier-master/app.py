from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import string
import pickle
import nltk
import json
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)

# Configure session
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Initialize PorterStemmer
ps = PorterStemmer()

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)
    
    y = []
    for i in text:
        if i.isalnum():
            y.append(i)
    
    text = y[:]
    y.clear()
    
    for i in text:
        if i not in stopwords.words('english') and i not in string.punctuation:
            y.append(i)
    
    text = y[:]
    y.clear()
    
    for i in text:
        y.append(ps.stem(i))
    
    return " ".join(y)

# Load pre-trained models
tfidf = pickle.load(open('vectorizer.pkl', 'rb'))
model = pickle.load(open('model.pkl', 'rb'))

def load_user_credentials():
    with open('users.json', 'r') as file:
        return json.load(file)['users']

def save_user_credentials(users):
    with open('users.json', 'w') as file:
        json.dump({"users": users}, file)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_user_credentials()
        user = next((user for user in users if user["username"] == username and user["password"] == password), None)
        
        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('sms_spam_classifier'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_user_credentials()
        if next((user for user in users if user["username"] == username), None):
            return render_template('register.html', error="Username already exists")
        
        users.append({"username": username, "password": password})
        save_user_credentials(users)
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/sms_spam_classifier', methods=['GET', 'POST'])
def sms_spam_classifier():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        input_sms = request.form['sms_body']
        transformed_sms = transform_text(input_sms)
        vector_input = tfidf.transform([transformed_sms])
        result = model.predict(vector_input)[0]
        
        classification = "Spam" if result == 1 else "Not Spam"
        return render_template('sms_spam_classifier.html', classification=classification)
    
    return render_template('sms_spam_classifier.html')

if __name__ == '__main__':
    app.run(debug=True)
