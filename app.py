from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from urllib.parse import quote as url_quote
import os
import time
import textwrap
import boto3

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

def check_exist_student_id(student_id):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1') 
    table = dynamodb.Table(os.environ.get('dynamo_table'))
    response = table.get_item(Key={'email': student_id})
    if 'Item' in response:
        return True
    return False

def update_score(student_id,current_score):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1') 
    table = dynamodb.Table(os.environ.get('dynamo_table'))
    response = table.get_item(Key={'email': student_id})
    if 'Item' in response:
        best_score_str = response['Item']['best_score']
        best_score = float(best_score_str.strip('%')) / 100
        if current_score > best_score:
            table.put_item(
                    Item={
                        'email': student_id,
                        'best_score': str(current_score)+'%'
                    }
                )


def add_score_dynamodb(student_id,best_score):
    print("")
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1') 
    table = dynamodb.Table(os.environ.get('dynamo_table'))
    table.put_item(
        Item={
            'email': student_id,
            'best_score': best_score,
        }
    )




@app.route("/")
def welcome():
    # if session['logged_in'] == True:
    #     return render_template('index.html')
    return render_template("login.html")

users = {
    'charul.rathore@sjsu.edu': 'Charul123',
    'narayan.balasubramanian@sjsu.edu': 'CS218'
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
        session['logged_in'] = True
        session['user_email'] = email
        return redirect(url_for('index'))
    else:
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
    
    student_id = session.get('user_email') 
    if not student_id:
        return jsonify({'message': 'Authentication required'})

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
        'test_07': [[3, 0, 0, 1, 1],None]
    }
    if file and file.filename.endswith('.py') or text_content:

        if file and file.filename.endswith('.py'):
            python_code = file.read().decode('utf-8')
        elif text_content:
            python_code = text_content
        else:
            return jsonify({'message': 'No valid input provided'})

        indented_code = textwrap.indent(python_code.strip(), '    ')

        wrapped_code = (
            "def my_main(n, kr, kc, pr, pc):\n"  
            f"{indented_code}\n"                
            "    result = knight_attack(n, kr, kc, pr, pc)\n"  
            "    return result\n"                             
        )

        # print(wrapped_code)
        output = {}
        result = {}
        try:
            exec(wrapped_code, {}, output)
        except SyntaxError as e:
            score = 0.0
            if check_exist_student_id(student_id):
                update_score(student_id, score)
            else:
                add_score_dynamodb(student_id, str(score)+'%')
            return jsonify({'message': 'Compilation Error: {}'.format(e), 'score': str(score)+'%'})

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
                execution_time = round((time.time() - start_time)*1000, 4)
                # print(execution_time)

                if (execution_time > 2000):
                    result[test] = ['Timeout', '[FAIL]']
                elif (temp != test_cases[test][1]): 
                    result[test] = ['Incorrect! Expected: '+ str(test_cases[test][1]) + ' got ' + str(temp), '[FAIL]']
                else:
                    score+=1
                    result[test] = [str(execution_time)+' MS', '[PASS]']
                
            
            score = 100*(score/len(test_cases))
            if check_exist_student_id(student_id):
                update_score(student_id, score)
            else:
                add_score_dynamodb(student_id, str(score)+'%')

            return jsonify({'message': 'Code compiled successfully!', 'result': result, 'score': str(score)+'%'})
        return jsonify({'message': 'Python code received!', 'content': python_code})
        
    else:
        return jsonify({'error': 'No valid input provided'}), 400
    

if __name__ == '__main__':
    app.run(debug=True)

  

