import base64
from bson.objectid import ObjectId
from pprint import pprint
from os import environ

from ..models.user_model import User
import database


def create_user_from_cursor(cursor):
    """
    Returns a user object populated with data from a pymongo cursor

    Parameters
    ----------
    cursor : pymongo_cursor
    Database information to load into user object

    Returns
    -------
    User Object on success
    Empty dict on failure
    """

    s = {}
    if cursor:
        s = User(cursor['_id'],
                    cursor['username'],
                    cursor['forename'],
                    cursor['surname'],
                    cursor['profile_about'],
                    cursor['profile_image'],
                    cursor['subjects'])

    return s


#Accepts get_user_by_name("Bob Loblaw") and get_user_by_name("Bob", "Loblaw")
def get_user_by_name(name, surname=None):
    #If name is one variable seperated by space
    #Split it and store those values in name and surname
    if surname is None:
        names = name.split(" ")
        if(len(names) != 2):
            raise TypeError(f"Expected two names found {name}")
        else:
            name = names[0]
            surname = names[1]

    if database.mongo.db.users.count_documents({'forename': name,
                                       'surname': surname}) > 0:

        return list(map(create_user_from_cursor,
                        database.mongo.db.users.find({'forename': name,
                                                 'surname': surname})
                        ))

    else:
        raise NameError(f"User {name} {surname} could not be found.")


def get_user_by_id(user_id):
    """
    Returns User object for user of user_id

    Parameters
    ----------
    user_id : str
    Unique ID of user

    Returns
    -------
    Empty dict on error
    Otherwise a user object (see /models/user_model.py)
    """

    try:
        cursor = database.mongo.db.users.find_one({'_id':ObjectId(user_id)})
        return create_user_from_cursor(cursor)
    except:
        return {}

def generate_menu_items(user_id):
    pipeline = [ {"$unwind": "$subjects"},
                {"$group": 
                    {
                        "_id":"$subjects.subject",
                        "courses": {
                            "$addToSet": "$subjects.course"
                                    }
                    }
                } ]

    menu_items = list(database.mongo.db.users.aggregate(pipeline))
    return menu_items

def get_subject_content(user_id, subject_name):
    """
    Returns an overview of a subject for a user

    Parameters
    ----------
    user_id : str
    ID of the user to use
    subject_name : str
    Name of the subject we want to overview of

    Return
    ------
    Empty dictionary on error.
    On success: {'avg_grade':float, 'num_courses': int}
    """
    pipeline = [
                { "$match": {"_id":ObjectId(user_id)} },
                {"$unwind": "$subjects"},
                { "$match": {"subjects.subject": subject_name}},
                {"$group":
                    {
                        "_id":"$subjects.subject",
                        "courses": {
                            "$addToSet": "$subjects.course"
                                    },
                        "avg_grade": { "$avg":"$subjects.grade"}
                    }
                } ]
    results = list( database.mongo.db.users.aggregate(pipeline) )
    subject_content = {}
    if results:
        subject_content.update({'avg_grade':results[0]['avg_grade'],
            'num_courses':len(results[0]['courses'])})
    return subject_content


def allowed_file(filename):
    """Checks if the filename provided is permitted 

    Permitted if it contains a '.' and the file extension is listed
    in the ALLOWED_EXTENSIONS in the .env file
    """

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in \
        environ.get('ALLOWED_EXTENSIONS')


def update_user_profile(user_id,new_profile_data):
    """
    Updates users profile about and image if changed

    Parameters
    ----------
    user_id : str
    Unique ID of user

    profile_data : dict
    { 'profile_about':str, profile_img: }
    """

    user = get_user_by_id(user_id) 
    flashed_message = ("There was a problem updating your profile","alert-danger")

    if 'profile_about' in new_profile_data:
        if user.profile_about != new_profile_data['profile_about']:
            user.profile_about = new_profile_data['profile_about']
            flashed_message = ("Profile updated.","alert-success")
    
    if 'profile_img' in new_profile_data:
        new_image = new_profile_data['profile_img']

        if new_image and allowed_file(new_image.filename):
            encoded_img = base64.b64encode(new_image.read()).decode()
            filetype = new_image.filename.rsplit('.', 1)[1].lower()
            img_data = f'data:image/{filetype};base64,{encoded_img}'
            database.mongo.db.users.update_one({'_id':user.id},
                    {'$set':
                        {
                    'profile_image': img_data
                        }
                    })

            flashed_message = ("Profile updated.", "alert-success") 
    return flashed_message

def get_students_of_course(subject, course):
    student = create_user_from_cursor(database.mongo.db.users.find_one(
            {'$and': [
                {'subjects.subject': subject},
                {'subjects.course':course},
                {'is_teacher':False}
                ]}
            ))

    return 'students' 
