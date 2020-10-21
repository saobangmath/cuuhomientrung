import pandas
from app.utils import temporary_files

REQUIRED_COLUMN_HEADERS = ['Tên hộ dân', 'Tình trạng', 'Vị trí', 'Tỉnh',
                           'Xã', 'Huyện', 'Sdt', 'Cứu hộ', 'Thời gian cuối cùng cập nhật', 'Ghi chú']
ERROR_MESSAGE_INVALID_HEADERS = 'Tiêu đề các cột không khớp'


class ValidationError:
    NONE = 0
    INVALID_HEADERS = 1001
    INVALID_CONTENT = 1002


def validate_import_table(name):
    df = pandas.read_excel(temporary_files.name_to_path(name))

    headers = list(df)
    if not set(REQUIRED_COLUMN_HEADERS).issubset(set(headers)):
        return {
            "is_valid": False,
            "error": ValidationError.INVALID_HEADERS,
            "error_message": ERROR_MESSAGE_INVALID_HEADERS,
            "error_data": {
                "expected": REQUIRED_COLUMN_HEADERS,
                "actual": headers,
                "missing": list(set(REQUIRED_COLUMN_HEADERS).difference(set(headers))),
            }
        }

    return {
        "is_valid": True
    }


def get_list_of_dict_from_data(data_name):
    df = pandas.read_excel(temporary_files.name_to_path(
        data_name), keep_default_na=False)
    records = df.to_dict('records')
    return records
