from flask import Flask, request, render_template, redirect, url_for, make_response
from models import *
# db = Database()
app = Flask(__name__)


@app.route('/sign_up/', methods = ['GET','POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form["new_username"]
        if User.find({'username': username}):
            # print 'found existing user'
            # TODO: add link to login page
            return render_template('signup.html', error = "User already exists! Choose a different username or login here")
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
        # print 'auth token =', auth_token
            if auth_token != '':
                # TODO: Store the token in a cookie
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
        # print 'auth token =', auth_token
        if auth_token != '':
            # TODO: Store the token in a cookie
            response = make_response(redirect(url_for('account', username = username)))
            response.set_cookie('username', username)
            response.set_cookie('auth_token', auth_token)
            return response
        else:
            return render_template('login.html', error = "Could not authenticate user. Please try again.")
    else:
        # TODO: Check for auth token and redirect to account page if valid
        # print 'before getting session id'
        auth_token = request.cookies.get('auth_token', None)
        username = request.cookies.get('username', None)
        if auth_token != '':
            # print 'auth token =',auth_token,'username',username
            return redirect(url_for('account', username = username))
        return render_template('login.html')

@app.route('/<username>/account/')
def account(username):
    auth_token = request.cookies.get('auth_token')
    if User.auth_by_token(auth_token, username):
        user = User.find({'username': username})
        print 'calling get_memories_with_image_data'
        user.info['memories'] = user.get_memories_with_image_data()
        # print 'user info is',user.info
        return render_template('account.html', user = user.info)
    else:
        return redirect(url_for('logout'))

@app.route('/<username>/account/add_memory', methods = ['GET', 'POST'])
def add_memory(username):
    if request.method == 'GET':
        return render_template('add_memory.html')
    elif request.method == 'POST':
        name = request.form['name']
        desc = request.form['description']
        address = request.form['address']
        image = request.files['image']
        # print name,desc,address,image
        user = User.find({'username': username})
        # TODO: Store image in gridfs and insert id in image field of memory
        print 'before add_memory in app'
        # TODO: Maybe write a static method to store image in User and use image id?
        user.add_memory({'name': name, 'address': address, 'description': desc, 'image': None}, image)

        # auth_token = request.cookies.get('auth_token')
        # print 'in route add_memory',user.info
        return redirect(url_for('account', username = username))

@app.route('/<username>/account/delete_memory/<memory_id>/', methods = ['POST'])
def delete_memory(username, memory_id):
    user = User.find({'username': username})
    # print 'called delete_memory for',user.info
    user.delete_memory(memory_id)

    # auth_token = request.cookies.get('auth_token')
    return redirect(url_for('account', username = username))

@app.route('/account/logout')
def logout():
    # TODO: Update cookies, redirect to login page
    response = make_response(redirect(url_for('login')))
    response.set_cookie('username', '')
    response.set_cookie('auth_token', '')
    return response

if __name__ == '__main__':
    app.run()
    db.close()
