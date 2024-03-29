# Generic imports
import datetime
from typing import Optional, Union
import re

# FireBase Stuff
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Use a service account to set up DB.
cred = credentials.Certificate('fbdbpractice-firebase-adminsdk-teuw8-4dcece3d0f.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()


class User:
    def __init__(self, userId, first, last, email, birth, gender, freePassUsed=False, tokenProfile=None, history=None,
                 scheduled=None, memberships=None, settings=None):
        self.userId = userId
        self.first = first
        self.last = last
        self.email = email
        self.birth = birth
        self.gender = gender
        self.freePassUsed = bool(freePassUsed)
        self.tokenProfile = tokenProfile or []
        self.history = history or []
        self.scheduled = scheduled or []
        self.memberships = memberships or []
        self.settings = settings or {}

    @staticmethod
    def from_dict(data: dict):
        """
        Given a dictionary, construct an instance of this User class. Purpose of this function is purely for dealing
          with confirmed existing entries => existence authentication is not necessary. Purely for fetching from DB
        :param data: a dictionary with unknown keys. there are certain mandatory keys whose presence must be checked.
        everything after that is nunez
        :return: a User instance.
        """

        # Bunch of asserts that the required dict keys exist.
        # Done: Figure out whether userId construction occurs here or whether its a necessary key. not necessary
        # TODO: Figure out the potential keys.

        mandatory_keys = ['user_id', 'first_name', 'last_name', 'email', 'birthdate', 'gender']
        all_keys = ['userId', 'first_name', 'last_name', 'email', 'birthdate', 'gender', 'free_pass_used',
                    'token_profile', 'history', 'scheduled', 'memberships', 'settings']
        values = []
        keys = set(data.keys())

        if not keys.issuperset(mandatory_keys):
            print('missing keys')
            # TODO: Missing info case. figure out error handling for missing info.
            pass
        else:
            for key in all_keys:
                values.append(data.get(key, None))  # essential keys will work, others will work if they dont exist.

            return User(*values)  # this will unpack the created list into the init parameters.

    def to_dict(self) -> list[str, dict]:
        """
        A function to create a universal dict from self.
        :param self: self
        :return: list wth the userId then the rest of the info in a dict
        """
        return [self.userId, {
            "first_name": self.first,
            "last_name": self.last,
            "email": self.email,
            "birthdate": self.birth,
            "gender": self.gender,
            "free_pass_used": self.freePassUsed,
            "token_profile": self.tokenProfile,
            "history": self.history,
            "scheduled": self.scheduled,
            "memberships": self.memberships,
            "settings": self.settings
        }]


def hash_name(first: str, last: str) -> str:
    """
    returns a hash of the full name to return a unique userId
    :param first: first name
    :param last: last name
    :return: hash
    """

    # return first three letters of each name followed by length of each name. ***for now***
    # e.g has_name(Abdelrahman, Alkhawas) -> Abd11Alk8
    return f'{first[:3]}{len(first)}{last[:3]}{len(last)}'


def valid_email(email: str) -> bool:
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return bool(re.fullmatch(regex, email))


def create_profile(first_name: str, last_name: str, email: str, birth: str, gender: str, member: Optional[bool]) -> bool:
    """
    A function that creates a new profile then adds it to the database
    :param first_name: self-explanatory
    :param last_name: self-explanatory
    :param email: self-explanatory
    :param birth: Birthdate. Used to determine age as well. Must be structured 'DD-MM-YYYY'
    :param gender: UI should restrict options to either Male or Female.
    :param member: Optional Bool representing whether the new user has come in with a member ship.
    :return: Boolean represnting success of database appendage.
    """

    user_id, name = hash_name(first_name, last_name), f'{first_name} {last_name}'

    if not valid_email(email):
        return False

    # ensure person doesn't already exist in the database
    users = db.collection("Users").stream()
    for user in users:
        if user.id == user_id:
            # TODO: Person exists, Raise some kind of safe error
            return False
        print(f'{user.id} => {user.to_dict()}')

    # TODO: Figure out birthdate format
    birth = birth.split('-')
    birth_dt = datetime.datetime(int(birth[2]), int(birth[1]), int(birth[0]))
    # birth_dt = birth

    assert gender in ['Male', 'Female']

    # create User
    new_user = User(user_id, first_name, last_name, email, birth_dt, gender, memberships=[member])
    new_user_info = new_user.to_dict()
    print(new_user.to_dict())
    # add user to DB
    db.collection("Users").document(new_user_info[0]).set(new_user_info[1])

    # TODO: figure out history management.
    return True


def fetch(user_id: str) -> Union[User, bool]:
    """
    Fetch a file from the DB with a given user_id
    :param user_id: duh
    :return: either a User object, or False
    """
    # users = db.collection("Users").stream()
    doc_ref = db.collection("Users").document(user_id)
    doc = doc_ref.get()
    if doc.exists:
        print(doc.to_dict())
        fetched = doc.to_dict()
        fetched['user_id'] = user_id
        user = User.from_dict(fetched)
        return user
    else:
        print('DNE')
        return False


def delete_user(user_id: str) -> datetime:
    """
    delete an entire user based on user_id
    :param user_id:  duh
    :return: timestamp of deletion if successful.
    """
    if db.collection("Users").document(user_id).get().exists:
        # TODO: figure out history management.
        return db.collection("Users").document(user_id).delete()


def edit_user(user_id: str, field: str) -> datetime:
    pass


create_profile('Abdelrahman', 'Alkhawas', 'abderlahman_khawas@hotmail.com', '04-10-2001', 'Male', False)
create_profile('Ahmed', 'Abdelaziz', 'ahmed.ym.tawfik@gmail.com', '19-07-2002', 'Male', False)
create_profile('Omar', 'Zeid', 'omar.kmaz@gmail.com', '21-09-2000', 'Male', False)