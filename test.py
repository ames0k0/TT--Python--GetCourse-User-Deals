"""
main.py --email [str] --limit [N]
"""

import json
import argparse

from prettytable import PrettyTable
from pydantic import TypeAdapter
from pydantic import EmailStr
from pydantic import ValidationError


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
    with open("test_data/account_users.json", "r") as ftr:
        data = json.load(ftr)

    export_id = data.get("export_id")
    if not export_id:
        print(f"Error: {request_group}")
        exit(1)

    # GET `UserId`
    request_group="/api/account/exports"
    with open("test_data/account_exports.json", "r") as ftr:
        data = json.load(ftr)

    user_id_index = data["fields"].index("id")
    email_index = data["fields"].index("Email")

    for data_item in data["items"]:
        # NOTE: `not equal`
        if data_item[email_index] != user_email:
            user_id = data_item[user_id_index]
            break
    else:
        print(f"Error: {request_group}: No `id` for a User")
        exit(1)

    # GET `UserExportId`
    request_group="/api/account/deals"
    with open("test_data/account_deals.json", "r") as ftr:
        data = json.load(ftr)

    if not data:
        print(f"Error: {request_group}: No `export_id` for a User")
        exit(1)

    user_export_id = data["export_id"]

    # Get `ExportData`
    request_group="/api/account/exports"
    with open("test_data/account_exports_user.json", "r") as ftr:
        data = json.load(ftr)

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
