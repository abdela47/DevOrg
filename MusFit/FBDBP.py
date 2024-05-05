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

# indicies for token profiles: [Football, BasketBall, ]
# DateTime string standard: DD-MM-YYYY;MM:HH

class Membership:
    def __init__(self, mem_name, token_profile, period, period_price):
        """
        Initiation Function
        :param mem_name: DisplayName of membership
        :param token_profile: Important Part
        :param period: One of either Weekly, Monthly, Quarterly, Yearly
        :param period_price:  Price to be delivered per period.
        """
        self.name: str = mem_name
        self.profile: dict = token_profile
        self.period = period
        self.price: float = period_price

    @staticmethod
    def from_dict(data: dict):
        """
        Return a membership from a dictionary coming from the DB
        :param data: the dictionary
        :return: Membership
        """
        values, keys = [], ["name", "Token Profile", "Period", "Period Price"]

        for key in keys:
            values.append(data.get(key))  # TODO: figure out how to make all keys non-optional

        return Membership(*values)


def create_membership_type(name: str, token_profile: dict[str, int], period: str, period_price: float):
    """
    Create and upload a membership type up to the DB
    :param name: DisplayName
    :param token_profile: dictionary that sends sports name to the number of tokens allowed per period
    :param period: either month, quarter, year or some other period.
    :param period_price: amount to be charged per period.
    :return: datetime (??)
    """

    new_mem_info = {"Token Profile": token_profile, "Period": period, "Period Price": period_price}
    db.collection("Memberships").document(name).set(new_mem_info)

    # TODO: Figure out History Management.
    return 1


class SingularEvent:
    def __init__(self, event_id, event_name, gender, sport, start_date_time, duration, capacity, enrolled=None,
                 tags=None, pending=None, waitlist=None):
        self.event_id = event_id
        self.event_name = event_name
        self.gender = gender
        self.sport = sport
        self.start_time = start_date_time
        self.duration = duration
        self.capacity = capacity
        self.enrolled = enrolled if enrolled is not None else []
        self.pending = pending if pending is not None else []
        self.waitlist = waitlist if waitlist is not None else []
        self.tags = tags if tags is not None else []

    @staticmethod
    def from_dict(data: dict):
        """
        Given a dictionary, construct an instance of this Event class. Purpose of this function is purely for dealing
            with confirmed existing entries => existence authentication is not necessary. Purely for fetching from DB
        :param data: a dictionary wth all key filled in. All keys are mandatory
        :return: an Event Instance.
        """
        values, keys = [], ["user_id", "event_id", "gender", "sport", "start_date_time", "duration", "capacity", "enrolled",
                            "tags", "pending", "waitlist"]

        for key in keys:
            values.append(data.get(key, None))

        return SingularEvent(*values)

    def to_dict(self) -> list[Union[str, dict]]:
        """
        a function to create a universal dict from self.
        :return: list with the event_id then the rest of the infoormation in a dict.
        """
        return [self.event_id,
                {"event_name": self.event_name,
                 "gender": self.gender,
                 "sport": self.sport,
                 "start_time": self.start_time,
                 "duration": self.duration,
                 "capacity": self.capacity,
                 "enrolled": self.enrolled,
                 "tags": self.tags,
                 "pending": self.pending,
                 "waitlist": self.waitlist}]

    def enroll_user(self, user_id) -> datetime:
        """
        Logic for enrolling user into a one time event. Figure out Queues, waitlists, capacities, buffer times...
        :param user_id: User to be enrolled into this singular event.
        :return: Datetime potentially for logging.
        """
        # DONE: Get user information
        user = fetch_user(user_id)
        tokens = user.tokenProfile  # token profile.

        # DONE: Membership Logic (Make membership class, put token profile as class attribute)
        mem_tokens = 0  # go through the memberships and figure out how many tokens are available to the user this week

        for membership in user.memberships:
            mem = fetch_mem(membership)
            mem_tokens += mem.profile.get(self.sport)

        mem_tokens += int(not user.freePassUsed)
        # mem_tokens no represents the number of available tokens.
        # INFO: now we need to get the number of used tokens.
        used_tokens = len(user.tokenProfile.get(self.sport))

        capable = True  # Temporary boolean for whether tokens are available.
        if used_tokens >= mem_tokens:
            # They no longer have enough tokens for this sport, make them pay / enroll
            capable = False
        # capable has been taken care of.

        if len(self.enrolled) < self.capacity and capable:  # space available and token available.
            self.enrolled.append(user_id)
            # TODO: Update Event DB instance with enrollment.
            # TODO: Put this enrollment (event_id) in the associated sport in the User and update the database.
            new_scheduled = user.scheduled  # Get the currently scheduled events
            new_scheduled.append(self.event_id)  # Append this new event
            edit_user(user.user_id, "scheduled", new_scheduled)  # update the DB User with scheduled.

            # TODO: Add Date to enrolled list for user.
            # TODO: Subtract token from sport (add it to used_tokens then update DB)
        elif len(self.enrolled) < self.capacity:  # space available but token unavailable.
            self.pending.append(user_id)
            # TODO: Figure out payment API and other necessary processes to ensure full transparency.
            # TODO: THIS IS A BIG ONE.
        elif capable:  # token available but no space available
            self.waitlist.append(user_id)
            # TODO: Tell the user that they have a waitlist item scheduled. When the event passes, waitlist scheduled doesnt go to history.
        else:
            # TODO: figure out what to do here. do we want them to pay before they go on the waitlist?
            pass
        pass


class User:
    def __init__(self, user_id, first, last, email, birth, gender, freePassUsed=False, tokenProfile: dict=None, history=None,
                 scheduled=None, memberships=None, settings=None):
        self.user_id = user_id
        self.first = first
        self.last = last
        self.email = email
        self.birth = birth
        self.gender = gender
        self.freePassUsed: bool = bool(freePassUsed)
        self.tokenProfile: dict[str, list] = tokenProfile or {}
        # Token profile will be of structure {'sport': [date_used_1, date_used_2,...]}
        self.history = history or []
        self.scheduled = scheduled or []
        self.memberships: list = memberships or []
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
        # Done: Figure out the potential keys.

        mandatory_keys = ['user_id', 'first_name', 'last_name', 'email', 'birthdate', 'gender']
        all_keys = ['user_id', 'first_name', 'last_name', 'email', 'birthdate', 'gender', 'free_pass_used',
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

    def to_dict(self) -> list[Union[str, dict]]:
        """
        A function to create a universal dict from self.
        :param self: self
        :return: list wth the userId then the rest of the info in a dict
        """
        return [self.user_id, {
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
            "settings": self.settings}]

    def get_mem(self, membership: str):
        """
        Get this user a membership
        :param membership: name of memberhship
        :return: Logging info
        """
        # TODO: BIG TODO Figure out payment stuff
        self.memberships.append(membership)
        edit_user(self.user_id, 'memberships', self.memberships)

    def __str__(self):
        thing = ""
        for key, value in self.to_dict()[1].items():
            thing = thing + (f'\n{key}: {value}')
        return thing


def hash_name(first: str, last: str) -> str:
    """
    returns a hash of the full name to return a unique userId
    :param first: first name
    :param last: last name
    :return: hash
    """

    # return first three letters of each name followed by length of each name. ***for now***
    # e.g has_name(Abdelrahman, Alkhawas) -> Abd11Alk8
    temp = str(hash(f'{first} {last}'))[-3:]
    # TODO: figure out hash function.
    return f'{first[:3]}{len(first)}{last[:3]}{len(last)}'


def hash_event_instance(sport: str, gender: str, event_datetime: datetime) -> str:
    """
    A function to hash a particular instance of an event.
    :param sport: self
    :param gender: self
    :param event_datetime: datetime of this particular instance.
    :return: unique hashed string
    """
    assert gender.lower() in ['male', 'female']
    return f'{gender[0]}{str(hash(event_datetime))[-3:]}{sport[:3]}'


def valid_email(email: str) -> bool:
    """
    returns bool representing whether an email is valid or not
    :param email: to be verified
    :return: validity
    """
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return bool(re.fullmatch(regex, email))


def create_singular_event(event_name: str, gender: str, sport: str, start_datetime: str, duration: int, capacity: int,
                          tags: Optional[list]):
    """
    A function that creates a new event then adds it to the DB
    :param event_name: Name to be displayed on front-end
    :param gender: self
    :param sport: self
    :param start_time: datetime string of this particular instance YYYY-MM-DD-HH-MM.
    :param duration: in minutes
    :param tags: for searching
    :return: SingularEvent object
    """

    event_datetime = datetime.datetime(*[int(num) for num in start_datetime.split('-')])
    event_id = hash_event_instance(sport, gender, event_datetime)

    events = db.collection("Events").stream()
    for event in events:
        if event.id == event_id:
            # TODO: Event exists, Raise some kind of safe error
            return None

    if sport not in tags: tags.append(sport)
    if gender not in tags: tags.append(gender)
    if 'non-recurring' not in tags: tags.append('non-recurring')

    new_event = SingularEvent(event_id, event_name, gender, sport, start_datetime, duration, capacity, None,
                              tags, None, None)
    new_event_info = new_event.to_dict()

    db.collection("Events").document(new_event_info[0]).set(new_event_info[1])
    return new_event


def create_profile(first_name: str, last_name: str, email: str, birth: str, gender: str,
                   member: Optional[bool]) -> Optional[User]:
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
        if user.id == user_id:  # Turns out we actually want to compare their emails. overlapping names.
            # TODO: Person exists, Raise some kind of safe error
            return False
        print(f'{user.id} => {user.to_dict()}')

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
    return new_user


def fetch_user(user_id: str) -> Union[User, bool]:
    """
    Fetch a file from the DB with a given user_id
    :param user_id: duh
    :return: either a User object, or False
    """
    # DONE: fully complete.
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


def fetch_event(event_id: str) -> Optional[SingularEvent]:
    """
    Fetch a file from the DB with a given event_id
    :param event_id: duh
    :return: either an Event object, or None
    """
    # DONE: fully complete.
    doc_ref = db.collection("Events").document(event_id)
    doc = doc_ref.get()
    if doc.exists:
        print(doc.to_dict())
        fetched = doc.to_dict()
        fetched['event_id'] = event_id
        event = SingularEvent.from_dict(fetched)
        return event
    else:
        print('DNE')
        return None


def fetch_mem(membership: str) -> Optional[Membership]:
    """
    Fetch the details of a membership from DB
    :param membership: membership id/name
    :return: Membership Object.
    """
    # DONE: fully complete
    doc_ref = db.collection("Memberships").document(membership)
    doc = doc_ref.get()
    if doc.exists:
        print(doc.to_dict())
        fetched = doc.to_dict()
        fetched['name'] = membership
        mem = Membership.from_dict(fetched)
        return mem
    else:
        print('DNE')
        return None


def delete_user(user_id: str) -> datetime:
    """
    delete an entire user based on user_id
    :param user_id:  duh
    :return: timestamp of deletion if successful.
    """
    if db.collection("Users").document(user_id).get().exists:
        # TODO: figure out history management. Logging document somewhere
        return db.collection("Users").document(user_id).delete()


def delete_event(event_id) -> datetime:
    """
    delete an event from DB
    :param event_id:
    :return:
    """
    if db.collection("Events").document(event_id).get().exists:
        # TODO: figure out history management. Logging document somewhere
        return db.collection("Events").document(event_id).delete()


def edit_user(user_id: str, field: str, new_value) -> datetime:
    """
    Edit at user object from database
    :param user_id: user to edit
    :param field: field of user to be edited. yet to be authenticated.
    :param new_value: value to be updated.
    :return: potentially return datetime for logging purposes.
    """
    all_keys = ['email', 'free_pass_used', 'token_profile', 'history', 'scheduled', 'memberships', 'settings']

    assert field in all_keys
    user = fetch_user(user_id)
    doc_ref = db.collection("Users").document(user_id)  # fetch user from DB
    doc_ref.update({field: new_value})  # update direct within DB
    # TODO: figure out history management. Logging document somewhere


def edit_event(event_id: str, field: str, new_value) -> datetime:
    # TODO: Actually Do it
    pass


create_profile('Abdelrahman', 'Alkhawas', 'abderlahman_khawas@hotmail.com', '04-10-2001', 'Male', False)
create_profile('Ahmed', 'Abdelaziz', 'ahmed.ym.tawfik@gmail.com', '19-07-2002', 'Male', False)
create_profile('Omar', 'Zeid', 'omar.kmaz@gmail.com', '21-09-2000', 'Male', False)
temp_event = SingularEvent('f2r34q', 'mens football', 'Male', 'football', datetime.datetime(2024, 4, 5, 21, 0, 0), 55, 21)
