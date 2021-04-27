#from datetime import datetime
import datetime
from time import sleep
import json

import psycopg2
import pytz
from celery import Celery
from celery.utils.log import get_task_logger  # Initialize celery
from fastapi import HTTPException

from app.model import Invoice, InvoiceOut
from data.connection.postgres.postgres_connection import get_connection
from data.postgre_data import get_user_of_coupon, track_of_coupon

celery = Celery('tasks', broker='redis://127.0.0.1:6379')
# Create logger - enable to display messages on task logger
celery_log = get_task_logger(__name__)


# Create Order - Run Asynchronously with celery
# Example process of long running task
@celery.task
def create_order(name, quantity):
    # 5 seconds per 1 order
    complete_time_per_item = 5

    # Keep increasing depending on item quantity being ordered
    sleep(complete_time_per_item * quantity)  # Display log
    celery_log.info(f"Order Complete!")
    return {"message": f"Hi {name}, Your order has completed!",
            "order_quantity": quantity}


@celery.task
def create_invoice(invoice, quantity):
    sleep(quantity)
    d = json.loads(invoice)
    print(d)
    print(d['coupon_code'])
    celery_log.info(f"Order Complete!1")
    coupon_ = get_user_of_coupon(d['coupon_code'], d['user_id'])
    celery_log.info(f"Order Complete!2")
    try:
        if coupon_:
            # print(date.today())
            # print(coupon_[3])
            # d = coupon_[3]
            # datetime_obj = datetime.datetime.strptime(d[:-13], '%y-%m-%d %H:%M:%S')
            # print(datetime_obj)
            # if date.today() > date(coupon_[3]):
            #     raise HTTPException(status_code=403, detail="Coupon is expired!")
            print(coupon_)
            celery_log.info(f"Order Complete!3")
            out = track_of_coupon(d['coupon_code'])
            celery_log.info(f"Order Complete!4")
            print(out)
            if len(out) >= int(coupon_[2]):
                # raise HTTPException(status_code=403, detail="Coupon has already been used!")
                return "Coupon has already been used!"

            ps_connection = get_connection()
            cur = ps_connection.cursor()
            try:
                celery_log.info(f"Order Complete!5")
                create_date = datetime.datetime.now(pytz.timezone('Asia/Tehran')).strftime("%Y-%m-%d %H:%M:%S")
                # date.today()
                segment = """ INSERT INTO invoices (user_id ,coupon_code , amount, coupon_discount, create_at, paid_at) 
                    values (%s,%s,%s,%s,%s,%s) RETURNING id"""
                record_to_insert = (
                    int(d['user_id']), d['coupon_code'], int(d['amount']), d['coupon_discount'], str(create_date),
                    str(create_date))

                cur.execute(segment, record_to_insert)

                ps_connection.commit()
                count = cur.rowcount
                invoice_id = cur.fetchone()[0]
                print(count, "Record inserted successfully into invoices table")

                data = InvoiceOut(
                    id=invoice_id,
                    user_id=d['user_id'],
                    coupon_code=d['coupon_code'],
                    amount=d['amount'],
                    coupon_discount=d['coupon_discount'],
                    create_at=create_date,
                    paid_at=create_date
                )
                print(data.json())

                return data
            except (Exception, psycopg2.Error) as error:
                print(error)
                raise HTTPException(status_code=500, detail="Internal server error!...")

        else:
            # raise HTTPException(status_code=403, detail="Coupon not exists or is not authorized!")
            return "Coupon not exists or is not authorized!"
    except (Exception, psycopg2.Error) as error:
        print(error)
        return error
