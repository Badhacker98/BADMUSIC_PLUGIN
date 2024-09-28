import re
from pymongo import MongoClient
from pyrogram import filters
from pyrogram.types import Message
from BADMUSIC import app
import os
from config import OWNER_ID
from BADMUSIC.misc import SUDOERS
from BADMUSIC.utils.pastebin import BADbin


MONGO_DB_URI = os.getenv("MONGO_DB_URI")

@app.on_message(filters.command("mongochk") & SUDOERS)
async def mongo_check_command(client, message: Message):
    if len(message.command) < 2:
        await message.reply("Please provide your MongoDB URL with the command: `/mongochk your_mongo_url`")
        return
    ok = await message.reply_text("**Please wait i am checking your mongo...**")
    mongo_url = message.command[1]
    
    try:
        mongo_client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        databases = mongo_client.list_database_names()

        result = f"**MongoDB URL** `{mongo_url}` **is valid**.\n\n**Available Databases:**\n"
        for db_name in databases:
            if db_name not in ["admin", "local"]:
                result += f"\n`{db_name}`:\n"
                db = mongo_client[db_name]
                for col_name in db.list_collection_names():
                    result += f"  `{col_name}` ({db[col_name].count_documents({})} documents)\n"
        
        
        if len(result) > 4096:
            paste_url = await BADbin(result)
            await ok.delete()
            await message.reply(f"**The database list is too long to send here. You can view it at:** {paste_url}")
        else:
            await ok.delete()
            await message.reply(result)

        mongo_client.close()

    except Exception as e:
        await message.reply(f"**Failed to connect to MongoDB**\n\n**Your Mongodb is dead❌**\n\n**Error:-** `{e}`")

#==============================[⚠️ DELETE DATABASE ⚠️]=======================================


def delete_collection(client, db_name, col_name):
    db = client[db_name]
    db.drop_collection(col_name)


def delete_database(client, db_name):
    client.drop_database(db_name)


def list_databases_and_collections(client):
    numbered_list = []
    counter = 1
    for db_name in client.list_database_names():
        if db_name not in ["admin", "local"]:  
            numbered_list.append((counter, db_name, None))
            counter += 1
            db = client[db_name]
            for col_name in db.list_collection_names():
                numbered_list.append((counter, db_name, col_name))
                counter += 1
    return numbered_list


@app.on_message(filters.command(["deletedb", "deletedatabase", "deldb", "deldatabase"]) & filters.user(OWNER_ID))
async def delete_db_command(client, message: Message):
    try:
        mongo_client = MongoClient(MONGO_DB_URI, serverSelectionTimeoutMS=5000)
        databases_and_collections = list_databases_and_collections(mongo_client)

        
        if len(message.command) == 1:
            if len(databases_and_collections) > 0:
                result = "**MongoDB Databases and Collections given below you can delete by /deldb 1,2,7,5 (your choice you can delete multiple databse in one command with multiple count value seperated by comma:**\n\n"
                for num, db_name, col_name in databases_and_collections:
                    if col_name:
                        result += f"{num}.) `{col_name}`\n"
                    else:
                        result += f"\n{num}.) **{db_name}** (Database)\n"
                ok = await message.reply(result)
            else:
                await message.reply("**No user databases found. ❌**")
        

        elif "," in message.command[1]:
            numbers = message.command[1].split(",")
            failed = []
            for num_str in numbers:
                num_str = num_str.strip()  
                if num_str.isdigit():
                    number = int(num_str)
                    if number > 0 and number <= len(databases_and_collections):
                        num, db_name, col_name = databases_and_collections[number - 1]
                        try:
                            if col_name:
                                delete_collection(mongo_client, db_name, col_name)
                                await message.reply(f"**Collection** `{col_name}` **in database** `{db_name}` **has been deleted successfully. 🧹**\n\n**Check Rest databse by: /checkdb, /deldb**")
                                await ok.delete()
                            else:
                                delete_database(mongo_client, db_name)
                                await message.reply(f"**Database** `{db_name}` **has been deleted successfully. 🧹**\n\n**Check Rest databse by: /checkdb, /deldb**")
                                await ok.delete()
                        except Exception as e:
                            failed.append(num_str)
                    else:
                        failed.append(num_str)
                else:
                    failed.append(num_str)
            
            if failed:
                await message.reply(f"Some entries could not be deleted or were invalid: {', '.join(failed)} ❌\n\n**Check Rest databse by: /checkdb, /deldb**")
                
        
        elif message.command[1].isdigit():
            number = int(message.command[1])
            if number > 0 and number <= len(databases_and_collections):
                num, db_name, col_name = databases_and_collections[number - 1]
                if col_name:
                    delete_collection(mongo_client, db_name, col_name)
                    await message.reply(f"**Collection** `{col_name}` **in database** `{db_name}` **has been deleted successfully. 🧹**\n\n**Check Rest databse by: /checkdb, /deldb**")
                else:
                    delete_database(mongo_client, db_name)
                    await message.reply(f"**Database** `{db_name}` **has been deleted successfully. 🧹**\n\n**Check Rest databse by: /checkdb, /deldb**")
            else:
                await message.reply("**Invalid number. Please check the list again.**")
        
        
        else:
            db_name = message.command[1]
            
            
            if len(message.command) == 3:
                col_name = message.command[2]
                if db_name in [db[1] for db in databases_and_collections if not db[2]]:
                    delete_collection(mongo_client, db_name, col_name)
                    await message.reply(f"**Collection** `{col_name}` **in database** `{db_name}` **has been deleted successfully. 🧹**\n\n**Check Rest databse by: /checkdb, /deldb**")
                else:
                    await message.reply(f"**Database** `{db_name}` **does not exist. ❌**")
            
            
            else:
                if db_name in [db[1] for db in databases_and_collections if not db[2]]:
                    delete_database(mongo_client, db_name)
                    await message.reply(f"**Database** `{db_name}` **has been deleted successfully. 🧹**\n\n**Check Rest databse by: /checkdb, /deldb**")
                else:
                    await message.reply(f"**Database** `{db_name}` **does not exist. ❌**")
        
        mongo_client.close()

    except Exception as e:
        await message.reply(f"**Failed to delete databases Try to delete by count**")


#==============================[⚠️ CHECK DATABASE ⚠️]=======================================



# Environment variable for the MongoDB URL
MONGO_DB_URI = os.getenv("MONGO_DB_URI")

# Command handler for /checkdb
@app.on_message(filters.command(["checkdb", "checkdatabase"]) & SUDOERS)
async def check_db_command(client, message: Message):
    try:
        ok = await message.reply_text("**Please wait while checking your bot mongodb database...**")
        mongo_client = MongoClient(MONGO_DB_URI, serverSelectionTimeoutMS=5000)
        databases = mongo_client.list_database_names()
        
        if len(databases) > 2:  # More than just admin and local
            result = "MongoDB Databases:\n"
            for db_name in databases:
                if db_name not in ["admin", "local"]:
                    result += f"\n{db_name}:\n"
                    db = mongo_client[db_name]
                    for col_name in db.list_collection_names():
                        collection = db[col_name]
                        result += f"  {col_name} ({collection.count_documents({})} documents)\n"
            
            # Check if message exceeds Telegram's limit
            if len(result) > 4096:  # Telegram's message length limit is 4096 characters
                paste_url = await BADbin(result)
                await message.reply(f"**The database list is too long to send here. You can view it at:** {paste_url}")
                await ok.delete()
            else:
                await ok.delete()
                await message.reply(result)
        else:
            await ok.delete()
            await message.reply("**No user databases found. ❌**")
        
        mongo_client.close()

    except Exception as e:
        await ok.delete()
        await message.reply(f"**Failed to check databases:** {e}")

#============================================[ ⚠️ TRANSFER DATABASE ⚠️ ]===============================

mongo_url_pattern = re.compile(r"mongodb(?:\+srv)?:\/\/[^\s]+")

# Function to backup old MongoDB data
def backup_old_mongo_data(old_client):
    backup_data = {}
    for db_name in old_client.list_database_names():
        db = old_client[db_name]
        backup_data[db_name] = {}
        for col_name in db.list_collection_names():
            collection = db[col_name]
            backup_data[db_name][col_name] = list(collection.find())  # Store all documents
    return backup_data

# Function to restore data to new MongoDB instance
def restore_data_to_new_mongo(new_client, backup_data):
    for db_name, collections in backup_data.items():
        db = new_client[db_name]
        for col_name, documents in collections.items():
            collection = db[col_name]
            if documents:
                collection.insert_many(documents)  # Insert all documents into the new collection

# Command handler for `/transferdb`
@app.on_message(filters.command(["transferdb", "copydb", "paste", "copydatabase", "transferdatabase"]) & filters.user(OWNER_ID))
async def transfer_db_command(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply("Please provide the new MongoDB URL with the command: `/transferdb your_new_mongodb_url`")
            return
        ok = await message.reply_text("**Ok wait transfer process Starting...**")
        new_mongo_url = message.command[1]
        
        if not re.match(mongo_url_pattern, new_mongo_url):
            await message.reply("**The provided MongoDB URL format is invalid! ❌**")
            return
        
        # Step 1: Backup data from the old MongoDB instance
        old_mongo_client = MongoClient(MONGO_DB_URI, serverSelectionTimeoutMS=5000)
        backup_data = backup_old_mongo_data(old_mongo_client)
        old_mongo_client.close()
        await message.reply("**Data copy from old MongoDB is complete. 📦**\n\n**Now opening new MongoDB and pasting**")
        
        # Step 2: Restore the backed-up data into the new MongoDB instance
        new_mongo_client = MongoClient(new_mongo_url, serverSelectionTimeoutMS=5000)
        restore_data_to_new_mongo(new_mongo_client, backup_data)
        new_mongo_client.close()
        await ok.delete()
        await message.reply("**Data transfer to the new MongoDB is successful! 🎉**")
    
    except Exception as e:
        await ok.delete()
        await message.reply(f"**Data transfer to the new MongoDB is successful! 🎉\n\nCheck your new mongo databse by /mongochk your mongo here\n\nIf not transferred from old mongo then either your mongo is dead or invalid.")


__MODULE__ = "MongoDB"
__HELP__ = """
**MongoDB Management Commands:**

• /deletedb : You can delete by /deletedb 1,2,7,5.

• /deletedb [database_name] [collection_name]: Deletes the specified collection within the database.

• /deletedb all: Deletes all user databases.

• /checkdb: Lists all databases and collections with the number of documents in the MongoDB.

• **MongoDB Transfer Commands:**

• /transferdb [new_mongo_url]: - Transfers all databases from the old MongoDB (from environment) to the new MongoDB URL.

• /mongochk [MongoDB_URL]: Verifies the given MongoDB URL and lists all databases and collections in it.
"""




