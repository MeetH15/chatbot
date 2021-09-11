# application.py #
from flask import *
from flask_mail import *
import pymysql
import string
from random import *
from passlib.hash import sha256_crypt

import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import numpy
import tflearn
import tensorflow
import random
import json
import pickle

def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]
    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]
    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return numpy.array(bag)

app = Flask(__name__)
app.secret_key = "abc"

# Configuring Flask Mail #
app.config['MAIL_SERVER']='smtp.gmail.com'  
app.config['MAIL_PORT']=465  
app.config['MAIL_USERNAME'] = 'smartsolver20'  
app.config['MAIL_PASSWORD'] = 'quirry091517'  
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USE_SSL'] = True

# Connecting to Database #
connection = pymysql.connect(host="localhost",user="root",passwd="",database="SmartSolver")
cursor = connection.cursor()

# Main Page #
@app.route('/')
def mainPage():
    return render_template("index.html", time1=5500)

@app.route('/main1')
def main1():
    return render_template("index.html", time1=1)

# Admin Login Page #
@app.route('/login/')
def login():
    return render_template('login.html')

@app.route('/sendMail', methods=['POST'])
def sendMail():
    first = request.form['first-name']
    last = request.form['last-name']
    senderMail = request.form['sender-email']
    message = request.form['message']

    # Creating instance of mail class #
    mail = Mail(app)

    msg = Message('subject', sender = senderMail, recipients=['smartsolver20@gmail.com'])
    msg.body = message
    mail.send(msg)
    return "<script> alert('Feedback Sent Successfully') </script>"

# Registration Page #
@app.route('/RegisterOrg',methods=['POST'])
def RegisterOrg():
    Form_OId = request.form['Oid']
    compareQuery = "SELECT `OrgId` FROM `orgdetails`"
    cursor.execute(compareQuery)
    res = cursor.fetchall()
    for row in res:
        a = row[0]
        if a == Form_OId:
            return "<script> alert('Same Data Present') </script>"

    orgQuery = "INSERT INTO `orgdetails` VALUES('{0}','{1}','{2}','{3}','{4}','{5}','{6}')".format(request.form['Oid'], request.form['Oname'], request.form['Otype'], request.form['Admin'], request.form['Email'], request.form['Address'], request.form['Phone'])
    cursor.execute(orgQuery)
    connection.commit()
    orgMail = request.form['Email']

    chars = string.ascii_letters + string.punctuation + string.digits
    generatedCode = f'{randrange(1, 10**5):03}'
    generatedPass = "".join(choice(chars) for k in range(randint(8,16)))
    MailMessage = "Thank you "+ request.form['Admin'] +" for your patience and registering with SmartSolver! Your details are recorded and now you can start using the chatbot. What you need to do is go the main page, login in and fill the details of your organization in the required format. Login credentials are provided below : \nOrganization Code : "+generatedCode+"\nOrganization Name : "+request.form['Oname']+"\nPassword : "+generatedPass+"\n\nFeel free to leave us a feedback or suggestions on smartsolver20@gmail.com"

    mail = Mail(app)
    msg = Message('Message From SmartSolver', sender = 'smartsolver20@gmail.com', recipients=[orgMail])
    msg.body = MailMessage
    mail.send(msg)


    codeQuery = "INSERT INTO `AdminLogin` VALUES('{0}','{1}','{2}','{3}','{4}')".format(request.form['Admin'], generatedCode, request.form['Oid'], request.form['Oname'], sha256_crypt.hash(generatedPass))
    cursor.execute(codeQuery)
    connection.commit()
    fName = Form_OId+".json"
    f = open(fName, "w+")
    contents = {
        "intents": [
            {
                "tag": "greeting",
                "patterns": [
                    "Hi",
                    "How are you",
                    "Is anyone there?",
                    "Hello",
                    "Good day",
                    "How's your day going ?",
                    "What's going on ?",
                    "Sup?",
                    "Whazzup?",
                    "Hiya!",
                    "Howdy!",
                    "Yo!",
                    "What's up?"
                ],
                "responses": [
                    "Hello, thanks for visiting.",
                    "Good to see you",
                    "Hi there, how can I help?",
                    "Nice to see you.",
                    "Pleased to meet you"
                ]
            },
            {
                "tag": "goodbye",
                "patterns": [
                    "Bye",
                    "See you later",
                    "Goodbye",
                    "Talk to you later"
                ],
                "responses": [
                    "See you later, thanks for visiting",
                    "Have a nice day",
                    "Bye! Come back again soon."
                ]
            }
        ]
    }
    f.write(json.dumps(contents, indent=4))

    return redirect(url_for('Done'))

# Registration Completed #
@app.route('/Done')
def Done():
    return render_template("done.html")

# Admin Login Verification #
@app.route('/ToAdmin',methods=['POST'])
def ToAdmin():
    if request.method == 'POST':
        entered_username = request.form['AdminName']
        entered_email = request.form['code']
        entered_password = request.form['password']

        sqlQuery = "SELECT `AdminName`, `OrgCode`, `Password`, `orgAbbr` FROM `AdminLogin`"
        cursor.execute(sqlQuery)
        result = cursor.fetchall()
        for row in result:
            name = row[0]
            email = str(row[1])
            psw = row[2]
            abbr = row[3]
        #connection.close()
            if entered_username==name and entered_email==email and sha256_crypt.verify(entered_password,psw):
                session['user'] = entered_username
                global gblAbbr
                gblAbbr = abbr
                return redirect(url_for('admin'))
            else:
                gblAbbr = ""
    return redirect(url_for('main1'))

# Chatbot Response #
@app.route("/get")
def get_bot_response():
    inp = request.args.get('note')
    results = model.predict([bag_of_words(inp, words)])
    results_index = numpy.argmax(results)
    tag = labels[results_index]
    flag1 = 0
    for tg in data["intents"]:
        if tg['tag'] == tag:
            flag1 = 1
            responses = tg['responses']
    if(flag1):
        return random.choice(responses)
    else:
        return "Sorry! Some problem occured while answering your question. Please ask your question in a different way."

# Organization Code Verification #
@app.route("/submitCode")
def MatchCode():
    userCode = request.args.get('r')
    codeQuery = "SELECT * FROM `AdminLogin`"
    cursor.execute(codeQuery)
    result = cursor.fetchall()
    for row in result:
        n = row[1]
        o = row[2]
        #connection.close()
        if str(n) == str(userCode):
            val = o+".json"
            global data, words, labels, training, output
            with open(val) as file:
                data = json.load(file)
            try:
                with open("data.pickle", "rb") as f:
                    f.truncate(0)
                    words, labels, training, output = pickle.load(f)
            except:
                words = []
                labels = []
                docs_x = []
                docs_y = []

                for intent in data["intents"]:
                    for pattern in intent["patterns"]:
                        wrds = nltk.word_tokenize(pattern)
                        words.extend(wrds)
                        docs_x.append(wrds)
                        docs_y.append(intent["tag"])
                    if intent["tag"] not in labels:
                        labels.append(intent["tag"])

                words = [stemmer.stem(w.lower()) for w in words if w != "?"]
                words = sorted(list(set(words)))

                labels = sorted(labels)

                training = []
                output = []

                out_empty = [0 for _ in range(len(labels))]

                for x, doc in enumerate(docs_x):
                    bag = []

                    wrds = [stemmer.stem(w.lower()) for w in doc]
                    for w in words:
                        if w in wrds:
                            bag.append(1)
                        else:
                            bag.append(0)

                    output_row = out_empty[:]
                    output_row[labels.index(docs_y[x])] = 1

                    training.append(bag)
                    output.append(output_row)

                training = numpy.array(training)
                output = numpy.array(output)

                with open("data.pickle", "wb") as f:
                    pickle.dump((words, labels, training, output), f)

            tensorflow.reset_default_graph()

            net = tflearn.input_data(shape=[None, len(training[0])])
            net = tflearn.fully_connected(net, 8)
            net = tflearn.fully_connected(net, 8)
            net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
            net = tflearn.regression(net)
            global model
            model = tflearn.DNN(net)

            model.fit(training, output, n_epoch=500, batch_size=8, show_metric=True)
            model.save(o+"model.tflearn")
            return str(1)
    return str(0)

# If Admin Login Successfull, Redirecting to Admin Page #
@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect(url_for('main1'))
    global file_name
    file_name = "{0}.json".format(gblAbbr)
    print()
    con = json.load(open(file_name))
    con = con['intents']
    return render_template('admin.html', con=con)

@app.route('/insertData', methods=['POST'])
def insertD():
    try:
        a = request.form['a']
        b = json.loads(request.form['b'])
        c = json.loads(request.form['c'])
        if len(a)==0:
            raise Exception("No Value Entered")
        #print(a,b,c,sep=" : ")
        with open(file_name) as json_file:
            data = json.load(json_file)
            temp = data['intents']
            b1 = []
            c1 = []
            for i in b:
                if len(i)==0:
                    raise Exception("No Value Entered")
                b1.append(i)
            for i in c:
                if len(i)==0:
                    raise Exception("No Value Entered")
                c1.append(i)
            f = {
                "tag": a,
                "patterns": b1,
                "responses": c1
            }
            temp.append(f)
            temp = {
                "intents": temp
            }
        open(file_name, "w").write(
            json.dumps(temp, indent=4)
        )
    except:
        return "0"

    return "1"

@app.route('/updateData', methods=['POST'])
def updateD():
    try:
        t = request.form['tag'].strip()
        d = json.loads(request.form['updateData'])
        d1 = []
        flag = 1
        for i in d:
            if len(i)==0:
                raise Exception("No Value Entered")
            d1.append(i)
        obj = json.load(open(file_name))
        for i in range(len(obj['intents'])):
            if str(obj['intents'][i]['tag']) == str(t):
                obj['intents'][i]['responses'].clear()
                obj['intents'][i]['responses'] = d1
                flag = 0
                break
        open(file_name, "w").write(
            json.dumps(obj, indent=4, separators=(',', ': '))
        )
    except:
        return "0"
    if flag == 0:
        return "1"
    else:
        return "0"


@app.route('/deleteData', methods=['POST'])
def DeleteD():
    flag = 1
    try:
        DelT = request.form['tag'].strip()
        obj = json.load(open(file_name))
        for i in range(len(obj['intents'])):
            if str(obj['intents'][i]['tag']) == str(DelT):
                flag = 0
                obj['intents'].pop(i)
                break

        open(file_name, "w").write(
            json.dumps(obj, indent=4, separators=(',', ': '))
        )
    except:
        return "0"
    if flag==0:
        return "1"
    else:
        return "0"

@app.route('/viewData', methods=['POST'])
def ViewD():
    flag = 1
    view_a = []
    view_b = []
    try:
        Tags = request.form['tag'].strip()
        obj = json.load(open(file_name))
        for i in range(len(obj['intents'])):
            if str(obj['intents'][i]['tag']) == str(Tags):
                flag = 0
                view_a = obj['intents'][i]['patterns']
                view_b = obj['intents'][i]['responses']
                break
    except:
        return "0"
    if flag==0:
        return jsonify({'var1': view_a, 'var2': view_b})
    else:
        return "0"

@app.route('/changePassword', methods=['POST'])
def changePSW():
    flag = 1
    try:
        old_Pass = request.form['old_Pass'].strip()
        new_Pass = request.form['new_Pass'].strip()
        sqlQuery = "SELECT `AdminName`, `Password` FROM `AdminLogin`"
        cursor.execute(sqlQuery)
        result = cursor.fetchall()
        for row in result:
            name = row[0]
            p = row[1]
            if session['user']==name and sha256_crypt.verify(old_Pass, p):
                temp = sha256_crypt.hash(new_Pass)
                updateQuery = "Update `AdminLogin` Set Password = '{0}' Where AdminName = '{1}';".format(temp, name)
                cursor.execute(updateQuery)
                flag = 0
                break
            else:
                flag = 1
    except:
        return "0"
    if flag==0:
        return "1"
    else:
        return "2"

# Admin Page Logout #
@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user',None)
        return redirect(url_for('main1'))
    else:
        return "<p> Already Logged Out </p>"

if __name__ == '__main__':
    #app.run(host='192.168.225.137',debug=True)
    app.run(debug=True)