from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from urllib.parse import quote as url_quote
import os
import time

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def welcome():
    if session['logged_in'] == True:
        return render_template('index.html')
    return render_template("login.html")

users = {
    'charul.rathore@sjsu.edu': 'Charul123',
}

@app.route('/logout')
def logout():
    session['logged_in'] = False
    session.pop('user_email', None)
    return redirect(url_for('welcome'))


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if email in users and users[email] == password:
        # Authentication successful
        session['logged_in'] = True
        session['user_email'] = email
        return redirect(url_for('index'))
    else:
        # Authentication failed
        return  render_template("/login.html", message="Failed! Try again.")
    
@app.route('/index')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('welcome'))
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    text_content = request.form.get('code_text')
    file = request.files.get('file')
    score = 0
    test_cases = {
        'test_00': [[8, 1, 1, 2, 2],2],
        'test_01': [[8, 1, 1, 2, 3],1],
        'test_02': [[8, 0, 3, 4, 2],3],
        'test_03': [[8, 0, 3, 5, 2],4],
        'test_04': [[24, 4, 7, 19, 20],10],
        'test_05': [[100, 21, 10, 0, 0],11],
        'test_06': [[3, 0, 0, 1, 2],2], ## Planted wrong answer, correct is 1
        'test_07': [[3, 0, 0, 1, 1],-1]
    }
    if file and file.filename.endswith('.py') or text_content:

        if file and file.filename.endswith('.py'):
            python_code = file.read().decode('utf-8')
        
        if text_content:
            python_code = text_content
            # print(python_code)

        output = {}
        result = {}
        # exec(python_code, {}, output)
        try:
            exec(python_code, {}, output)
        except SyntaxError as e:
            score = 0
            return jsonify({'message': 'Compliation Error SyntaxError in provided Python code: {}'.format(e), 'score': str(score)+'%'})

        if 'my_main' in output and callable(output['my_main']):
            count = 0
            for test in test_cases:
                count += 1
                n = test_cases[test][0][0]
                kr = test_cases[test][0][1]
                kc = test_cases[test][0][2]
                pr = test_cases[test][0][3]
                pc = test_cases[test][0][4]

                start_time = time.time()
                temp = output['my_main'](n, kr, kc, pr, pc)
                execution_time = (time.time() - start_time)*1000
                # print(execution_time)

                if (execution_time > 2000):
                    result[test] = ['Timeout', '[FAIL]']
                elif (temp != test_cases[test][1]): 
                    result[test] = ['Incorrect! Expected: '+ str(test_cases[test][1]) + ' got ' + str(temp), '[FAIL]']
                else:
                    score+=1
                    result[test] = [str(execution_time)+' MS', '[PASS]']

            return jsonify({'message': 'Python code executed!', 'result': result, 'score': str(100*(score/len(test_cases)))+'%'})
        return jsonify({'message': 'Python code received!', 'content': python_code})
        
    else:
        return jsonify({'error': 'No valid input provided'}), 400
    

if __name__ == '__main__':
    app.run(debug=True)
