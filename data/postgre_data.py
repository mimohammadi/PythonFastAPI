import psycopg2
from fastapi import HTTPException
import json

from app.model import UserSchema, UserInDB, User
from data.connection.postgres.postgres_connection import get_connection


def get_coupon(coupon_code_):
    # try:
    connect = get_connection()
    cur = connect.cursor()

    cur.execute(
            'select id from coupons where coupon_code = %s', [coupon_code_])
    res = []
    if cur.rowcount != 0:
        res = cur.fetchall()
        if res:
            return [i[0] for i in res]
    return res
    # except(Exception, psycopg2.Error) as error:
    #     # raise HTTPException(status_code=500, detail="Internal server error!")
    #     return res


def get_user_of_coupon(coupon_code_, user_id):
    #try:
    connect = get_connection()
    cur = connect.cursor()
    qry = '''select id,user_id, rule->'rule'->>'count_of_use' as count_of_use
        ,rule->'rule'->>'expire_date' as expire_date,results->'results'->>'discount_type'
        as discount_type,results->'results'->>'discount_ceil' as discount_ceil
        from coupons where coupon_code = %s and user_id = %s'''

    cur.execute(qry
                    , (coupon_code_, user_id))
    res = []
    lst = []
    if cur.rowcount != 0:
        res = cur.fetchall()
        if res:
            for i in res:
                counter = 0
                lst = []
                for j in i:
                    lst.append(j)
                    counter += 1
    return lst
    #except(Exception, psycopg2.Error) as error:
        # raise HTTPException(status_code=500, detail="Internal server error!")
        #return lst


def show_coupons(coupon_code_=None):
    #try:
        connect = get_connection()
        cur = connect.cursor()
        qry = 'select * from coupons where 1=1'
        qry_c = None
        # if coupon_code_ is not None:
        qry += ' and coupon_code = %s'
        qry_c = [coupon_code_]
        # elif coupon_id_ is not None:
        #     qry += ' and coupon_id_ = %s'
        #     qry_c = [coupon_id_]
        # else:
        #     # return "One parameter must be involved!"
        #     raise HTTPException(status_code=400, detail="One parameter must be involved!")

        cur.execute(
            qry, qry_c)
        res = []
        # out = []
        lst = []
        if cur.rowcount != 0:
            res = cur.fetchall()
            if res:
                # count = 0
                # for i in res:
                #   counter = 0

                for j in res[0]:
                    lst.append(j)
                    # counter += 1
                    # out.append(lst)
                    # count += 1
        return lst
        # return out
    # except(Exception, psycopg2.Error) as error:
    #     raise HTTPException(status_code=500, detail="Internal server error!")


def track_of_coupon(coupon_code_):
    # try:
        connect = get_connection()
        cur = connect.cursor()

        cur.execute(
            'select id from invoices where coupon_code = %s', [coupon_code_])
        res = []
        if cur.rowcount != 0:
            res = cur.fetchall()
            if res:
                return [i[0] for i in res]
        return res
    # except(Exception, psycopg2.Error) as error:
    #     raise HTTPException(status_code=500, detail="Internal server error!")


def check_user(data: UserSchema):
    # try:
        connect = get_connection()
        cur = connect.cursor()
        d = json.loads(data.json())
        cur.execute(
            'select * from users where username = %s', [d['username']])

        res = []
        if cur.rowcount != 0:
            res = cur.fetchall()
            if res:

                for i in res:
                    counter = 0
                    lst = []
                    for j in i:
                        lst.append(j)
                        counter += 1
            return lst
    # except(Exception, psycopg2.Error) as error:
    #     raise HTTPException(status_code=500, detail="Internal server error!")


def get_user(user_id: int):
    # try:
        connect = get_connection()
        cur = connect.cursor()
        cur.execute(
            'select * from users where id = %s', [user_id])

        res = []
        if cur.rowcount != 0:
            res = cur.fetchall()
            if res:
                data = User(
                    username=res[0][3],
                    name=res[0][1],
                    lname=res[0][2],
                    created_at=res[0][4]
                )

        return data
    # except(Exception, psycopg2.Error) as error:
    #     raise HTTPException(status_code=500, detail="Internal server error!")
    #


def get_user_permission(username: str):
    # try:
        connect = get_connection()
        cur = connect.cursor()
        cur.execute(
            '''with a as
                (
                    with a as
                        (select id from users where username = %s)
                        select permission_id from user_permissions up where exists (select id from a where 
                        a.id = up.user_id)
                )
                select role from permissions p where exists(select * from a where a.permission_id = p.id)''',
            [username])

        res = []
        if cur.rowcount != 0:
            res = cur.fetchall()
            if res:
                return [i[0] for i in res]

    # except(Exception, psycopg2.Error) as error:
    #     raise HTTPException(status_code=500, detail="Internal server error!")
        return res
