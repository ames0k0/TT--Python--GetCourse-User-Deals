"""
main.py --email [str] --limit [N]
"""

import os
import argparse
from typing import NoReturn

import requests
from prettytable import PrettyTable
from pydantic import TypeAdapter
from pydantic import EmailStr
from pydantic import ValidationError


account_name = os.environ.get("GET_COURSE__ACCOUNT_NAME")
secret_key = os.environ.get("GET_COURSE__SECRET_KEY")

if not account_name:
    print("Missing ENV Variable: `GET_COURSE__ACCOUNT_NAME`")
    exit(1)

if not secret_key:
    print("Missing ENV Variable: `GET_COURSE__SECRET_KEY`")
    exit(1)


def get_request_data(
    *,
    url: str, params: dict, request_group: str,
) -> dict | NoReturn:
    response = requests.get(url, params=params)
    data = response.json()

    if data["success"]:
        return data["info"]

    err_msg = f"Error: {request_group}"
    if not data["error"]:
        print(err_msg)
    else:
        print(err_msg + ": " + data["error_message"])

    exit(1)


def pretty_print_export_data(
    *,
    data: dict,
    result_limit: int,
) -> None:
    table = PrettyTable()
    fields = [
        "Пользователь",
        "Email",
        "ID пользователя",
        "ID заказа",
        "Дата создания",
        "Дата оплаты",
        "Статус",
        "Стоимость, RUB",
        "Состав заказа",
    ]
    row_data_index = []

    for field in fields:
        row_data_index.append(data["fields"].index(field))

    table.field_names = fields
    for data_item in data["items"][:result_limit]:
        table.add_row([data_item[idx] for idx in row_data_index])

    print(table)


def main(
    *,
    user_email: str, result_limit: int,
) -> None:
    # GET `ExportId`
    request_group="/api/account/users"
    data = get_request_data(
        url="https://{account_name}.getcourse.ru/pl/api/account/users".format(
            account_name=account_name,
        ),
        params={
            "email": user_email,
            "key": secret_key,
        },
        request_group=request_group,
    )

    export_id = data.get("export_id")
    if not export_id:
        print(f"Error: {request_group}")
        exit(1)

    # GET `UserId`
    request_group="/api/account/exports"
    data = get_request_data(
        url="https://{account_name}.getcourse.ru/pl/api/account/exports/{export_id}".format(
            account_name=account_name,
            export_id=export_id,
        ),
        params={
            "key": secret_key,
        },
        request_group=request_group,
    )

    user_id_index = data["fields"].index("id")
    email_index = data["fields"].index("Email")

    for data_item in data["items"]:
        if data_item[email_index] == user_email:
            user_id = data_item[user_id_index]
            break
    else:
        print(f"Error: {request_group}: No `id` for a User")
        exit(1)

    # GET `UserExportId`
    request_group="/api/account/deals"
    data = get_request_data(
        url="https://{account_name}.getcourse.ru/pl/api/account/deals".format(
            account_name=account_name,
        ),
        params={
            "key": secret_key,
            "user_id": user_id,
        },
        request_group=request_group,
    )

    if not data:
        print(f"Error: {request_group}: No `export_id` for a User")
        exit(1)

    user_export_id = data["export_id"]

    # Get `ExportData`
    request_group="/api/account/exports"
    data = get_request_data(
        url="https://{account_name}.getcourse.ru/pl/api/account/exports/{user_export_id}".format(
            user_export_id=user_export_id,
            account_name=account_name,
        ),
        params={
            "key": secret_key,
        },
        request_group=request_group,
    )

    pretty_print_export_data(
        data=data, result_limit=result_limit,
    )


if __name__ == "__main__":
    TA = TypeAdapter(EmailStr)

    parser = argparse.ArgumentParser(
        prog='GetCourse',
        description='Выгрузки данных из Геткурса для анализа',
        epilog='API_DOCS: https://getcourse.ru/help/api',
    )
    parser.add_argument(
        '-e', '--email',
        required=True,
        help='Адрес электронной почты пользователя',
    )
    parser.add_argument(
        '-l', '--limit',
        type=int, default=10,
        help='Ограничение отображаемых данных',
    )

    args = parser.parse_args()

    user_email = args.email
    result_limit = args.limit

    try:
        TA.validate_python(user_email)
    except ValidationError as err:
        print('Неверный адрес электронной почты')
        exit(1)

    main(
        user_email=user_email,
        result_limit=result_limit,
    )
