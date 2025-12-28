from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class UserRepository:
    def __init__(self, db):
        self.users = db["users"]

    def create(self, username, password, is_admin=False):
        hashed = generate_password_hash(password)
        user = {
            "username": username,
            "password": hashed,
            "is_admin": is_admin,
            "stats": {"wins": 0, "losses": 0, "draws": 0}  
        }
        result = self.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        return user
    
    def find_by_username(self, username):
        return self.users.find_one({"username": username})

    def find_by_id(self, id):
        return self.users.find_one({"_id": ObjectId(id)})

    def find_all(self):
        return list(self.users.find({}, {"password": 0}))

    def update(self, id, data):
        if "password" in data:
            data["password"] = generate_password_hash(data["password"])
        result = self.users.update_one({"_id": ObjectId(id)}, {"$set": data})
        return result.modified_count > 0

    def delete(self, id):
        result = self.users.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    def update_stats(self, user_id, result):
        if result not in ["wins", "losses", "draws"]:
            return
        

        self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {f"stats.{result}": 1}}
        )
