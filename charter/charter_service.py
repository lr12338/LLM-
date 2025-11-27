import email
import imaplib
import json
import re
import threading
import traceback
from email.utils import parseaddr, parsedate_to_datetime

import pytz
import requests
import schedule
import time
from datetime import datetime, timedelta
from config import DATABASE_CONFIG,charter_log_dir,system_text,user_text


import mysql.connector
import logging
from log_config import get_logger
import concurrent.futures

from db_utils import get_db_connection
scheduled_users = {}
logger = get_logger("charter_logger", "vessel_charter.log", log_dir=charter_log_dir)

from charter_utils import sanitize_date, generate_vessel_tags, extract_reply, desensitize_text, convert_date, \
    clean_port, fetch_imo_email_records, fuzzy_port_match, extract_sender_info, clean_sender_name, \
    generate_cargo_tags, call_deepseek_region, load_imo_email_records_from_xlsx, get_portid, classify_vessel_type, \
    call_deepseek_shiptype
from charter_utils import is_same_company,check_date_overlap,parse_dwt_range


import email
from email.header import decode_header
from email.utils import parseaddr
import chardet
import logging
import re


def safe_decode_header(raw_header):
    """安全解码邮件头部"""
    if not isinstance(raw_header, (str, bytes)):
        return ""
    try:
        parts = decode_header(raw_header)
        decoded = ""
        for part, encoding in parts:
            if isinstance(part, bytes):
                try:
                    decoded += part.decode(encoding or 'utf-8', errors='ignore')
                except Exception:
                    decoded += part.decode('utf-8', errors='ignore')
            else:
                decoded += part
        return decoded
    except Exception as e:
        logger.error(f"decode_header error: {e}")
        return ""

def parse_email(raw_email):
    """解析邮件内容，返回标准字典格式"""
    msg = email.message_from_bytes(raw_email)

    subject = safe_decode_header(msg.get("Subject"))
    from_ = msg.get("From")
    from_name, from_email = parseaddr(from_)
    date = msg.get("Date")

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")
            if content_type == "text/plain" and "attachment" not in content_disposition:
                raw_payload = part.get_payload(decode=True)
                try:
                    if raw_payload:
                        detected_encoding = chardet.detect(raw_payload)["encoding"]
                        body = raw_payload.decode(detected_encoding or 'utf-8', errors='ignore')
                except Exception as e:
                    logger.error(f"邮件内容解码失败: {e}")
                    for encoding in ['utf-8', 'ISO-8859-1', 'gbk', 'windows-1252']:
                        try:
                            body = raw_payload.decode(encoding)
                            break
                        except Exception:
                            continue
                break
    else:
        try:
            raw_payload = msg.get_payload(decode=True)
            if raw_payload:
                body = raw_payload.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"非 multipart 邮件解码失败: {e}")
            for encoding in ['ISO-8859-1', 'gbk', 'windows-1252']:
                try:
                    body = raw_payload.decode(encoding)
                    break
                except Exception:
                    continue

    email_data = {
        "from_name": from_name,
        "from_email": from_email,
        "date": date,
        "subject": subject,
        "body": body
    }

    return email_data



def get_last_parse_time(user_email, cursor):
    """获取用户上次解析的时间，如果为空，则设定为 frequency 天前"""
    try:
        cursor.execute("SELECT last_parse_time FROM charter_user_service_configuration WHERE email_user = %s", (user_email,))
        result = cursor.fetchone()
        cursor.fetchall()
    except Exception as e:
        logger.error(f"更新解析时间失败: {e}")
        raise

    if result and result['last_parse_time']:
        return result['last_parse_time']

    # 如果 last_parse_time 为空，设定为当前时间的前 frequency 天,datetime.now() - timedelta(days=frequency)
    return None


def update_last_parse_time(user_email, new_time, cursor):
    """更新用户上次解析的时间"""
    try:
        cursor.execute("UPDATE charter_user_service_configuration SET last_parse_time = %s WHERE email_user = %s",
                   (new_time, user_email))
    except Exception as e:
        logger.error(f"更新用户上次解析的时间: {e}")
        raise


from gmssl import sm4
import base64
def sm4_cbcdecrypt(ciphertext: str) -> str:
    """
    SM4/CBC/PKCS5Padding 解密 Hutool 加密的 Base64 密文。

    参数：
        ciphertext (str): Base64 编码的密文字符串

    返回：
        str: 解密后的明文
    """
    KEY = b"4&Wxb6^cnu9vrqv3"
    IV = b"Cv5$3@9Q33MTEj7e"
    encrypted_bytes = base64.b64decode(ciphertext)
    sm4_decryptor = sm4.CryptSM4()
    sm4_decryptor.set_key(KEY, sm4.SM4_DECRYPT)
    decrypted_bytes = sm4_decryptor.crypt_cbc(IV, encrypted_bytes)
    def remove_pkcs5_padding(data: bytes) -> bytes:
        pad_len = data[-1]
        if all(p == pad_len for p in data[-pad_len:]):
            return data[:-pad_len]
        return data

    decrypted_bytes = remove_pkcs5_padding(decrypted_bytes)
    return decrypted_bytes.decode('utf-8')

import imaplib
import poplib
import email
import pytz
import logging

def fetch_emails(email_user, email_password, server, port, last_parse_time, protocol):
    """获取指定时间之后的邮件，支持 IMAP / POP"""
    beijing_tz = pytz.timezone("Asia/Shanghai")

    if last_parse_time.tzinfo is None:
        last_parse_time = beijing_tz.localize(last_parse_time)
    else:
        last_parse_time = last_parse_time.astimezone(beijing_tz)

    results = []

    if protocol.lower() == "imap":
        # ---------- IMAP ----------
        try:
            mail = imaplib.IMAP4_SSL(server, port)
            mail.login(email_user, sm4_cbcdecrypt(email_password))

            status, _ = mail.select("INBOX")
            if status != "OK":
                logger.error("无法搜索收件箱")
                mail.logout()
                return []

            start_date = last_parse_time.strftime("%d-%b-%Y")
            search_criteria = f'(SINCE {start_date})'
            status, messages = mail.search(None, search_criteria)
            if status != "OK":
                logger.error("IMAP 邮件搜索失败")
                mail.logout()
                return []

            email_ids = messages[0].split()
            for eid in email_ids:
                # 获取邮件时间
                status, msg_data = mail.fetch(eid, "(INTERNALDATE RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue

                try:
                    raw_response = msg_data[0][0].decode(errors="ignore")
                    internal_date_str = raw_response.split('INTERNALDATE "')[1].split('"')[0]
                    internal_date = email.utils.parsedate_to_datetime(internal_date_str)
                    if internal_date.tzinfo is None:
                        internal_date = beijing_tz.localize(internal_date)
                    else:
                        internal_date = internal_date.astimezone(beijing_tz)
                except Exception:
                    continue

                if internal_date <= last_parse_time:
                    continue

                # 解析邮件
                raw_email = msg_data[0][1]
                email_data = parse_email(raw_email)
                if email_data:
                    results.append(email_data)

            mail.close()
            mail.logout()

        except Exception as e:
            logger.error(f"{email_user} IMAP 获取邮件失败: {e}")
            return []


    elif protocol.lower() == "pop":

        # ---------- POP ----------

        try:

            server_conn = poplib.POP3_SSL(server, port)
            poplib._MAXLINE = 10 * 1024 * 1024
            server_conn.user(email_user)
            server_conn.pass_(sm4_cbcdecrypt(email_password))
            num_messages = len(server_conn.list()[1])
            logger.info(f"{email_user} POP 收件箱共有 {num_messages} 封邮件")

            if num_messages == 0:
                server_conn.quit()
                return []

            max_check = min(num_messages, 100)

            for i in range(num_messages, num_messages - max_check, -1):
                try:
                    resp, lines, octets = server_conn.top(i, 100)
                    msg_content = b"\r\n".join(lines).decode(errors="ignore")
                    msg = email.message_from_string(msg_content)
                    date_str = msg.get("Date")
                    if not date_str:
                        continue
                    try:
                        msg_date = email.utils.parsedate_to_datetime(date_str)
                        if msg_date.tzinfo is None:
                            msg_date = beijing_tz.localize(msg_date)
                        else:
                            msg_date = msg_date.astimezone(beijing_tz)

                    except Exception as e:
                        logger.warning(f"解析 POP 邮件时间失败: {e}")
                        continue

                    if msg_date <= last_parse_time:
                        continue

                    resp, lines, octets = server_conn.retr(i)
                    full_msg = b"\r\n".join(lines)
                    email_data = parse_email(full_msg)
                    if email_data:
                        results.append(email_data)

                except poplib.error_proto as e:
                    logger.warning(f"POP 第 {i} 封邮件获取失败: {e}")
                    continue

                except Exception as e:
                    logger.warning(f"POP 第 {i} 封邮件处理异常: {e}")
                    continue
            server_conn.quit()

        except Exception as e:
            logger.error(f"{email_user} POP 获取邮件失败: {e}")
            return []
    else:
        logger.error(f"未知协议: {protocol}")
        return []

    return results

def safe_json_parse(content: str):
    """
    尝试从 content 中提取并解析 JSON，带补救逻辑
    """
    match = re.search(r'\{[\s\S]*\}', content)
    if not match:
        logger.error("未找到 JSON 数据")
        return {"intent": "unknown", "data": {}}

    json_content = match.group(0)
    json_content = re.sub(r'//.*', '', json_content)
    json_content = json_content.replace("None", "null")
    json_content = json_content.strip()
    fixed_lines = []
    for line in json_content.splitlines():
        quote_count = line.count('"')
        if quote_count % 2 == 1:  # 奇数说明有未闭合引号
            line = line.rstrip() + '"'
        fixed_lines.append(line)
    json_content = "\n".join(fixed_lines)
    # 检查 key/value 结尾缺逗号
    json_content = re.sub(r'"\s*\n(\s*[}\]])', '",\n\\1', json_content)

    try:
        result = json.loads(json_content)
        return result
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.error(f"错误的 JSON 内容: {json_content}")
        return {"intent": "unknown", "data": {}}


def call_deepseek_api(content, retries=5, delay=10):
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
            system_prompt = system_text
            extract_reply_user_text = extract_reply(user_text)
            desensitize_user_text = desensitize_text(extract_reply_user_text)
            user_prompt = desensitize_user_text.format(content=content[:5000])
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
                            # logger.info(json.dumps(result, indent=2, ensure_ascii=False))
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON 解析失败: {e}")
                            logger.error(f"错误的 JSON 内容: {json_content_fixed}")
                            result = {"intent": "unknown", "data": {}}
                    else:
                        logger.error("未找到 JSON 数据")
                        result = {"intent": "unknown", "data": {}}

                except json.JSONDecodeError:
                    logger.error(f"JSON解析失败: {e}")
                    result = {"intent": "unknown", "data": {}}

                if result.get('intent', '') == "unknown":
                    result = {"intent": "unknown", "data": {}}

                return result

            else:
                logger.info(f"API响应错误，状态码: {response.status_code}")
                attempt += 1
                time.sleep(delay)

        except Exception as e:
            attempt += 1
            logger.error(f"API调用失败: {str(e)}. 尝试 {attempt}/{retries} 次...")
            if attempt == retries:
                return {"intent": "unknown", "data": {}}

def sanitize_vessel(vessel: dict) -> dict:
    """
    清理 vessel 字典：
    - 把 "null"/"NULL"/" Null " 等字符串替换为 None
    - 其他值保持不变
    """
    if not vessel:
        return {}
    return {
        k: (None if isinstance(v, str) and v.strip().lower() == "null" else v)
        for k, v in vessel.items()
    }


def save_charter_data(email_user, user_id, emails_data, cursor):
    """
    将解析的租船船货盘数据存储到 charter_open_vessels 和 charter_cargo 表中
    :param email_user: 用户邮箱
    :param user_id: 用户账号ID
    :param emails_data: 从 fetch_emails 获取的邮件数据列表
    """

    if not emails_data:
        logging.info("没有可处理的邮件数据")
        return

    try:
        # owner_email = fetch_imo_email_records()
        for email_data in emails_data:
            # 记录已处理邮件信息
            parsed_emails_info_sql = """
                INSERT INTO charter_parsed_emails_info 
                (email_user, subject, from_name, from_email, receive_time)
                VALUES (%s, %s, %s, %s, %s)
            """
            email_values = (
                email_user, email_data["subject"], email_data["from_name"], email_data["from_email"],
                convert_date(email_data["date"])
            )
            cursor.execute(parsed_emails_info_sql, email_values)

            try:
                data = call_deepseek_api(email_data['subject'] + "\n" + email_data['body'])
                if not isinstance(data, dict):
                    raise ValueError("API 返回的数据格式不符合预期")

                intent_list = data.get('intent') or []
                charter_data = data.get('data') or {}
                now_time = datetime.now()
                match_start_time = now_time - timedelta(days=1)
                match_start_time_str = match_start_time.strftime("%Y-%m-%d %H:%M:%S")
                end_time_str = now_time.strftime("%Y-%m-%d %H:%M:%S")
                import traceback

                try:
                    if "openvessels" in intent_list and "openvessels" in charter_data:
                        for vessel in charter_data["openvessels"]:
                            try:
                                vessel = sanitize_vessel(vessel)

                                imo = vessel.get("IMO")
                                shipname = vessel.get("船名")
                                shiptype = vessel.get("船型")
                                port = clean_port(vessel.get("OPEN位置"))
                                portcode = port
                                clean_name = shipname.strip() if shipname else ""
                                year = vessel.get("建造年份")
                                dwt = vessel.get("载重吨")
                                age = None
                                mmsi = None
                                tags = None
                                dwt_type = None

                                # 清洗前缀
                                clean_name = re.sub(
                                    r'^(M\s*[\./\\]?\s*(V|T)\s*[\./\\]?\s*)',
                                    '',
                                    clean_name,
                                    flags=re.IGNORECASE
                                ).strip()

                                try:
                                    imo_int = int(str(imo).strip())
                                    if len(str(imo_int)) != 7 or imo_int == 0:
                                        imo = None
                                    else:
                                        imo = str(imo_int)
                                except (ValueError, TypeError):
                                    imo = None

                                # 如果 IMO 缺失，则调用API获取
                                if not imo:
                                    try:
                                        token = 'Ga0sTmtwDV9l2LELSXUmHdJQuAgiwJOKk2z/qkKePEq9h/L+pD46KQcb8smOSaim'
                                        url = f"https://api.hifleet.com/position/search/basicinfo/token?shipname={clean_name}&usertoken={token}"
                                        response = requests.get(url, timeout=10)
                                        data = response.json()

                                        if data.get("result") == "ok" and "list" in data:
                                            candidates = []
                                            for item in data["list"]:
                                                if item.get("name", "").lower() == shipname.lower():
                                                    imo_num = item.get("imonumber")
                                                    dwt_imo = item.get("dwt", -1)
                                                    length = item.get("length", 0)
                                                    updatetime = item.get("updatetime", "")

                                                    # 跳过无效 IMO
                                                    if not imo_num or imo_num == "0" or len(str(imo_num).strip()) != 7:
                                                        continue

                                                    dwt_imo_val = (
                                                        int(dwt_imo) if isinstance(dwt_imo, (int, float)) or str(
                                                            dwt_imo).isdigit() else -1
                                                    )
                                                    length_val = int(length) if str(length).isdigit() else 0
                                                    update_time_val = (
                                                        datetime.strptime(updatetime,
                                                                          "%Y-%m-%d %H:%M:%S") if updatetime else None
                                                    )

                                                    candidates.append({
                                                        "imo": imo_num,
                                                        "mmsi": item.get("mmsi"),
                                                        "dwt": dwt_imo_val,
                                                        "length": length_val,
                                                        "updatetime": update_time_val,
                                                        "raw": item
                                                    })

                                            # 若邮件中提取的 dwt 存在，优先匹配差值小于 1000 的候选项
                                            dwt = int(dwt)
                                            if candidates:
                                                if dwt and isinstance(dwt, (int, float)):
                                                    # 过滤差值小于1000的项
                                                    close_matches = [
                                                        c for c in candidates
                                                        if c["dwt"] > 0 and abs(c["dwt"] - dwt) <= 1000
                                                    ]

                                                    if close_matches:
                                                        # 若有接近的候选项，按时间、吨位、长度排序
                                                        close_matches.sort(
                                                            key=lambda x: (
                                                                x["updatetime"] or datetime.min,
                                                                x["dwt"],
                                                                x["length"]
                                                            ),
                                                            reverse=True
                                                        )
                                                        best = close_matches[0]
                                                    else:
                                                        candidates.sort(
                                                            key=lambda x: (
                                                                x["dwt"] > 2000,
                                                                x["updatetime"] or datetime.min,
                                                                x["dwt"],
                                                                x["length"]
                                                            ),
                                                            reverse=True
                                                        )
                                                        best = candidates[0]
                                                else:
                                                    candidates.sort(
                                                        key=lambda x: (
                                                            x["dwt"] > 2000,
                                                            x["updatetime"] or datetime.min,
                                                            x["dwt"],
                                                            x["length"]
                                                        ),
                                                        reverse=True
                                                    )
                                                    best = candidates[0]

                                                imo = best["imo"]
                                                mmsi = best["mmsi"]

                                    except Exception as e:
                                        print(f"获取IMO失败: {e}")

                                port_region = None
                                port_region_cn = None
                                port_id = None

                                port_shiptype = None
                                try:
                                    shiptype_result = call_deepseek_shiptype(shiptype)
                                    if shiptype_result and "shiptype" in shiptype_result:
                                        port_shiptype = shiptype_result.get('shiptype')
                                except Exception as e:
                                    logger.error(f"获取船型失败: {e}")
                                    logger.error(traceback.format_exc())

                                try:
                                    port_result = call_deepseek_region(port)
                                    logger.info(f"port_result:{port_result}")
                                    if port_result and "region_name" in port_result:
                                        port_region = port_result.get('region_name')
                                        port_region_cn = port_result.get('region_cn_name')
                                        if port_result.get('portcode') and len(port_result.get('portcode')) == 5:
                                            portcode = port_result.get('portcode')
                                except Exception as e:
                                    logger.error(f"获取港口区域失败: {e}")
                                    logger.error(traceback.format_exc())

                                if port:
                                    try:
                                        port_id = get_portid(portcode, port)
                                    except Exception as e:
                                        logger.error(f"获取港口ID失败: {e}")
                                        logger.error(traceback.format_exc())

                                # 数据整合
                                try:
                                    row = {
                                        "email_users": email_user,
                                        "vessel_name": clean_name,
                                        "imo": imo,
                                        "vessel_type": port_shiptype,
                                        "dwt": vessel.get("载重吨"),
                                        "built_year": vessel.get("建造年份"),
                                        "open_port": port,
                                        "open_date": vessel.get("OPEN开始日期"),
                                        "open_end_date": vessel.get("OPEN结束日期"),
                                        "oa": vessel.get("O/A其他附加信息"),
                                        "trading_area": vessel.get("航线意向"),
                                        "crane_count": vessel.get("吊机数量"),
                                        "is_geared": vessel.get("是否有船吊"),
                                        "crane_type": vessel.get("吊机类型"),
                                        "hatch_size": vessel.get("舱口尺寸"),
                                        "hold_capacity_cbm": vessel.get("舱容（立方米）"),
                                        "holds_count": vessel.get("舱数"),
                                        "hatch_cover_type": vessel.get("舱盖类型"),
                                        "deck_strength": vessel.get("甲板载重能力"),
                                        "dg_approved": vessel.get("是否可装危险品"),
                                        "reefer_plugs": vessel.get("冷藏插座数量"),
                                        "sprinkler_system": vessel.get("是否有喷淋系统"),
                                        "fuel_type": vessel.get("燃料类型"),
                                        "vessel_owner": vessel.get("所属公司"),
                                        "imo_equipment_class": vessel.get("IMO设备等级"),
                                        "speed_knots": vessel.get("船速（节）"),
                                        "cargo_equipment": vessel.get("载货设备描述"),
                                        "email_body": email_data["body"],
                                        "port_region": port_region,
                                        "port_region_cn": port_region_cn,
                                        "open_type": vessel.get("租船类型"),
                                        "vessel_age": age,
                                        "portid": port_id,
                                        "mmsi": mmsi,
                                        "is_cis":vessel.get("是否可跑CIS航线"),
                                        "is_bh":vessel.get("是否可跑BH航线"),
                                        "is_aus":vessel.get("是否可跑AUS航线"),
                                        "is_boxhold":vessel.get("是否是BOX HOLD"),
                                        "is_no_iran":vessel.get("是否是NO IRAN/ISRAEL/YEMEN")
                                    }

                                    tags_year = generate_vessel_tags(row)
                                    tags = tags_year.get('tags')
                                    year_ship_data = tags_year.get('YearOfBuild')
                                    dwt_ship_data = tags_year.get('dwt')
                                    year_value = year or year_ship_data
                                    dwt_value = dwt or dwt_ship_data
                                    shiptype = tags_year.get("shiptype")
                                    minotype = tags_year.get("minotype")

                                    try:
                                        age = datetime.now().year - int(year_value) if year_value else None
                                    except ValueError:
                                        age = None

                                    if imo and dwt:
                                        try:
                                            dwt_val = float(dwt)
                                            dwt_ship_val = float(dwt_ship_data)
                                            if abs(dwt_val - dwt_ship_val) > dwt_val * 0.1:
                                                imo = None
                                        except (ValueError, TypeError):
                                            imo = None

                                    try:
                                        dwt_int = int(dwt_value) if dwt_value not in (None, "") else None
                                    except:
                                        dwt_int = None

                                    dwt_type = classify_vessel_type(shiptype, minotype, port_shiptype, dwt_int)


                                except Exception as e:
                                    logger.error(f"生成标签或行数据失败: {e}")
                                    logger.error(traceback.format_exc())

                                # 插入数据库
                                try:
                                    filepath = r"E:\xwc\vessel_sales_purchase\imo_email.xlsx"
                                    owner_email = load_imo_email_records_from_xlsx(filepath)
                                    is_owner = is_same_company(email_data["from_email"], imo, owner_email)

                                    insert_values = (
                                        email_user, user_id, clean_name, imo, port_shiptype,
                                        vessel.get("载重吨"), vessel.get("建造年份"), port,
                                        sanitize_date(vessel.get("OPEN开始日期")),
                                        sanitize_date(vessel.get("OPEN结束日期")),
                                        vessel.get("O/A其他附加信息"),
                                        convert_date(email_data["date"]),
                                        clean_sender_name(email_data.get("from_name", "")), email_data["from_email"],
                                        vessel.get("航线意向"), vessel.get("吊机数量"), vessel.get("是否有船吊"),
                                        vessel.get("吊机类型"), vessel.get("舱口尺寸"), vessel.get("舱容（立方米）"),
                                        vessel.get("舱数"), vessel.get("舱盖类型"), vessel.get("甲板载重能力"),
                                        vessel.get("是否可装危险品"), vessel.get("冷藏插座数量"),
                                        vessel.get("是否有喷淋系统"),
                                        vessel.get("燃料类型"), vessel.get("所属公司"), vessel.get("IMO设备等级"),
                                        vessel.get("船速（节）"), vessel.get("载货设备描述"), email_data["body"],
                                        port_region,
                                        port_region_cn, vessel.get("租船类型"), age,
                                        is_owner, port_id, mmsi, tags, dwt_type
                                    )

                                    insert_open_sql = """
                                        INSERT INTO charter_open_vessels (
                                            email_users, user_id, vessel_name, imo, vessel_type, dwt, built_year, open_port, 
                                            open_date, open_end_date, oa, received_time, sender_name, sender_email, created_date, trading_area,
                                            crane_count, is_geared, crane_type, hatch_size, hold_capacity_cbm, holds_count,
                                            hatch_cover_type, deck_strength, dg_approved, reefer_plugs, sprinkler_system,
                                            fuel_type, vessel_owner, imo_equipment_class, speed_knots, cargo_equipment, email_body,
                                            is_duplicate, is_public, port_region, port_region_cn, open_type, vessel_age, is_owner, portid, mmsi, tags, dwt_type
                                        ) VALUES (
                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), %s,
                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 0, %s, %s, %s, %s, %s, %s, %s, %s,%s
                                        )
                                    """
                                    cursor.execute(insert_open_sql, insert_values)
                                    vessel_id = cursor.lastrowid
                                except Exception as e:
                                    logger.error(f"插入数据库失败: {e}")
                                    logger.error(traceback.format_exc())

                            except Exception as e:
                                logger.error(f"处理单条船盘数据时出错: {e}")
                                logger.error(traceback.format_exc())

                except Exception as e:
                    logger.error(f"主循环执行失败: {e}")
                    logger.error(traceback.format_exc())

                    # 3. 获取在匹配区间内的货盘记录
                        # sql_cargo = f"""
                        #                 SELECT * FROM charter_cargo
                        #                 WHERE (
                        #                             email_users = '{email_user}' AND
                        #                             received_time BETWEEN '{match_start_time_str}' AND '{end_time_str}'
                        #                             AND is_duplicate = 0
                        #                         )
                        #                         OR (
                        #                             is_public = 1 AND
                        #                             is_duplicate = 0 AND
                        #                             received_time BETWEEN '{match_start_time_str}' AND '{end_time_str}'
                        #                         )
                        #             """
                        # cursor.execute(sql_cargo)
                        # cargos = cursor.fetchall()
                        #
                        # for cargo in cargos:
                        #     # 港口匹配
                        #     if not fuzzy_port_match(cargo['load_port'], vessel.get("OPEN位置"), cargo["load_port_region"], port_region):
                        #         continue
                        #
                        #     # 日期匹配
                        #     if not check_date_overlap(vessel.get("OPEN开始日期"),vessel.get("OPEN结束日期"), cargo['laycan_start'], cargo['laycan_end']):
                        #         continue
                        #
                        #     # 船型匹配
                        #     if cargo['allowed_vessel_types'] and vessel.get("船型"):
                        #         cargo_type = cargo['allowed_vessel_types'].replace(" ", "").lower()
                        #         vessel_type = vessel.get("船型").replace(" ", "").lower()
                        #         if cargo_type != vessel_type:
                        #             continue
                        #
                        #     # 船龄匹配
                        #     if cargo['max_age_limit'] and vessel.get("建造年份"):
                        #         try:
                        #             if int(vessel.get("建造年份")) < int(cargo['max_age_limit']):
                        #                 continue
                        #         except:
                        #             continue
                        #
                        #     # 载重吨匹配
                        #     if cargo['requires_dwt'] and vessel.get("载重吨") is not None:
                        #         min_dwt, max_dwt = parse_dwt_range(cargo['requires_dwt'])
                        #         try:
                        #             vessel_dwt = float(vessel.get("载重吨"))
                        #         except:
                        #             continue
                        #         if min_dwt is None or max_dwt is None or not (min_dwt <= vessel_dwt <= max_dwt):
                        #             continue
                        #
                        #     # 船吊匹配
                        #     if cargo['requires_geared'] is not None and vessel.get("是否有船吊") is not None:
                        #         if int(cargo['requires_geared']) == 1 and int(vessel.get("是否有船吊")) != 1:
                        #             continue
                        #
                        #     # 危险品匹配
                        #     if cargo['is_dg_cargo'] is not None and vessel.get("是否可装危险品") is not None:
                        #         if int(cargo['is_dg_cargo']) == 1 and int(vessel.get("是否可装危险品")) != 1:
                        #             continue
                        #
                        #     # 冷藏匹配
                        #     if cargo['reefer_required'] is not None and vessel.get("冷藏插座数量") is not None:
                        #         if int(cargo['reefer_required']) == 1:
                        #             try:
                        #                 if float(vessel.get("冷藏插座数量")) <= 0:
                        #                     continue
                        #             except:
                        #                 continue
                        #
                        #     insert_cargo = """
                        #     INSERT IGNORE INTO charter_match_result (vessel_id, cargo_id, matched_at, user_id,email_user)
                        #     VALUES (%s, %s, NOW(), %s, %s)
                        #     """
                        #     cursor.execute(insert_cargo, (vessel_id, cargo['id'], user_id,email_user))



                # 插入 cargo 数据
                if "cargo" in intent_list and "cargo" in charter_data:
                    for cargo in charter_data["cargo"]:
                        cargo = sanitize_vessel(cargo)
                        port = cargo.get("装货港")
                        port_region = None
                        port_region_cn = None
                        portcode = port
                        port_result = call_deepseek_region(port)

                        port_id = None
                        if port_result and "region_name" in port_result:
                            port_region = port_result.get('region_name')
                            port_region_cn = port_result.get('region_cn_name')
                            if port_result.get('portcode') and len(port_result.get('portcode')) == 5:
                                portcode = port_result.get('portcode')
                            else:
                                portcode = port
                        if port:
                            port_id = get_portid(portcode, port)
                        row = {
                            "email_users": email_user,
                            "user_id": user_id,
                            "acct_name": cargo.get("客户名称"),
                            "cargo_quantity": cargo.get("货物数量"),
                            "cargo_type": cargo.get("货物种类"),
                            "load_port": clean_port(cargo.get("装货港")),
                            "discharge_port": clean_port(cargo.get("卸货港")),
                            "laycan_start": cargo.get("装港消约期开始日期"),
                            "laycan_end": cargo.get("装港消约期结束日期"),
                            "sender_email": email_data["from_email"],
                            "is_bulk": cargo.get("是否为散装"),
                            "loading_rate": cargo.get("装货率"),
                            "loading_terms": cargo.get("装货条款"),
                            "allowed_vessel_types": cargo.get("允许船型"),
                            "max_age_limit": cargo.get("最早船舶建造年份限制"),
                            "class_restriction": cargo.get("船级限制"),
                            "requires_geared": cargo.get("是否要求船吊"),
                            "is_dg_cargo": cargo.get("是否为危险品"),
                            "reefer_required": cargo.get("冷藏需求"),
                            "hold_type": cargo.get("舱型要求"),
                            "deck_cargo_allowed": cargo.get("是否接收甲板货"),
                            "packaging": cargo.get("包装要求"),
                            "cargo_note": cargo.get("货物特殊说明"),
                            "charterer_note": cargo.get("货主要求"),
                            "email_body": email_data["body"],
                            "requires_dwt": cargo.get("dwt要求"),
                            "load_port_region": port_region,
                            "load_port_region_cn": port_region_cn
                        }
                        tags = generate_cargo_tags(row)
                        insert_values = (
                            email_user, user_id,
                            cargo.get("客户名称"), cargo.get("货物数量"),
                            cargo.get("货物种类"), clean_port(cargo.get("装货港")), clean_port(cargo.get("卸货港")),
                            cargo.get("装港消约期开始日期"), cargo.get("装港消约期结束日期"),
                            convert_date(email_data["date"]), clean_sender_name(email_data.get("from_name", "")), email_data["from_email"],
                            cargo.get("是否为散装"), cargo.get("装货率"), cargo.get("装货条款"),
                            cargo.get("允许船型"), cargo.get("最早船舶建造年份限制"), cargo.get("船级限制"),
                            cargo.get("是否要求船吊"), cargo.get("是否为危险品"), cargo.get("冷藏需求"),
                            cargo.get("舱型要求"), cargo.get("是否接收甲板货"),
                            cargo.get("包装要求"), cargo.get("货物特殊说明"), cargo.get("货主要求"),
                            email_data["body"], cargo.get("dwt要求"),port_region, port_region_cn,tags,port_id
                        )

                        # 用于查重的字段（30个）
                        # duplicate_check_values = (
                        #     email_user, user_id,
                        #     cargo.get("客户名称"), cargo.get("货物名称"), cargo.get("货物数量"),clean_port(cargo.get("装货港")), clean_port(cargo.get("卸货港")),
                        #     cargo.get("装港消约期开始日期"), cargo.get("装港消约期结束日期"),
                        #     clean_sender_name(email_data.get("from_name", "")), email_data["from_email"],
                        #     email_data["body"]
                        # )
                        #
                        # # 1. 更新已有相同记录为 is_duplicate = 1
                        # update_duplicate_sql = """
                        #     UPDATE charter_cargo SET is_duplicate = 1 WHERE
                        #     email_users = %s AND user_id = %s AND acct_name = %s AND cargo_name = %s AND
                        #     cargo_quantity = %s AND load_port = %s AND discharge_port = %s AND
                        #     laycan_start = %s AND laycan_end = %s AND sender_name = %s AND sender_email = %s AND email_body = %s
                        # """
                        # cursor.execute(update_duplicate_sql, duplicate_check_values)

                        # 2. 插入新数据，标记为最新数据 is_duplicate = 0
                        insert_cargo_sql = """
                            INSERT INTO charter_cargo (
                                email_users, user_id, acct_name, cargo_quantity, cargo_type,
                                load_port, discharge_port, laycan_start, laycan_end, received_time,
                                sender_name, sender_email, created_date, is_bulk, loading_rate,
                                loading_terms, allowed_vessel_types, max_age_limit, class_restriction,
                                requires_geared, is_dg_cargo, reefer_required, hold_type,
                                deck_cargo_allowed, packaging, cargo_note, charterer_note, email_body,
                                requires_dwt, is_duplicate, is_public,load_port_region, load_port_region_cn,tags,portid
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, CURDATE(), %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, 0, 0,%s,%s,%s,%s
                            )
                        """
                        cursor.execute(insert_cargo_sql, insert_values)

                        cargo_id = cursor.lastrowid

                        # sql_vessels = f"""
                        #                 SELECT * FROM charter_open_vessels
                        #                 WHERE (
                        #                             email_users = '{email_user}' AND
                        #                             received_time BETWEEN '{match_start_time_str}' AND '{end_time_str}'
                        #                             AND is_duplicate = 0
                        #                         )
                        #                         OR (
                        #                             is_public = 1 AND
                        #                             is_duplicate = 0 AND
                        #                             received_time BETWEEN '{match_start_time_str}' AND '{end_time_str}'
                        #                         )
                        #             """
                        # cursor.execute(sql_vessels)
                        # vessels = cursor.fetchall()
                        #
                        # # 6. 遍历船盘数据，使用匹配算法进行筛选
                        # for vessel in vessels:
                        #     # 条件 1：港口匹配（货盘的装货港与船盘的 OPEN位置 对比）
                        #     if not fuzzy_port_match(cargo.get("装货港"), vessel['open_port'],port_region,vessel['port_region']):
                        #         continue
                        #
                        #     # 条件 2：日期匹配（船盘OPEN日期须在货盘的装港消约期范围内）
                        #     if not check_date_overlap(vessel['open_date'], vessel['open_end_date'], cargo.get("装港消约期开始日期"), cargo.get("装港消约期结束日期")):
                        #         continue
                        #
                        #     # 条件 3：船型匹配（若货盘指定了允许船型，则船盘的船型必须匹配）
                        #     if cargo.get("允许船型") and vessel['vessel_type']:
                        #         cargo_type = cargo.get("允许船型").replace(" ", "").lower()
                        #         vessel_type = vessel['vessel_type'].replace(" ", "").lower()
                        #         if cargo_type != vessel_type:
                        #             continue
                        #
                        #     # 条件 4：船龄匹配（若货盘提供建造年份限制，则船盘建造年份不能低于该限制）
                        #     if cargo.get("最早船舶建造年份限制") and vessel['built_year']:
                        #         try:
                        #             if int(vessel['built_year']) < int(cargo.get("最早船舶建造年份限制")):
                        #                 continue
                        #         except Exception as e:
                        #             continue
                        #
                        #     # 条件 5：载重吨匹配（若货盘对载重吨有要求，则船盘dwt需要在要求范围内）
                        #     if cargo.get("dwt要求") and vessel['dwt'] is not None:
                        #         min_dwt, max_dwt = parse_dwt_range(cargo.get("dwt要求"))
                        #         try:
                        #             vessel_dwt = float(vessel['dwt'])
                        #         except Exception as e:
                        #             continue
                        #         if min_dwt is None or max_dwt is None or not (min_dwt <= vessel_dwt <= max_dwt):
                        #             continue
                        #
                        #     # 条件 6：船吊匹配（若货盘要求船吊，则船盘必须有船吊，假设 1 表示 yes）
                        #     if cargo.get("是否要求船吊") is not None and vessel['is_geared'] is not None:
                        #         if int(cargo.get("是否要求船吊")) == 1 and int(vessel['is_geared']) != 1:
                        #             continue
                        #
                        #     # 条件 7：危险品匹配（若货盘为危险品，则船盘必须可装危险品，1 表示 yes）
                        #     if cargo.get("是否为危险品") is not None and vessel['dg_approved'] is not None:
                        #         if int(cargo.get("是否为危险品")) == 1 and int(vessel['dg_approved']) != 1:
                        #             continue
                        #
                        #     # 条件 8：冷藏需求匹配（若货盘要求冷藏，则船盘的冷藏插座数量必须大于 0）
                        #     if cargo.get("冷藏需求") is not None and vessel.get('reefer_plugs') is not None:
                        #         if int(cargo.get("冷藏需求")) == 1:
                        #             try:
                        #                 if float(vessel['reefer_plugs']) <= 0:
                        #                     continue
                        #             except Exception as e:
                        #                 continue
                        #
                        #     insert_cargo = """
                        #                                 INSERT IGNORE INTO charter_match_result (vessel_id, cargo_id, matched_at, user_id,email_user)
                        #                                 VALUES (%s, %s, NOW(), %s, %s)
                        #                                 """
                        #     cursor.execute(insert_cargo, (vessel['id'], cargo_id, user_id,email_user))



            except Exception as e:
                logging.error(f"解析或存储失败: {email_data['from_email']} | {email_data['date']} | 错误: {str(e)}")

                logger.error(traceback.format_exc())
                continue

    except Exception as e:
        logging.error(f"整体处理失败: {str(e)}")

def mark_duplicates(cursor):
    update_sql = """
        UPDATE charter_open_vessels
        SET is_duplicate = 1
        WHERE id NOT IN (
            SELECT t.max_id
            FROM (
                SELECT MAX(id) AS max_id
                FROM charter_open_vessels
                WHERE is_duplicate = 0
                GROUP BY email_users, user_id, vessel_name, open_port, sender_name, sender_email
            ) AS t
        )
        AND is_duplicate = 0
    """
    cursor.execute(update_sql)
    update_cargo_sql = """
        UPDATE charter_cargo
        SET is_duplicate = 1
        WHERE id NOT IN (
            SELECT t.max_id
            FROM (
                SELECT MAX(id) AS max_id
                FROM charter_cargo
                WHERE is_duplicate = 0
                GROUP BY 
                            email_users,user_id, acct_name, cargo_name ,
                            cargo_quantity, load_port, discharge_port ,
                            laycan_start , laycan_end, sender_name, sender_email
            ) AS t
        )
        AND is_duplicate = 0
    """
    cursor.execute(update_cargo_sql)


def get_user_config():
    """获取所有活跃用户的配置信息"""
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT email_user, server_address, server_port, email_password,user_id, last_parse_time, expiration_time 
        FROM charter_user_service_configuration 
        WHERE is_active = 1 AND (expiration_time IS NULL OR expiration_time > %s)
    """, (datetime.now(),))
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

def job(user_config):
    """执行解析邮件任务"""
    email_user = user_config["email_user"]
    email_password = user_config["email_password"]
    server_address = user_config["server_address"]
    server_port = user_config["server_port"]
    user_id = user_config["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        last_parse_time = get_last_parse_time(email_user, cursor)
        if last_parse_time is None:
            last_parse_time = datetime.now() - timedelta(days=1)

        logger.info(f"[{datetime.now()}] 执行任务: {email_user}, 上次解析时间: {last_parse_time}")

        addr = server_address.lower()
        if "imap" in addr:
            protocol = "imap"
        elif "pop" in addr:
            protocol = "pop"
        else:
            protocol = "imap"
        mail = fetch_emails(email_user, email_password, server_address, server_port, last_parse_time,protocol)
        new_last_parse_time = datetime.now()

        if mail:
            update_last_parse_time(email_user, new_last_parse_time, cursor)
            conn.commit()
            save_charter_data(email_user,user_id, mail, cursor)
            conn.commit()
            mark_duplicates(cursor)
            conn.commit()
            logger.info(f"[{datetime.now()}] {email_user} 数据已保存，新解析时间: {new_last_parse_time}")
        else:
            update_last_parse_time(email_user, new_last_parse_time, cursor)
            conn.commit()
            logger.info(f"[{datetime.now()}] {email_user} 未获取到新邮件")
    except Exception as e:
        conn.rollback()
        logger.error(f"[{datetime.now()}] {email_user} 任务执行失败: {e}", exc_info=True)
        logger.error(traceback.format_exc())
        raise
    finally:
        cursor.close()
        conn.close()


def job_wrapper(user):
    """包装 job 函数，添加超时机制"""
    future = executor.submit(job, user)
    try:
        future.result(timeout=7200)
    except concurrent.futures.TimeoutError:
        logger.error(f"[{datetime.now()}] 任务超时: {user['email_user']}")
    except Exception as e:
        logger.error(f"[{datetime.now()}] 任务执行失败 {user['email_user']}: {e}", exc_info=True)

def schedule_tasks():
    """调度任务在每小时的 00 分 和 30 分"""
    def run_all_users():
        users = get_user_config()
        logger.info(f"[{datetime.now()}] 开始执行所有用户任务，共 {len(users)} 个用户")
        for user in users:
            email_user = user.get("email_user")
            email_password = user.get("email_password")
            if not email_user or not email_password:
                logger.warning(f"跳过无效用户: {email_user}")
                continue
            try:
                executor.submit(job_wrapper, user)
            except Exception as e:
                logger.error(f"执行用户任务失败: {email_user} - {e}", exc_info=True)

    schedule.clear("all_users")

    schedule.every().hour.at(":00").do(run_all_users).tag("all_users")
    schedule.every().hour.at(":10").do(run_all_users).tag("all_users")
    schedule.every().hour.at(":20").do(run_all_users).tag("all_users")
    schedule.every().hour.at(":30").do(run_all_users).tag("all_users")
    schedule.every().hour.at(":40").do(run_all_users).tag("all_users")
    schedule.every().hour.at(":50").do(run_all_users).tag("all_users")


def run_scheduler():
    logger.info(f"[{datetime.now()}] 调度器启动")
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    try:
        logger.info("任务调度器启动中...")
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("任务调度器正在运行...")

        while True:
            time.sleep(1)
    except Exception as e:
        logger.error(f"任务调度发生错误: {e}", exc_info=True)

if __name__ == "__main__":
    main()