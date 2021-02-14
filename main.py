import uvicorn
import psycopg2
from fastapi import FastAPI, Response, status, HTTPException
from typing import Optional
import psycopg2.extras
from psycopg2 import extras
from pydantic import BaseModel
import json
from datetime import date, datetime
import os
import datetime

app = FastAPI()

# DB_HOST = '127.0.0.1'
# DB_PORT = 5432
# DB_NAME = 'postgres'
# DB_USER = 'postgres'
# DB_PASS = 'Mm123456'
# DB_SCHEMA = 'public'
#
# ps_connection = psycopg2.connect(host=DB_HOST, port=DB_PORT, database=DB_NAME,
#                                  user=DB_USER, password=DB_PASS)
# ps_cursor = ps_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
ps_connection = psycopg2.connect(user="postgres",
                                 password="Mm123456",
                                 host="127.0.0.1",
                                 port="5432",
                                 database="postgres")
ps_cursor = ps_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ps_connection=None

class Coupon(BaseModel):
    coupon_code: str
    description: Optional[str] = None
    expire_date: datetime.datetime
    user_id: int
    product_id: int
    count_of_use: int
    discount_type: int
    discount_percent: Optional[int] = None
    discount_ceil: Optional[int] = None
    discount_amount: Optional[int] = None


class CouponOut(BaseModel):
    id: int
    user_id: int
    coupon_code: str
    created_at: datetime.datetime
    rule: str
    results: str
    description: Optional[str] = None


class Invoice(BaseModel):
    user_id: int
    coupon_code: str
    amount: int
    coupon_discount: int


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/coupons/{coupon_code}")
def get_coupon(coupon_code: Optional[str] = None, coupon_id: Optional[int] = None):
    coupons = show_Coupons(coupon_code, coupon_id)
    out = []
    try:
        if coupons:
            for item in coupons:
                lst = {}
                lst["id"] = item[0]
                lst["user_id"] = item[1]
                lst["coupon_code"] = item[2]
                lst["created_at"] = item[3]
                lst["rule"] = item[4]
                lst["results"] = item[5]
                lst["description"] = item[6]
                return lst
    except (Exception, psycopg2.Error) as error:
        print(error)
    return out


@app.post("/coupon/", status_code=201)
async def create_coupon(coupon: Coupon, response: Response):
    coupon_ = get_Coupon(coupon.coupon_code)
    if len(coupon_) != 0:
        raise HTTPException(status_code=409, detail="Coupon_code already exists!")

    ps_connection = get_connection()
    cur = ps_connection.cursor()
    try:
        # results = {}
        # results[''] = []
        # results['results'].append({
        #     'discount_type': coupon.discount_type,
        #     'discount_percent': coupon.discount_percent,
        #     'discount_ceil': coupon.discount_ceil,
        #     'discount_amount': coupon.discount_amount
        # })

        results = '''
        {
            "results": {
                "discount_type": ''' + str(coupon.discount_type) + ''',
                "discount_percent": ''' + str(coupon.discount_percent) + ''',
                "discount_ceil": ''' + str(coupon.discount_ceil) + ''',
                "discount_amount": ''' + str(coupon.discount_amount) + '''
            }
        }
        '''

        # rule = {}
        # rule[''] = []
        # rule['rule'].append({
        #     'user_id': coupon.user_id,
        #     'product_id': coupon.product_id,
        #     'expire_date': coupon.expire_date,
        #     'count_of_use': coupon.count_of_use
        # })

        rule = '''
                {
                    "rule": {
                        "user_id": ''' + str(coupon.user_id) + ''',
                        "product_id": ''' + str(coupon.product_id) + ''',
                        "expire_date": "''' + str(coupon.expire_date) + '''",
                        "count_of_use": ''' + str(coupon.count_of_use) + '''
                    }
                }
                '''
        create_date = date.today()
        segment = """ INSERT INTO coupons (coupon_code , created_at ,results , rule ,description , user_id ) values  
        (%s,%s,%s,%s,%s,%s) RETURNING id"""
        record_to_insert = (coupon.coupon_code, str(create_date), results, rule, coupon.description,
                            int(coupon.user_id))

        cur.execute(segment, record_to_insert)

        ps_connection.commit()
        count = cur.rowcount
        coupon_id = cur.fetchone()[0]
        print(count, "Record inserted successfully into coupons table")

        # data = {}
        # data[''] = []
        # data['data'].append({
        #     'id': coupon_id,
        #     'coupon_code': coupon.coupon_code,
        #     'created_at': create_date,
        #     'results': results['results'],
        #     'rule': rule['rule'],
        #     'description': coupon.description,
        #     'user_id': coupon.user_id
        # })
        data = '''
            {
                "id": ''' + str(coupon_id) + ''',
                "coupon_code": ''' + str(coupon.coupon_code) + ''',
                "created_at": "''' + str(create_date) + '''",
                "results": [''' + str(results) + '''],
                "rule": [''' + str(rule) + '''],
                "description": "''' + str(coupon.description) + '''",
                "user_id": ''' + str(coupon.user_id) + '''
            }
        '''
        response.status_code = status.HTTP_201_CREATED
    except (Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=500, detail="Internal server error!")
        # response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        # if ps_connection:
        #     print("Failed to insert record into coupons table", error)

    return data


@app.post("/invoice/", status_code=201)
async def use_coupon(invoice: Invoice, response: Response):
    coupon_ = get_UserOfCoupon(invoice.coupon_code, invoice.user_id)
    try:
        if coupon_:
            # print(date.today())
            # print(coupon_[3])
            # d = coupon_[3]
            # datetime_obj = datetime.datetime.strptime(d[:-13], '%y-%m-%d %H:%M:%S')
            # print(datetime_obj)
            # if date.today() > date(coupon_[3]):
            #     raise HTTPException(status_code=403, detail="Coupon is expired!")

            out = track_of_coupon(invoice.coupon_code)
            if len(out) == coupon_[2]:
                raise HTTPException(status_code=403, detail="Coupon has already been used!")

            ps_connection = get_connection()
            cur = ps_connection.cursor()
            try:
                create_date = date.today()
                segment = """ INSERT INTO invoices (user_id ,coupon_code , amount, coupon_discount, create_at, paid_at) values  
                    (%s,%s,%s,%s,%s,%s) RETURNING id"""
                record_to_insert = (
                invoice.user_id, invoice.coupon_code, invoice.amount, invoice.coupon_discount, create_date, create_date)

                cur.execute(segment, record_to_insert)

                ps_connection.commit()
                count = cur.rowcount
                coupon_id = cur.fetchone()[0]
                print(count, "Record inserted successfully into invoices table")

                response.status_code = status.HTTP_201_CREATED
            except (Exception, psycopg2.Error) as error:
                raise HTTPException(status_code=500, detail="Internal server error!")

        else:
            raise HTTPException(status_code=403, detail="Coupon not exists or is not authorized!")
    except (Exception, psycopg2.Error) as error:
        print(error)


def get_connection():
    if not ps_connection or ps_connection.closed:
        connection = psycopg2.connect(user="postgres",
                                      password="Mm123456",
                                      host="127.0.0.1",
                                      port="5432",
                                      database="postgres")
        # cursor = connection.cursor()
    else:
        connection = ps_connection
    return connection


def get_Coupon(coupon_code_):
    try:
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
    except(Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=500, detail="Internal server error!")


def get_UserOfCoupon(coupon_code_, user_id):
    try:
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
    except(Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=500, detail="Internal server error!")


def show_Coupons(coupon_code_=None, coupon_id_=None):
    try:
        connect = get_connection()
        cur = connect.cursor()
        qry = 'select * from coupons where 1=1'
        qry_c = None
        if coupon_code_ is not None:
            qry += ' and coupon_code = %s'
            qry_c = [coupon_code_]
        elif coupon_id_ is not None:
            qry += ' and coupon_id_ = %s'
            qry_c = [coupon_id_]
        else:
            raise HTTPException(status_code=400, detail="One parameter must be involved!")

        cur.execute(
            qry, qry_c)
        res = []
        out = []
        if cur.rowcount != 0:
            res = cur.fetchall()
            if res:
                count = 0
                for i in res:
                    counter = 0
                    lst = []
                    for j in i:
                        lst.append(j)
                        counter += 1
                    out.append(lst)
                    count += 1

        return out
    except(Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=500, detail="Internal server error!")


def track_of_coupon(coupon_code_):
    try:
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
    except(Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=500, detail="Internal server error!")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)
