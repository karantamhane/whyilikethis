from flask import Flask, request, render_template, redirect, url_for, make_response
from bson import ObjectId
from gridfs import GridFS
from models import *
from database import Database

app = Flask(__name__)
app.db = Database()
app.image_collection = GridFS(app.db.db, 'images')

@app.route('/sign_up/', methods = ['GET','POST'])
def sign_up():
    if request.method == 'POST':
        # Display sign up form for user account creation
        username = request.form["new_username"]
        if User.find({'username': username}):
            return render_template('signup.html', error = "User already exists! Choose a different username or login")
        pswd = request.form["new_password"]
        if pswd == request.form["confirm_password"]:
            password = pswd
        else:
            return render_template('signup.html', error = "Password values do not match!")
        print 'creating new user now with username',username,'and password',password
        new_user = User(username, password)
        print 'new user is',new_user.info
        saved = new_user.save()
        if saved:
            auth_token = new_user.authenticate(username, password)
            if auth_token != '':
                response = make_response(redirect(url_for('account', username = username)))
                response.set_cookie('username', username)
                response.set_cookie('auth_token', auth_token)
                return response
            return redirect(url_for('login'))
        else:
            return render_template('signup.html')
    else:
        return render_template('signup.html')

@app.route('/', methods = ['GET', 'POST'])
@app.route('/login/', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form["username"]
        user = User.find({'username': username})
        if user:
            password = request.form["password"]
        else:
            return redirect(url_for('sign_up')) #TODO: add error msg

        auth_token = user.authenticate(username, password)
        if auth_token and auth_token != '':
            response = make_response(redirect(url_for('account', username = username)))
            response.set_cookie('username', username)
            response.set_cookie('auth_token', auth_token)
            return response
        else:
            return render_template('login.html', error = "Could not authenticate user. Please try again.")
    else:
        auth_token = request.cookies.get('auth_token', None)
        username = request.cookies.get('username', None)
        if auth_token and auth_token != '':
            return redirect(url_for('account', username = username))
        return render_template('login.html')

@app.route('/<username>/account/')
def account(username):
    auth_token = request.cookies.get('auth_token')
    if User.auth_by_token(auth_token, username):
        user = User.find({'username': username})
        # user.info['memories'] = user.get_memories_with_image_data()
        return render_template('account.html', user = user.info)
    else:
        return redirect(url_for('logout'))

@app.route('/<username>/account/add_memory', methods = ['GET', 'POST'])
def add_memory(username):
    if request.method == 'GET':
        return render_template('add_memory.html', username = username)
    elif request.method == 'POST':
        name = request.form['name']
        desc = request.form['description']
        address = request.form['address']
        image = request.files['image']
        # print 'added image has filename:',image.filename

        user = User.find({'username': username})
        user.add_memory({'name': name, 'address': address, 'description': desc, 'image': None}, image)
        return redirect(url_for('account', username = username))

@app.route('/<username>/account/delete_memory/<memory_id>/', methods = ['POST'])
def delete_memory(username, memory_id):
    user = User.find({'username': username})
    user.delete_memory(memory_id)
    return redirect(url_for('account', username = username))

@app.route('/get_image/<image_id>/', methods = ['GET'])
def get_image(image_id):
    image_id = ObjectId(image_id)
    if app.image_collection.exists(image_id):
        image = app.image_collection.get(image_id)
        response = make_response(image.read())
        response.mimetype = "image/png"
        return response
    else:
        return make_response("No image for this memory")


@app.route('/account/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('username', '')
    response.set_cookie('auth_token', '')
    return response

if __name__ == '__main__':
    app.run()