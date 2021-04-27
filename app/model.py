from pydantic import BaseModel, Field
from typing import Optional
import datetime
from functools import wraps


class UserLoginSchema(BaseModel):
    username: str = Field(...)
    password: str = Field(...)

    class Config:
        schema_extra = {
            "example": {
                "username": "username",
                "password": "weakpassword"
            }
        }


class UserSchema(BaseModel):
    username: str
    password: str

    class Config:
        schema_extra = {
            "example": {
                "username": "username",
                "password": "weakpassword"
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


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


class InvoiceOut(BaseModel):
    id: int
    user_id: int
    coupon_code: str
    amount: int
    coupon_discount: int
    create_at: datetime.datetime
    paid_at: datetime.datetime


class User(BaseModel):
    username: str
    name: Optional[str] = None
    lname: Optional[str] = None
    created_at: datetime.datetime


class UserInDB(User):
    hashed_password: str


class Order(BaseModel):
    customer_name: str
    order_quantity: int
    user_id: int




