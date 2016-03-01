from werkzeug.security import generate_password_hash, check_password_hash
from database import *
from gridfs import GridFS
import random, string, base64
db = Database(drop_db = False)
image_collection = GridFS(db.db, 'images')


class User():
    collection = 'users'
    def __init__(self, username, password):
        # print username, password
        self.info = {}
        self.info['username'] = username
        self.info['password'] = generate_password_hash(password)
        self.info['memories'] = []
        self.info['memory_count'] = 0

    def save(self):
        # print 'Adding user', self.info
        return db.add_entry(self)

    @staticmethod
    def find_all():
        return db.get_collection(User.collection)

    @staticmethod
    def find(query_dict):
        result = db.find_entry(User.collection, query_dict)
        if result:
            user = User(result['username'], result['password'])
            user.info = result
            return user
        else:
            return

    @staticmethod
    def auth_by_token(token, username):
        # print 'inside auth_by_token',token, username
        # decrypted = 'justsomethingtoresetthecookie'
        decrypted = base64.b64decode(token).split("_")[1]
        # print 'username is',username,'decrypted token has',decrypted,'equal?', username == decrypted
        return decrypted == username


    def authenticate(self, username, password):
        # print 'username =',username,"password =",password
        if check_password_hash(self.info['password'], password):
            token = ''.join(random.choice(string.lowercase) for i in range(8))+"_"+username+"_"+''.join(random.choice(string.lowercase) for i in range(8))
            if len(token)%3 > 0:
                token = token[:len(token)-len(token)%3]
            encrypted = base64.b64encode(token)
            return encrypted
        else:
            return None

    def set_password(self, password):
        self.password = generate_password_hash(password)
        return

    def get_memories_with_image_data(self):
        for memory in self.info['memories']:
            if image_collection.exists(memory['image']):
                memory['image_data'] = base64.b64encode(image_collection.get(memory['image']).read())
                # print 'memory data received'
            else:
                memory['image_data'] = None
        return self.info['memories']

    def add_memory(self, memory_dict, image):
        # TODO: Add images and save to image_collection
        print 'memory dict in user.add_memory',memory_dict
        if image:
            image_id = image_collection.put(image)
            print 'added image to gridfs. image_id =',image_id
            memory_dict['image'] = image_id
        self.info['memory_count'] += 1
        memory_dict['id'] = self.info['memory_count']
        self.info['memories'].append(memory_dict)
        res = db.update_entry({'username': self.info['username']}, self)
        return res

    def delete_memory(self, memory_id):
        # TODO: Delete all relevant images too
        memory = filter(lambda (mem): mem['id'] == int(memory_id), self.info['memories'])[0]
        print 'to delete this -',memory,memory['image']
        if image_collection.exists(memory['image']):
            image_collection.delete(memory['image'])
        self.info['memories'] = filter(lambda (mem): mem['id'] != int(memory_id), self.info['memories'])
        res = db.update_entry({'username': self.info['username']}, self)
        return res

