import datetime
import time
from yoomoney import Quickpay, Client
from config import YOOMONEY_TOKEN, YOOMONEY_RECEIVER

client = Client(YOOMONEY_TOKEN)

def make_payment_url(price, label, target='Доступ к боту'):
    payment = Quickpay(
        receiver=YOOMONEY_RECEIVER,
        quickpay_form='shop',
        targets=target,
        paymentType='SB',
        sum=price,
        label=label
    )
    return payment.redirected_url

def check_payment(label):
    history = client.operation_history(label=label, from_date=datetime.datetime.now() - datetime.timedelta(hours=1))

    for operation in history.operations:
        if operation.label == label:
            return operation.status.lower() in ["success", "succeeded", "completed"]

    return False

