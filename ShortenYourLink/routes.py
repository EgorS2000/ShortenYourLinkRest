from re import match

from ShortenYourLink import db, app
from ShortenYourLink.models import Link, link_schema, User, Transitions, app_dmn

from flask import jsonify, request
import secrets
import string
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, get_jwt_identity


@app.route('/', methods=['POST'])
@jwt_required
def main_page():
    orig_link = request.json['link']

    domain_name = orig_link[int(str(orig_link).find('/')) + 2:]

    domain_name = domain_name[:int(str(domain_name).find('/'))].replace('www.', '')

    random_sequence = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))

    link_owner = get_jwt_identity()

    link_struct = Link(orig_link=orig_link, domain_name=domain_name, random_sequence=random_sequence,
                       link_owner=link_owner)

    if Link.query.filter_by(orig_link=orig_link, link_owner=link_owner).first():
        exist_rand_seq = Link.query.filter_by(orig_link=orig_link).first().random_sequence
        link_struct = Link(orig_link=orig_link, domain_name=domain_name, random_sequence=exist_rand_seq,
                           link_owner=link_owner)

    else:
        try:
            db.session.add(link_struct)
            db.session.commit()

        except:
            return 'Error with creating new link'

    return link_schema.jsonify(link_struct)


@app.route('/check', methods=['POST'])
@jwt_required
def check_link_page():
    orig_link = request.json['short_link']

    short_link_rand_sequence = str(orig_link).replace(f'{app_dmn}', '')

    if Link.query.filter_by(random_sequence=short_link_rand_sequence).first():
        real_link = Link.query.filter_by(random_sequence=short_link_rand_sequence).first().orig_link

        return jsonify(real_link)

    else:
        return 'Short link does not exist'


@app.route('/change_link', methods=['POST'])
@jwt_required
def change_link_page():
    orig_link = request.json['short_link']

    new_idx = request.json['new_idx']

    short_link_rand_sequence = str(orig_link).replace(f'{app_dmn}', '')

    if Link.query.filter_by(random_sequence=short_link_rand_sequence).first() and \
            not Link.query.filter_by(random_sequence=new_idx).first():

        if int(get_jwt_identity()) == Link.query.filter_by(
                random_sequence=short_link_rand_sequence).first().link_owner:

            short_link = Link.query.filter_by(random_sequence=short_link_rand_sequence).first()

            short_link.random_sequence = new_idx

            try:
                db.session.commit()
                return jsonify(f'{app_dmn}{short_link.random_sequence}')

            except:
                return "An error occurred while changing the link"

        else:
            return "You are not owner of this link"

    else:
        return "Original link doesn't exist or new link already exists"


@app.route('/my_links', methods=['GET'])
@jwt_required
def my_links():
    links = Link.query.order_by(Link.creation_date).filter_by(link_owner=get_jwt_identity()).all()
    links_list = []
    for link in links:
        links_list.append({"id": link.id, "original link": link.orig_link, "domain name": link.domain_name,
                           "random sequence": link.random_sequence, "link owner": link.link_owner,
                           "creation date": link.creation_date, "link tag": link.link_tag})
    return jsonify(links_list)


@app.route('/deactivate_link', methods=['POST'])
@jwt_required
def deactivate_link():
    short_link = request.json['short_link']

    user_password = request.json['user_password']

    short_link_rand_sequence = str(short_link).replace(f'{app_dmn}', '')

    if Link.query.filter_by(random_sequence=short_link_rand_sequence).first():

        if check_password_hash(User.query.filter_by(id=get_jwt_identity()).first().password, user_password):

            if int(get_jwt_identity()) == Link.query.filter_by(
                    random_sequence=short_link_rand_sequence).first().link_owner:

                try:
                    db.session.delete(Link.query.filter_by(random_sequence=short_link_rand_sequence).first())
                    db.session.commit()

                except:
                    return "An error occurred while deleting of the link"

            else:
                return "You are not owner of this link"

        else:
            return "Password does not correct"

    else:
        return "Short link does not exist"

    return {"Deleted short link": short_link}


@app.route('/my_account', methods=['GET'])
@jwt_required
def my_account():
    status = User.query.filter_by(id=get_jwt_identity()).first().account_status

    trans_all_time = Transitions.query.filter_by(owner_id=get_jwt_identity()).count()

    trans_last_day = 0

    for trans in Transitions.query.filter_by(owner_id=get_jwt_identity()).all():
        if (datetime.now() - trans.trans_time).seconds < 86400:
            trans_last_day += 1

    trans_last_week = 0

    for trans in Transitions.query.filter_by(owner_id=get_jwt_identity()).all():
        if (datetime.now() - trans.trans_time).seconds < 604800:
            trans_last_week += 1

    trans_last_30_days = 0

    for trans in Transitions.query.filter_by(owner_id=get_jwt_identity()).all():
        if (datetime.now() - trans.trans_time).seconds < 2592000:
            trans_last_30_days += 1

    trans_last_year = 0

    for trans in Transitions.query.filter_by(owner_id=get_jwt_identity()).all():
        if (datetime.now() - trans.trans_time).seconds < 3.15 * 10 ** 7:
            trans_last_year += 1

    domains = []

    for domain in Link.query.filter_by(link_owner=get_jwt_identity()).all():
        domains.append(domain.domain_name)

    domains_count = []

    for domain in domains:
        domains_count.append(Link.query.filter_by(domain_name=domain).count())

    result_domain_list = []

    for i in range(len(domains)):
        result_domain_list.append([domains[i], domains_count[i]])

    result_domain_dict = dict(result_domain_list)

    return {"Account status": status,
            "Trasitions during all time": trans_all_time,
            "Trasitions during last day": trans_last_day,
            "Trasitions during last week": trans_last_week,
            "Trasitions during 30 days": trans_last_30_days,
            "Trasitions during last year": trans_last_year,
            "All domains": result_domain_dict}


@app.route('/my_links/<string:random_sequence>/more', methods=['GET'])
@jwt_required
def my_link_delete(random_sequence):

    if int(get_jwt_identity()) == Link.query.filter_by(random_sequence=random_sequence).first().link_owner:

        link = Link.query.filter_by(random_sequence=random_sequence).first()
        owner = User.query.filter_by(id=link.link_owner).first().login

        link_trans_all_time = Transitions.query.filter_by(link_id=link.id).count()

        link_trans_last_day = 0

        for trans in Transitions.query.filter_by(link_id=link.id).all():
            if (datetime.now() - trans.trans_time).seconds < 86400:
                link_trans_last_day += 1

        link_trans_last_week = 0

        for trans in Transitions.query.filter_by(link_id=link.id).all():
            if (datetime.now() - trans.trans_time).seconds < 604800:
                link_trans_last_week += 1

        link_trans_last_30_days = 0

        for trans in Transitions.query.filter_by(link_id=link.id).all():
            if (datetime.now() - trans.trans_time).seconds < 2592000:
                link_trans_last_30_days += 1

        link_trans_last_year = 0

        for trans in Transitions.query.filter_by(link_id=link.id).all():
            if (datetime.now() - trans.trans_time).seconds < 3.15 * 10**7:
                link_trans_last_year += 1

        return {"Link": link.orig_link,
                "Sequence": link.random_sequence,
                "Owner": owner,
                "Trasitions during all time": link_trans_all_time,
                "Trasitions during last day": link_trans_last_day,
                "Trasitions during last week": link_trans_last_week,
                "Trasitions during last 30 days": link_trans_last_30_days,
                "Trasitions during last year": link_trans_last_year}

    else:
        return "You are not owner of this link"


@app.route('/my_links/<string:random_sequence>/more/add_hashtag', methods=['POST'])
@jwt_required
def add_hashtag(random_sequence):
    if int(get_jwt_identity()) == Link.query.filter_by(random_sequence=random_sequence).first().link_owner:

        link = Link.query.filter_by(random_sequence=random_sequence).first()

        link.link_tag = request.json['link_tag']

        try:
            db.session.commit()

            return {"Link": link.orig_link, "Random sequence": link.random_sequence, "Hashtag": link.link_tag}

        except:
            return "An error occurred while adding hashtag"

    else:
        return "You are not owner of this link"


@app.route('/register', methods=['POST'])
def user_registration():
    login = request.json['login']
    password = request.json['password']
    registration_date = datetime.now()

    if not (login or password):
        return 'Please, fill all fields'

    elif not match(r'[0-9a-zA-Z!@#$%^&*]{8,}', str(password)):
        return 'Your password must consist 8 and more latin letters and numbers'

    elif not match(r'^[a-zа-яA-ZА-Я-ёЁ_.][a-zа-яA-ZА-ЯёЁ0-9-_.]{1,20}$', login):
        return 'Your login must consist from 2 to 20 latin letters and numbers'

    else:
        hash_password = generate_password_hash(password)
        new_user = User(login=login, password=hash_password, registration_date=registration_date)

        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            return 'Login is already taken'

        token = new_user.get_token()

        return {'access_token': token}


@app.route('/login', methods=['POST'])
def user_login():
    login = request.json['login']
    password = request.json['password']

    if login and password:
        user = User.query.filter_by(login=login).first()

        if user and check_password_hash(user.password, password):

            user.last_login_date = datetime.now()

            try:
                db.session.commit()

            except:
                return "An error occurred while login"

            user.authenticate(login=login, password=password)
            token = user.get_token()

            return {'access_token': token}
        else:
            return 'Login or password is not correct'


@app.route('/delete_account', methods=['POST'])
@jwt_required
def user_delete_account():
    user_password = request.json['password']

    if not check_password_hash(User.query.filter_by(id=get_jwt_identity()).first().password, user_password):
        return 'Password is not correct'

    else:
        user = User.query.filter_by(id=get_jwt_identity()).first()
        links = Link.query.filter_by(link_owner=int(get_jwt_identity()))

        user_name = User.query.filter_by(id=get_jwt_identity()).first().login

        try:
            db.session.delete(user)

            for link in links:
                db.session.delete(link)

            db.session.commit()

        except:
            return 'An error occurred while deleting account or deleting your links'

    return {"Deleted account": user_name}


@app.route('/change_password', methods=['POST'])
@jwt_required
def user_change_password():

    old_password = request.json['old_password']
    new_password = request.json['new_password']

    if not (old_password or new_password):
        return 'Please, fill all fields'

    elif not check_password_hash(User.query.filter_by(id=get_jwt_identity()).first().password, old_password):
        return 'Your old password is not correct'

    elif not match(r'[0-9a-zA-Z!@#$%^&*]{8,}', str(new_password)):
        return 'Your password must consist 8 and more latin letters and numbers'

    else:
        User.query.filter_by(id=get_jwt_identity()).first().password = generate_password_hash(new_password)

        try:
            db.session.commit()
        except:
            return 'An error occurred while changing your password'

    return {"New password": new_password}
