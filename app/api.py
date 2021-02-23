import psycopg2
from fastapi import Depends, FastAPI, Response, status, HTTPException
from typing import Optional
import psycopg2.extras
# from fastapi.security import OAuth2PasswordBearer
import json
from datetime import datetime
import datetime
import logging
from datetime import timedelta
import pytz
# from passlib.context import CryptContext
from fastapi.params import Body
from app.auth.auth_bearer import JWTBearer
from app.auth.auth_handler import sign_jwt, verify_password, get_password_hash
from data.connection.redis.redis_connection import redis_connect
from data.connection.postgres.postgres_connection import get_connection
from app.model import Coupon, CouponOut, Invoice, InvoiceOut, UserLoginSchema, UserSchema

# to get a string like this run:
# openssl rand -hex 32
from data.redis_data import get_routes_from_cache, set_routes_to_cache

logging.basicConfig()


app = FastAPI()


#
# ps_connection = psycopg2.connect(user="postgres",
#                                  password="Mm123456",
#                                  host="127.0.0.1",
#                                  port="5432",
#                                  database="postgres")
# ps_cursor = ps_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


client = redis_connect()

# ps_connection=None


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
    u = json.loads(user.json())
    # u["password"] = get_password_hash(u["password"])
    data = UserSchema(
        username=u["username"],
        password=u["password"]
    )
    user_ = check_user(data)
    if user_ is not None:
        if not verify_password(u["password"], user_[5]):
            return False
        return sign_jwt(user_[0])
    return {
        "error": "Wrong login details!"
    }


@app.get("/coupons/{coupon_code}")
def get_coupon(coupon_code: str, coupon_id: Optional[int] = None):
    try:

        coupon = get_routes_from_cache(key="coupon-code:" + coupon_code)
        # if coupon is None:
        #     #response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        #     print(coupon)
        #     return "Failed to get redis value"

        d = coupon.decode('utf8').replace("'", '"')
        c = json.loads(d)
        print(c)
        lst = {}
        lst["id"] = c["id"]
        lst["user_id"] = c["user_id"]
        lst["coupon_code"] = c["coupon_code"]
        lst["created_at"] = c["created_at"]
        lst["rule"] = c["rule"]
        lst["results"] = c["results"]
        lst["description"] = c["description"]
        return json.dumps(lst)
    except (Exception, psycopg2.Error) as error:
        print(error)
        raise HTTPException(status_code=500, detail="Internal server error!")

    # coupons = show_Coupons(coupon_code, coupon_id)
    #
    # try:
    #     if coupons:
    #         for item in coupons:
    #             lst = {}
    #             lst["id"] = item[0]
    #             lst["user_id"] = item[1]
    #             lst["coupon_code"] = item[2]
    #             lst["created_at"] = item[3]
    #             lst["rule"] = item[4]
    #             lst["results"] = item[5]
    #             lst["description"] = item[6]
    #             return lst
    # except (Exception, psycopg2.Error) as error:
    #     print(error)
    #     raise HTTPException(status_code=500, detail="Internal server error!")


@app.post("/coupon/", status_code=201, dependencies=[Depends(JWTBearer())])
async def create_coupon(coupon: Coupon, response: Response):
    coupon_ = get_coupon(coupon.coupon_code)
    if len(coupon_) != 0:
        response.status_code = status.HTTP_409_CONFLICT
        return "Coupon_code already exists!"
        # raise HTTPException(status_code=409, detail="Coupon_code already exists!")

    ps_connection = get_connection()
    cur = ps_connection.cursor()
    try:

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
        create_date = datetime.datetime.now(pytz.timezone('Asia/Tehran')).strftime("%Y-%m-%d %H:%M:%S")
        # date.today()
        segment = """ INSERT INTO coupons (coupon_code , created_at ,results , rule ,description , user_id ) values  
        (%s,%s,%s,%s,%s,%s) RETURNING id"""
        record_to_insert = (coupon.coupon_code, str(create_date), results, rule, coupon.description,
                            int(coupon.user_id))

        cur.execute(segment, record_to_insert)

        ps_connection.commit()
        count = cur.rowcount
        coupon_id = cur.fetchone()[0]
        print(count, "Record inserted successfully into coupons table")
        print(datetime.datetime.now(pytz.timezone('Asia/Tehran')).strftime("%Y-%m-%d %H:%M:%S"))

        # data = '''
        #     {
        #         "id": ''' + str(coupon_id) + ''',
        #         "coupon_code": ''' + str(coupon.coupon_code) + ''',
        #         "created_at": "''' + str(create_date) + '''",
        #         "results": [''' + str(results) + '''],
        #         "rule": [''' + str(rule) + '''],
        #         "description": "''' + str(coupon.description) + '''",
        #         "user_id": ''' + str(coupon.user_id) + '''
        #     }
        # '''

        data = CouponOut(
            id=coupon_id,
            user_id=coupon.user_id,
            coupon_code=coupon.coupon_code,
            created_at=create_date,
            rule=rule,
            results=results,
            description=coupon.description
        )

        status_ = set_routes_to_cache(key="coupon-code:"+str(coupon.coupon_code), value=data.json())
        if not status_:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return "Failed to set redis key"


        print(get_routes_from_cache(key="coupon-code:"+str(coupon.coupon_code)))
        response.status_code = status.HTTP_201_CREATED
    except (Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=500, detail="Internal server error!")
        # response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        # if ps_connection:
        #     print("Failed to insert record into coupons table", error)

    return data


@app.post("/invoice/", status_code=201, dependencies=[Depends(JWTBearer())])
async def use_coupon(invoice: Invoice, response: Response):
    coupon_ = get_user_of_coupon(invoice.coupon_code, invoice.user_id)
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
            if len(out) >= int(coupon_[2]):
                # raise HTTPException(status_code=403, detail="Coupon has already been used!")
                response.status_code = status.HTTP_403_FORBIDDEN
                return "Coupon has already been used!"

            ps_connection = get_connection()
            cur = ps_connection.cursor()
            try:
                create_date = datetime.datetime.now(pytz.timezone('Asia/Tehran')).strftime("%Y-%m-%d %H:%M:%S")
                # date.today()
                segment = """ INSERT INTO invoices (user_id ,coupon_code , amount, coupon_discount, create_at, paid_at) 
                values (%s,%s,%s,%s,%s,%s) RETURNING id"""
                record_to_insert = (
                    invoice.user_id, invoice.coupon_code, invoice.amount, invoice.coupon_discount, create_date,
                    create_date)

                cur.execute(segment, record_to_insert)

                ps_connection.commit()
                count = cur.rowcount
                invoice_id = cur.fetchone()[0]
                print(count, "Record inserted successfully into invoices table")

                data = InvoiceOut(
                    id=invoice_id,
                    user_id=invoice.user_id,
                    coupon_code=invoice.coupon_code,
                    amount=invoice.amount,
                    coupon_discount=invoice.coupon_discount,
                    create_at=create_date,
                    paid_at=create_date
                )
                print(data.json())
                # print(json.dumps(data))
                status_ = set_routes_to_cache(key="invoice-id:" + str(invoice_id), value=data.json())
                if not status_:
                    response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    return "Failed to set redis key"

                # coupon = get_routes_from_cache(key="coupon-code:" + invoice.coupon_code)
                # d = coupon.decode('utf8').replace("'", '"')
                # c = json.loads(d)

                print(get_routes_from_cache(key="invoice_id:" + str(invoice_id)))
                response.status_code = status.HTTP_201_CREATED
                return data
            except (Exception, psycopg2.Error) as error:
                raise HTTPException(status_code=500, detail="Internal server error!")

        else:
            # raise HTTPException(status_code=403, detail="Coupon not exists or is not authorized!")
            response.status_code = status.HTTP_403_FORBIDDEN
            return "Coupon not exists or is not authorized!"
    except (Exception, psycopg2.Error) as error:
        print(error)


def get_coupon(coupon_code_):
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


def get_user_of_coupon(coupon_code_, user_id):
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


def show_coupons(coupon_code_=None, coupon_id_=None):
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
            # return "One parameter must be involved!"
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


def check_user(data: UserSchema):
    try:
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
    except(Exception, psycopg2.Error) as error:
        raise HTTPException(status_code=500, detail="Internal server error!")

