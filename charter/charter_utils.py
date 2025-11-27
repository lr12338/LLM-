import base64
import email
import json
import re
import time
from datetime import datetime

import openpyxl
from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
from Crypto.Util.Padding import pad, unpad
import base64
import mysql.connector
import pandas as pd
import requests
from gmssl import sm4
import unicodedata

def desensitize_text(user_text: str) -> str:
    """对用户邮件body的邮箱地址和电话进行脱敏"""
    # 脱敏邮箱
    user_text = re.sub(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', '***@***.***', user_text)
    # 脱敏电话号码
    user_text = re.sub(r'((\+\d{1,3}[- ]?)?\d{3,4}[- ]?\d{3,4}[- ]?\d{3,4})', '***-****-****', user_text)
    # 脱敏公司名称
    user_text = re.sub(r'([\u4e00-\u9fa5\w]+公司|Company|Corp|Inc|Ltd)', '***公司', user_text, flags=re.IGNORECASE)
    return user_text

def extract_reply(email_body: str) -> str:
    """
    从邮件正文中提取用户的回复部分，去除被回复的原始邮件内容
    """
    reply_patterns = [
        r"^-{2,}.*原始邮件.*-{2,}$",
        r"^-{2,}.*回复邮件.*-{2,}$",
        r"^-{2,}.*Original Message.*-{2,}$",
        r"On .+ wrote:",
        r"From: .+",
        r"发件人: .+",
        r"发送时间: .+",
        r"收件人: .+",
        r"主题: .+",
    ]

    for pattern in reply_patterns:
        match = re.search(pattern, email_body, re.IGNORECASE)
        if match:
            return email_body[:match.start()].strip()

    return email_body.strip()

import base64

class Sm4Util:
    KEY = b"4&Wxb6^cnu9vrqv3"
    IV  = b"Cv5$3@9Q33MTEj7e"

    @staticmethod
    def _normalize_string(s: str) -> str:
        if s is None:
            s = ""
        s = s.lstrip("\ufeff")
        s = s.strip()
        s = "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")
        return s

    @staticmethod
    def encrypt(data, key: bytes = None, iv: bytes = None, debug: bool = False) -> str:
        if key is None:
            key = Sm4Util.KEY
        if iv is None:
            iv = Sm4Util.IV

        data_str = str(data)
        data_str = Sm4Util._normalize_string(data_str)

        data_bytes = data_str.encode("utf-8")
        crypt_sm4 = CryptSM4()
        crypt_sm4.set_key(key, SM4_ENCRYPT)
        encrypted_bytes = crypt_sm4.crypt_cbc(iv, data_bytes)

        return base64.b64encode(encrypted_bytes).decode("utf-8")

    @staticmethod
    def decrypt(encrypted_data: str, key: bytes = None, iv: bytes = None) -> str:
        """
        SM4 CBC PKCS5Padding 解密，传入 Base64 字符串
        """
        if key is None:
            key = Sm4Util.KEY
        if iv is None:
            iv = Sm4Util.IV

        crypt_sm4 = CryptSM4()
        crypt_sm4.set_key(key, SM4_DECRYPT)

        encrypted_bytes = base64.b64decode(str(encrypted_data))
        decrypted_padded = crypt_sm4.crypt_cbc(iv, encrypted_bytes)
        decrypted = unpad(decrypted_padded, 16)

        return decrypted.decode("utf-8")

from config import region_system, shiptype_system


def call_deepseek_region(port,retries=5, delay=10):
    """
    调用 DeepSeek API 解析单封邮件内容，返回 JSON 数据
    """
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-6d670ffb122c49d0ae69720a9e45e8f5"
    }

    attempt = 0
    while attempt < retries:
        try:
            system_prompt = region_system
            user_prompt = port
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            payload = {
                "model": "deepseek-v3",
                "messages": messages,
                # "response_format": {"type": "json_object"},
                # "Stream": False
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    content = response_data['choices'][0]['message']['content']
                    match = re.search(r'\{[\s\S]*\}', content)
                    if match:
                        json_content = match.group(0)
                        json_content_no_comments = re.sub(r'//.*', '', json_content)
                        json_content_fixed = json_content_no_comments.replace("None", "null")

                        try:
                            result = json.loads(json_content_fixed)
                            print(json.dumps(result, indent=2, ensure_ascii=False))  # 美化输出 JSON
                        except json.JSONDecodeError as e:
                            result = {}
                    else:
                        result = {}

                except json.JSONDecodeError:
                    result = {}

                if result.get('intent', '') == "unknown":
                    result = {}

                return result

            else:

                attempt += 1
                time.sleep(delay)

        except Exception as e:
            attempt += 1
            if attempt == retries:
                return {}
def call_deepseek_shiptype(shiptype,retries=5, delay=10):
    """
    调用 DeepSeek API 解析单封邮件内容，返回 JSON 数据
    """
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-6d670ffb122c49d0ae69720a9e45e8f5"
    }

    attempt = 0
    while attempt < retries:
        try:
            system_prompt = shiptype_system
            user_prompt = shiptype
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            payload = {
                "model": "deepseek-v3",
                "messages": messages,
                # "response_format": {"type": "json_object"},
                # "Stream": False
            }

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    content = response_data['choices'][0]['message']['content']
                    match = re.search(r'\{[\s\S]*\}', content)
                    if match:
                        json_content = match.group(0)
                        json_content_no_comments = re.sub(r'//.*', '', json_content)
                        json_content_fixed = json_content_no_comments.replace("None", "null")

                        try:
                            result = json.loads(json_content_fixed)
                            print(json.dumps(result, indent=2, ensure_ascii=False))  # 美化输出 JSON
                        except json.JSONDecodeError as e:
                            result = {}
                    else:
                        result = {}

                except json.JSONDecodeError:
                    result = {}

                if result.get('intent', '') == "unknown":
                    result = {}

                return result

            else:

                attempt += 1
                time.sleep(delay)

        except Exception as e:
            attempt += 1
            if attempt == retries:
                return {}
from email.utils import parseaddr
def convert_date(mail_date):
    """转换邮件日期的格式"""
    parsed_date = email.utils.parsedate_tz(mail_date)

    if parsed_date:
        date_obj = datetime.fromtimestamp(email.utils.mktime_tz(parsed_date))
        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
    return None

def parse_range(value):
    """解析范围值（如'10000-20000'或'25.5-30'）"""
    if '-' in str(value):
        parts = str(value).split('-')
        return float(parts[0]), float(parts[1])
    return float(value), float(value)


from email.header import decode_header

def clean_sender_name(sender_name_raw):
    try:
        decoded_parts = decode_header(sender_name_raw)
        decoded = ''.join([
            part.decode(encoding or 'utf-8') if isinstance(part, bytes) else part
            for part, encoding in decoded_parts
        ])
    except Exception:
        return ""

    cleaned = ''.join(c for c in decoded if c.isprintable())
    if re.fullmatch(r"[\w\u4e00-\u9fff\s\.\-]+", cleaned):
        return cleaned
    return ""

def fuzzy_port_match(port1, port2, region1, region2):
    if not all(isinstance(x, str) for x in [port1, port2, region1, region2]):
        return False

    if len(port1.strip()) == 5:
        port1_clean = port1.replace(" ", "").lower()
        port2_clean = port2.replace(" ", "").lower()
        return port1_clean in port2_clean or port2_clean in port1_clean
    else:
        region1_clean = region1.replace(" ", "").lower()
        region2_clean = region2.replace(" ", "").lower()
        return region1_clean in region2_clean or region2_clean in region1_clean

def check_date_overlap(open_start_date, open_end_date,laycan_start_date, laycan_end_date):
    """
    日期区间匹配：判断船盘 open_date 与货盘的装港消约期是否重合
    :param open_start_date:
    :param open_end_date:
    :param laycan_start_date:
    :param laycan_end_date:
    :return:
    """
    try:
        open_start_dt = pd.to_datetime(open_start_date)
        open_end_dt = pd.to_datetime(open_end_date)
        laycan_start_dt = pd.to_datetime(laycan_start_date)
        laycan_end_dt = pd.to_datetime(laycan_end_date)
        return not (open_end_dt < laycan_start_dt or open_start_dt > laycan_end_dt)
    except Exception as e:
        return False


def parse_dwt_range(dwt_str):
    """
    解析载重吨要求字符串，并返回范围[min, max]
    当字符串形如 "25000-30000" 时，直接转换；若只有一个数字时，可使用 A左右规则（上下各加减25%）
    :param dwt_str:
    :return:
    """
    try:
        if isinstance(dwt_str, str):
            dwt_clean = dwt_str.replace(" ", "")
            if '-' in dwt_clean:
                parts = dwt_clean.split('-')
                if len(parts) == 2:
                    min_dwt, max_dwt = map(float, parts)
                    return min_dwt, max_dwt
            # 当只提供一个数字时，默认为 A左右, 上下各加减25%
            dwt_val = float(dwt_clean)
            return dwt_val * 0.75, dwt_val * 1.25
        return None, None
    except Exception as e:
        return None, None

def clean_port(text: str) -> str:
    """
    去除字符串中间的空格和 -，并且转换为大写
    """
    if not isinstance(text, str):
        return ""

    text = text.replace(" ", "")
    text = text.replace("-", "")
    text = text.upper()
    return text

import re
from datetime import datetime, timedelta

def extract_sender_info(email_body: str,
                        fallback_sender_name="",
                        fallback_sender_email="",
                        fallback_date=""):
    """
    从转发邮件正文中提取发件人名称、邮箱地址和发件时间（标准格式）。
    如果不是转发邮件，则使用原始邮件头信息（通过 fallback_* 参数传入）。
    """

    sender_patterns = [
        r'发件人[：:]\s*"?([^"<\n\r]*)"?\s*<([^<>]+)>',
        r'From:\s*"?([^"<\n\r]*)"?\s*<([^<>]+)>',
        r'From:\s*([^@<\s]+)@([a-zA-Z0-9.-]+)',
    ]

    time_field_patterns = [
        r'(?:发送日期|发送时间|日期)[：:\s]+(.+?)(?:\r?\n|$)',
        r'(?:Date|Sent on|Sent|Time)[：:\s]+(.+?)(?:\r?\n|$)',
        r'On\s+(.+?),\s+.*wrote:',
    ]

    time_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M",
        "%Y.%m.%d %H:%M",
        "%Y年%m月%d日(%a) %H:%M",
        "%Y年%m月%d日 %H:%M",
        "%b %d, %Y %H:%M",
        "%a, %b %d, %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S",
        "%a %b %d %H:%M:%S %Y",
        "%a, %d %b %y %H:%M:%S",
    ]

    sender_name = None
    sender_email = None
    received_time = None

    # 先匹配正文中的转发信息
    for pattern in sender_patterns:
        match = re.search(pattern, email_body, re.IGNORECASE)
        if match:
            sender_name = match.group(1).strip() if match.lastindex >= 2 else ""
            sender_email = match.group(2).strip() if match.lastindex >= 2 else match.group(0)
            break

    for pattern in time_field_patterns:
        match = re.search(pattern, email_body, re.IGNORECASE)
        if match:
            raw_time = match.group(1).strip()
            raw_time = re.sub(r"[（(][^)）]{1,6}[)）]", "", raw_time)
            for fmt in time_formats:
                try:
                    dt = datetime.strptime(raw_time, fmt)
                    if not dt.tzinfo:
                        dt += timedelta(hours=0)  # 默认按北京时间
                    received_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    break
                except:
                    continue
            if received_time:
                break

    # 如果没有匹配到转发信息，就用邮件本身的发件人信息
    if not sender_name:
        sender_name = fallback_sender_name
    if not sender_email:
        sender_email = fallback_sender_email
    if not received_time:
        received_time = convert_date(fallback_date)

    return {
        "sender_name": sender_name,
        "sender_email": sender_email,
        "received_time": received_time
    }


def get_portid(portcode, portname):
    conn = None
    cursor = None
    result = None

    try:
        conn = mysql.connector.connect(
            host='rdsrieyar2qii22298.mysql.rds.aliyuncs.com',
            user='purpose_identify',
            password='sdfso1@@F!$ttMsal',
            database='ihsdata',
            port=3306
        )
        cursor = conn.cursor(dictionary=True)

        # 先按 portname 精确匹配
        if portname:
            name_clean = portname.strip()
            if name_clean:
                cursor.execute(
                    "SELECT portid FROM port_data WHERE LOWER(portname) = %s LIMIT 1",
                    (name_clean.lower(),)
                )
                rows = cursor.fetchall()
                if rows:
                    result = rows[0]

        # 如果没有精确命中，且 portname 较长，再做前缀匹配
        MIN_PREFIX_LEN = 3
        if result is None and portname:
            name_clean = portname.strip()
            if len(name_clean) >= MIN_PREFIX_LEN:
                cursor.execute(
                    "SELECT portid FROM port_data WHERE LOWER(portname) LIKE %s LIMIT 1",
                    (f"{name_clean.lower()}%",)
                )
                rows = cursor.fetchall()
                if rows:
                    result = rows[0]

        # 最后按 portcode 查
        if result is None and portcode:
            cursor.execute(
                "SELECT portid FROM port_data WHERE portcode = %s LIMIT 1",
                (portcode,)
            )
            rows = cursor.fetchall()
            if rows:
                result = rows[0]

        return result["portid"] if result else None

    except Exception as e:
        print("DB error:", e)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



def fetch_imo_email_records():
    """
    从数据库查询 IMO-邮箱 映射关系，返回 List[Dict] 格式
    """
    conn = mysql.connector.connect(
        host='rdsrieyar2qii22298.mysql.rds.aliyuncs.com',
        user='purpose_identify',
        password= 'sdfso1@@F!$ttMsal',
        database= 'ihs_shipdata_2020',
        port= 3306
    )
    cursor = conn.cursor(dictionary=True)

    union_sql = """
    SELECT t1.mmsi, t1.imo, t2.Emailaddress 
    FROM shipdata t1 
    LEFT JOIN companyfulldetailswithcodesandparent t2 
        ON t1.OperatorCompanyCode = t2.owcode 
    WHERE t2.Emailaddress IS NOT NULL AND t1.mmsi IS NOT NULL

    UNION

    SELECT t1.mmsi, t1.imo, t2.Emailaddress 
    FROM shipdata t1 
    LEFT JOIN companyfulldetailswithcodesandparent t2 
        ON t1.RegisteredOwnerCode = t2.owcode 
    WHERE t2.Emailaddress IS NOT NULL AND t1.mmsi IS NOT NULL

    UNION

    SELECT t1.mmsi, t1.imo, t2.Emailaddress 
    FROM shipdata t1 
    LEFT JOIN companyfulldetailswithcodesandparent t2 
        ON t1.ShipManagerCompanyCode = t2.owcode 
    WHERE t2.Emailaddress IS NOT NULL AND t1.mmsi IS NOT NULL

    UNION

    SELECT t1.mmsi, t1.imo, t2.Emailaddress 
    FROM shipdata t1 
    LEFT JOIN companyfulldetailswithcodesandparent t2 
        ON t1.GroupBeneficialOwnerCompanyCode = t2.owcode 
    WHERE t2.Emailaddress IS NOT NULL AND t1.mmsi IS NOT NULL;
    """

    cursor.execute(union_sql)
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results


COMMON_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "icloud.com", "mail.com", "163.com", "126.com",
    "qq.com", "yeah.net", "sina.com", "sohu.com", "foxmail.com"
}


def get_email_domain(email):
    """
    提取邮箱的域名（后缀）
    """
    if not email or "@" not in email:
        return ""

    return email.split("@")[-1]

def is_same_company(sender_email, imo, imo_email_records):
    """
    判断发件人邮箱是否属于IMO公司（同域名，且非公共邮箱）
    sender_email: 发件人邮箱（如 test@hifleet.com）
    imo: 对应船的 IMO 编号
    imo_email_records: 来自SQL查询结果的字典列表，每项包含 mmsi, imo, Emailaddress
    """
    sender_domain = get_email_domain(sender_email)
    if sender_domain in COMMON_EMAIL_DOMAINS:
        return 0  # 公共邮箱不能判断为所属公司

    # 获取 IMO 相关公司邮箱的域名集合
    company_domains = {
        get_email_domain(row["Emailaddress"])
        for row in imo_email_records
        if str(row.get("imo")) == str(imo) and row.get("Emailaddress")
    }

    # 判断是否存在相同域名，且该域名不为公共邮箱
    for domain in company_domains:
        if domain == sender_domain and domain not in COMMON_EMAIL_DOMAINS:
            return 1
    return 0


def load_imo_email_records_from_xlsx(filepath):
    """ 从 Excel 文件加载 IMO 邮箱数据 """
    wb = openpyxl.load_workbook(filepath)
    sheet = wb.active

    records = []
    for row in sheet.iter_rows(min_row=2, values_only=True):  # 跳过表头
        mmsi, imo, email = row
        records.append({
            "mmsi": str(mmsi).strip() if mmsi else "",
            "imo": str(imo).strip() if imo else "",
            "Emailaddress": str(email).strip() if email else ""
        })
    return records



# def is_same_company(sender_email, imo, imo_email_records):
#     """
#     判断发件人邮箱是否属于IMO公司（同域名，且非公共邮箱）
#
#     sender_email: 发件人邮箱（如 test@hifleet.com）
#     imo: 对应船的 IMO 编号
#     imo_email_records: 来自SQL查询结果的字典列表，每项包含 mmsi, imo, Emailaddress
#     """
#     sender_domain = get_email_domain(sender_email)
#     if sender_domain in COMMON_EMAIL_DOMAINS:
#         return 0  # 公共邮箱不能判断为所属公司
#
#     # 获取 IMO 相关公司邮箱的域名集合
#     company_domains = {
#         get_email_domain(row["Emailaddress"])
#         for row in imo_email_records
#         if str(row.get("imo")) == str(imo) and row.get("Emailaddress")
#     }
#     print(company_domains)
#     # 判断是否存在相同域名，且该域名不为公共邮箱
#     for domain in company_domains:
#         if domain == sender_domain and domain not in COMMON_EMAIL_DOMAINS:
#             return 1
#
#     return 0


def sanitize_date(input_date):
    """
    处理无效日期格式，将0000-00-00转为None
    支持字符串、datetime对象等多种输入格式
    """
    if input_date in (None, '', '0000-00-00', '0000-00-00 00:00:00'):
        return None

    if isinstance(input_date, str):
        try:
            # 尝试解析日期字符串
            parsed_date = datetime.strptime(input_date.split()[0], '%Y-%m-%d')
            if parsed_date.year == 0:
                return None
            return input_date
        except ValueError:
            return None

    if isinstance(input_date, datetime):
        if input_date.year == 0:
            return None
        return input_date

    return None

def extract_numeric(text):
    if not text:
        return None
    match = re.search(r'(\d+(\.\d+)?)', str(text))
    if match:
        return float(match.group(1))
    return None

def classify_vessel_type(shiptype, minotype, port_shiptype,dwt):
    """
    根据船舶类型（shiptype）、子类型（minotype）和载重吨（dwt）分类。
    """

    if not dwt:
        return None

    # ---------- 散货船/杂货船 Bulk Carriers ----------
    if shiptype in ["Bulk Carriers", "Dry Cargo/Passenger"] or port_shiptype in ["杂货船", "散货船"]:
        if 1000 <= dwt < 10000:
            return "Mini Bulk"
        elif 10000 <= dwt < 25000:
            return "Small Handy"
        elif 25000 <= dwt < 40000:
            return "Handysize"
        elif 40000 <= dwt < 50000:
            return "Handymax"
        elif 50000 <= dwt < 65000:
            return "Supramax / Ultramax"
        elif 65000 <= dwt < 80000:
            return "Panamax"
        elif 80000 <= dwt < 93000:
            return "Neo-Panamax"
        elif 93000 <= dwt < 99000:
            return "Post-Panamax"
        elif 100000 <= dwt < 120000:
            return "Baby Cape"
        elif 120000 <= dwt < 180000:
            return "Capesize"
        elif 180000 <= dwt <= 400000:
            return "VLBC / VLOC"
        else:
            return None


    # ---------- 油船 Tankers ----------
    elif shiptype == "Tankers":
        if minotype == "Crude Oil Tanker":
            if 55000 <= dwt < 85000:
                return 'Aframax'
            elif 85000 <= dwt < 125000:
                return 'Panamax'
            elif 125000 <= dwt < 200000:
                return 'Suezmax'
            elif dwt >= 200000:
                return 'UL/VLCC'
            else:
                return None

        elif minotype == "Oil Products Tanker" or minotype == "Chemical/Oil Products Tanker":
            if dwt < 10000:
                return 'Small Tanker'
            elif 10000 <= dwt < 25000:
                return 'LR1'
            elif 25000 <= dwt < 55000:
                return 'LR2'
            elif 55000 <= dwt < 85000:
                return 'MR/Handy'
            elif 85000 <= dwt < 125000:
                return 'SR Products'
            elif 125000 <= dwt < 200000:
                return 'Suezmax'
            else:
                return None

    else:
        return None


def generate_vessel_tags(row):
    """
    根据 charter_open_vessels 单行记录生成标签。
    :param row: dict，包含表中字段的记录
    :return: str，逗号分隔的标签
    """
    import mysql.connector

    tags = []

    vessel_age = row.get("vessel_age")
    is_geared = row.get("is_geared")
    crane_type = row.get("crane_type", "")
    hatch_size = row.get("hatch_size")  # 单位：米
    hold_capacity_cbm = row.get("hold_capacity_cbm")  # 单位：立方米
    deck_strength = row.get("deck_strength")  # 单位：t/m2
    fuel_type = row.get("fuel_type", "")
    reefer_plugs = row.get("reefer_plugs")
    dg_approved = row.get("dg_approved")
    sprinkler_system = row.get("sprinkler_system")
    open_type = row.get("open_type", "")
    imo = row.get("imo")
    is_cis = row.get("is_cis")
    is_bh = row.get("is_bh")
    is_aus = row.get("is_aus")
    is_boxhold = row.get("is_boxhold")
    is_no_iran = row.get("is_no_iran")

    conn = mysql.connector.connect(
        host='rdsrieyar2qii22298.mysql.rds.aliyuncs.com',
        user='purpose_identify',
        password='sdfso1@@F!$ttMsal',
        database='ihs_shipdata_2020',
        port=3306
    )
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT YearOfBuild, GearTypeLargest, Gearless, LargestHatchBreadth, LargestHatchLength,
               GrainCapacity, ReeferPoints, GearDescriptiveNarrative, Deadweight, ShiptypeLevel2,
               ShiptypeLevel4
        FROM ihs_shipdata_2020.shipdata
        WHERE imo = %s
        LIMIT 1
    """
    cursor.execute(query, (imo,))
    result = cursor.fetchone()
    if result is None:
        result = {}
    year_of_build = result.get("YearOfBuild")
    dwt = result.get("Deadweight")
    ship_type = result.get("ShiptypeLevel2")
    minotype = result.get("ShiptypeLevel4")
    cursor.close()
    conn.close()

    # 查询挂靠船舶是否挂靠过制裁国家
    conn2 = mysql.connector.connect(
        host='rm-2zeen2o6509ka50l7.mysql.rds.aliyuncs.com',
        user='db55o2pytj4vx12b',
        password='dzjymyylla@JFYF1997',
        database='dataanalysis',
        port=3306
    )
    cursor2 = conn2.cursor(dictionary=True)

    query2 = """
        SELECT DISTINCT country 
        FROM dataanalysis.port_of_call_israel 
        WHERE imonumber = %s
    """
    cursor2.execute(query2, (imo,))
    result2 = cursor2.fetchall()

    cursor2.close()
    conn2.close()
    country_tag_map = {
        "Iran": "IRAN",
        "Israel": "ISRAEL",
        "Russia": "RUSSIA",
        "Venezuela": "VENEZUELA"
    }

    if result2:
        for r in result2:
            country = r.get("country")
            if country in country_tag_map:
                tag = country_tag_map[country]
                if tag not in tags:
                    tags.append(tag)

    # 查询制裁风险
    conn1 = mysql.connector.connect(
        host='rdsrieyar2qii22298.mysql.rds.aliyuncs.com',
        user='purpose_identify',
        password='sdfso1@@F!$ttMsal',
        database='pscdata',
        port=3306
    )
    cursor1 = conn1.cursor(dictionary=True)
    query1 = """
            select risk_score from pscdata.ship_risk_score where imo = %s
        """
    cursor1.execute(query1,(imo,))
    result1 = cursor1.fetchone()
    cursor1.close()
    conn1.close()
    if result1 and "risk_score" in result1:
        score = result1["risk_score"]
        if score >= 45:
            tags.append("High PSC Risk")
        elif 25 <= score <= 44:
            tags.append("Medium PSC Risk")

    url = "http://172.17.137.177:18005/shipdetail/sanction/assess/shiprisk"
    params = {
        "imonumber": imo,
        "innercall": "1"
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=(3, 5))
        response.raise_for_status()
        api_result = response.json()
        data = api_result.get("data") or {}
        risk_level = data.get("riskLevel")

        if risk_level == 2:
            tags.append("High Sanction Risk")
        elif risk_level == 1:
            tags.append("Medium Sanction Risk")

    except requests.exceptions.RequestException as e:
        pass

    if is_cis == 1:
        tags.append("CIS")
    if is_bh == 1:
        tags.append("BH")
    if is_aus == 1:
        tags.append("AUS")
    if is_boxhold == 1:
        tags.append("Box Hold")
    if is_no_iran == 1:
        tags.append("NO IRAN/ISRAEL/YEMEN")
    # # -------- 年龄标签 --------
    # if vessel_age is not None:
    #     if vessel_age <= 3:
    #         tags.append("Newbuilding")
    #     elif 4 <= vessel_age <= 10:
    #         tags.append("Modern")
    #     elif vessel_age >= 15:
    #         tags.append("Old (>15Y)")
    # else:
    #     year_of_build = result.get("YearOfBuild")
    #     if year_of_build is not None:
    #         vessel_age = datetime.now().year - year_of_build
    #         if vessel_age <= 3:
    #             tags.append("Newbuilding")
    #         elif 4 <= vessel_age <= 10:
    #             tags.append("Modern")
    #         elif vessel_age >= 15:
    #             tags.append("Old (>15Y)")

    # -------- 装卸设备 --------
    gearless = result.get("Gearless")
    if gearless == "Y":
        tags.append("Gearless")
    elif gearless == "N":
        tags.append("Geared")
    elif is_geared is not None:
        tags.append("Geared" if is_geared else "Gearless")

    # gear_desc = result.get("GearDescriptiveNarrative", "")
    # if gear_desc and any(x in gear_desc for x in ["100", "120", "150", "200"]):
    #     tags.append("Heavy Lift")

    # -------- 舱型相关 --------
    # breadth = result.get("LargestHatchBreadth")
    # length = result.get("LargestHatchLength")
    # if breadth and length and hold_capacity_cbm:
    #     # if min(breadth, length) >= 8 and hold_capacity_cbm >= 50000:
    #     #     tags.append("Box Hold")
    #     if hold_capacity_cbm >= 60000:
    #         tags.append("Grain Fitted")
    #
    # if breadth and length:
    #     if min(breadth, length) < 8:
    #         tags.append("Non-GRABS")
    #     elif min(breadth, length) >= 10 and ("tween" not in crane_type.lower() if crane_type else True):
    #         tags.append("GRABS-Full")
    #     elif min(breadth, length) >= 8:
    #         tags.append("GRABS-Ltd")

    # -------- 甲板强度 --------
    # deck_strength_val = extract_numeric(deck_strength)
    # if deck_strength_val and breadth and length:
    #     if deck_strength_val >= 10 and min(breadth, length) >= 12:
    #         tags.append("Logger")
    #     elif deck_strength_val >= 5 and min(breadth, length) >= 10:
    #         tags.append("Logger--")

    # -------- 燃料与环保 --------
    eco_keywords = [
        "lng", "低硫", "lsfo", "ammonia", "nh3",
        "methanol", "甲醇", "biofuel", "生物燃料", "dual fuel", "dual-fuel",
        "lpg", "ethanol", "电推进", "electric", "hybrid", "碳中和", "carbon neutral",
        "future fuel", "new fuel"
    ]
    fuel_ls_keywords = [
        ("hsfo", "scrubber"),
        ("high sulfur", "scrubber"),
        ("3.5%", "scrubber"),
        ("高硫", "脱硫"),
        ("residual fuel", "scrubber")
    ]
    fuel_type_lc = fuel_type.lower() if fuel_type else ""

    if any(k in fuel_type_lc for k in eco_keywords):
        tags.append("Eco")

    for key1, key2 in fuel_ls_keywords:
        if key1 in fuel_type_lc and key2 in fuel_type_lc:
            tags.append("Fuel-LS")
            break

    # -------- 冷藏插座 --------
    # reefer_points = result.get("ReeferPoints")
    # if reefer_points is not None:
    #     if reefer_points > 0:
    #         tags.append("COR")
    #     else:
    #         tags.append("Non-COR")

    # -------- 危险品 & 喷淋 --------
    if dg_approved == 1:
        tags.append("DG Approved")
    if sprinkler_system == 1:
        tags.append("Sprinkler")

    return {
            "tags": ",".join(tags),
            "YearOfBuild": year_of_build,
            "dwt": dwt,
            "shiptype":ship_type,
            "minotype":minotype
        }

def generate_cargo_tags(row: dict) -> str:
    """
    根据 charter_cargo 单行记录生成标签。
    :param row: dict
    :return: str，逗号分隔的标签
    """
    tags = []

    cargo_type = (row.get("cargo_type") or "").lower()
    cargo_quantity = row.get("cargo_quantity")
    is_bulk = row.get("is_bulk")
    requires_geared = row.get("requires_geared")
    is_dg_cargo = row.get("is_dg_cargo")
    reefer_required = row.get("reefer_required")
    deck_cargo_allowed = row.get("deck_cargo_allowed")
    packaging = row.get("packaging") or ""
    allowed_vessel_types = row.get("allowed_vessel_types") or ""
    max_age_limit = row.get("max_age_limit")
    class_restriction = row.get("class_restriction")
    hold_type = row.get("hold_type") or ""
    hatch_type = row.get("hatch_type") or ""

    # -------- 货物种类 --------
    if "coal" in cargo_type or "煤" in cargo_type:
        tags.append("Coal")
    elif "grain" in cargo_type or "谷" in cargo_type or "豆" in cargo_type:
        tags.append("Grain")
    elif "iron" in cargo_type or "矿" in cargo_type:
        tags.append("Ore")
    elif "steel" in cargo_type or "钢" in cargo_type:
        tags.append("Steel")
    elif "fertilizer" in cargo_type or "肥料" in cargo_type:
        tags.append("Fertilizer")
    elif "container" in cargo_type or "集装箱" in cargo_type:
        tags.append("Container")


    # -------- 数量规模 --------
    if cargo_quantity:
        try:
            qty = float(cargo_quantity)
            if qty < 10000:
                tags.append("Small Parcel")
            elif 10000 <= qty <= 50000:
                tags.append("Handy/Handymax")
            elif 50000 < qty <= 100000:
                tags.append("Panamax")
            else:
                tags.append("Capesize")
        except ValueError:
            pass

    # -------- 散装 or 包装 --------
    if is_bulk == 1:
        tags.append("Bulk")
    elif is_bulk == 0:
        tags.append("Breakbulk")

    if "bag" in packaging.lower() or "袋" in packaging:
        tags.append("Bagged")
    if "pallet" in packaging.lower() or "托盘" in packaging:
        tags.append("Palletized")

    # -------- 装卸要求 --------
    if requires_geared == 1:
        tags.append("Gear Required")
    elif requires_geared == 0:
        tags.append("Gearless Accepted")

    # -------- 特殊需求 --------
    if is_dg_cargo == 1:
        tags.append("Dangerous Cargo")
    if reefer_required and int(reefer_required) > 0:
        tags.append("Reefer Required")
    if deck_cargo_allowed == 1:
        tags.append("Deck Cargo Accepted")

    # -------- 船型 / 船级限制 --------
    # if allowed_vessel_types:
    #     tags.append(f"Allowed Types: {allowed_vessel_types}")
    # if max_age_limit:
    #     tags.append(f"Max Age {max_age_limit}Y")
    # if class_restriction:
    #     tags.append(f"Class: {class_restriction}")

    # -------- 舱型舱盖 --------
    # if hold_type:
    #     tags.append(f"Hold: {hold_type}")
    # if hatch_type:
    #     tags.append(f"Hatch: {hatch_type}")

    return ",".join(tags)


def parse_range_sp(value):
    """解析'2003-2006'或'2005'成(min, max)"""
    if value is None:
        return None, None
    value = str(value).strip()
    if '-' in value:
        try:
            min_val, max_val = value.split('-', 1)
            return float(min_val.strip()), float(max_val.strip())
        except ValueError:
            return None, None
    else:
        try:
            num = float(value)
            return num, num
        except ValueError:
            return None, None


def check_range_from(buy_value, sell_value):
    """直接传入买方范围字符串和卖方数值/字符串，判断是否在范围内"""
    buy_min, buy_max = parse_range_sp(buy_value)

    if buy_min is None and buy_max is None:
        return True

    if sell_value is None:
        return False

    try:
        sell_num = float(sell_value)
    except:
        return False

    if buy_min is not None and sell_num < buy_min:
        return False
    if buy_max is not None and sell_num > buy_max:
        return False
    return True


def clean_value(value):
    """空值处理：None、空字符串、'null' 统一为 None"""
    if value is None:
        return None
    if isinstance(value, str):
        val = value.strip()
        if val.lower() == "null" or val == "":
            return None
        return val
    return value

def clean_imo(imo):
    """IMO 校验：必须是 7 位数字，否则为 None"""
    if imo and re.fullmatch(r"\d{7}", str(imo).strip()):
        return str(imo).strip()
    return None


