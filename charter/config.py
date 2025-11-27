
DATABASE_CONFIG = {
    'host':'rdsrieyar2qii22298.mysql.rds.aliyuncs.com',
    'user':'weather_routing',
    'password':'us!sT7@@M0kdL1iS',
    'database':'vessel_sales_purchase',
    'port': 3306
}

EMAIL_CONFIG = {
    'smtp_server': 'smtp.qiye.aliyun.com',
    'smtp_port': 587,
    'smtp_user': 'ai@hifleet.com',
    'smtp_password': 'bUOFWik02SKmmSX9'
}

CC_EMAIL = 'xuwanchu@hifleet.com'
# 本地测试发件邮箱
# EMAIL_CONFIG = {
#     'smtp_server': 'smtp.163.com',
#     'smtp_port': 465,
#     'smtp_user': 'xwc991230@163.com',
#     'smtp_password': 'YZdK2DZQFHg8WDXF'
# }
# EMAIL_CONFIG = {
#     'smtp_server': 'smtp.qq.com',
#     'smtp_port': 587,
#     'smtp_user': '3466762863@qq.com',
#     'smtp_password': 'hwugckmdvsrpdbie'
# }
# DATABASE_CONFIG = {
#     'host':'localhost',
#     'user':'root',
#     'password':'123456',
#     'database':'vessel_sales_purchase',
#     'port': 3306
# }
# """OPEN位置、装货港、卸货港请严格按照以下规则提取和格式化地理位置信息： 按顺序判断：如果是具体港口 → 返回UN/LOCODE 5位代码（格式：CNPEK），如果是国家名称 → 返回ISO 3166-1 Alpha-2代码（格式：CN），如果是区域/非标准名称 → 直接返回原文
# 其中：港口特征包含"港"、"port"或有明确港口名（如上海、Singapore），国家特征：主权国家名称（中国、USA等），区域特征：地理区域（华北、N.CHINA、East Coast等）、城市名或无法归类的内容"""
sp_log_dir = r"E:\xwc\vessel_sales_purchase\vessel_sp_logs"
charter_log_dir = r"E:\xwc\vessel_sales_purchase\vessel_charter_logs"
sp_bill_log_dir = r"E:\xwc\vessel_sales_purchase\sp_billing_logs"
charter_bill_log_dir =  r"E:\xwc\vessel_sales_purchase\charter_billing_logs"

system_text = """请分析以下邮件内容，判断是否为租船邮件（比如包含OPEN、CHARTER等等专业词），邮件分为三种：cargo:租船货盘邮件，openvessels：租船船盘邮件，unknown：卖船买船意图和其他意图。如果邮件提到的是buy/sell/SP，表示的是unknown意图，如果文本中同时提到了船盘和货盘，请分别进行提取，并按照船盘/货盘按顺序提取以下字段：
- 船盘需要提取：船名, IMO, 船型, 载重吨, 建造年份, OPEN位置, OPEN开始日期,open结束日期, O/A其他附加信息, 航线意向, 吊机数量，是否有船吊，吊机类型，舱口尺寸，舱容（立方米），舱数，舱盖类型，甲板载重能力，是否可装危险品，冷藏插座数量，是否有喷淋系统，燃料类型，所属公司，IMO设备等级，船速（节），载货设备描述；
- 货盘需要提取：客户名称, 货物名称, 货物数量, 货物种类, 装货港, 卸货港, 装港消约期开始日期, 装港消约期结束日期, 是否为散装，装货率，装货条款，允许船型，最大船龄限制，船级限制，是否要求船吊，是否为危险品，冷藏需求，舱型要求，舱盖要求，是否接收甲板货，包装要求，货物特殊说明，货主要求。

**返回 JSON 结构必须严格遵循标准格式，确保如下格式：**
{
  "intent": ["cargo", "openvessels"],  # 可能的值为 ["cargo"], ["openvessels"], ["unknown"], ["cargo", "openvessels"]
  "data": {
    "cargo": [
      {
        "客户名称": "...",
        "货物数量": ...,# int类型
        "货物种类": "...",
        "装货港": "...",# 保留原文位置
        "卸货港": "...",# 保留原文位置
        "装港消约期开始日期": "...",# date类型,注意今年是2025年
        "装港消约期结束日期": "...",# date类型,注意今年是2025年
        "是否为散装": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空
        "装货率": "...",
        "装货条款": "...",
        "允许船型": "...",
        "最早船舶建造年份限制": "...",# 只保留年份，4位数字的字符串,如果邮件中说明的是船龄没有说明建造年份，那么你需要推算下最早的建造年份，也就是距离今年前多少年建造的
        "船级限制": "...",
        "是否要求船吊": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空
        "是否为危险品": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空
        "冷藏需求": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空
        "舱型要求": "...",
        "是否接收甲板货": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空
        "包装要求": "...",
        "货物特殊说明": "...",
        "货主要求": "...",
        "dwt要求":"...",#为范围，‘int类型-int类型’格式
      }
    ],
    "openvessels": [# 若同一条船的航线意向有多条，请分开存储到字典中
      {
        "船名": "...", # 不要保留MV两个字符，只提取具体的船舶名称，不要包含"NASCO-1"等编号前缀，不要包含"OR SUB"、"TBN OR SUB"等备选说明，对于TBN（待定船名）的情况，如实提取为"TBN"
        "IMO": "...",
        "船型": "...",# 如果文中没有提到船型，请结合邮件中的载重吨、船长船宽数据推测下是什么船，最好不为空
        "载重吨": ...,# int类型
        "建造年份": "...",# 只保留年份，4位数字的字符串
        "OPEN位置": "...",# 保留原文位置
        "OPEN开始日期": "...", # date类型,注意今年是2025年，如果文中只给了一个日期，那么这个日期为open日期,open结束日期为空，如果给了一个范围如，7月5-10日，那开始日期为5号
        "OPEN结束日期": "...", # date类型,注意今年是2025年，如果文中只给了一个日期，那么这个日期为open日期,open结束日期为空，如果给了一个范围如，7月5-10日，那结束日期为10号
        "O/A其他附加信息": "...",
        "航线意向": "...", #提取航线的地理范围，尽量识别到初始港口和目的港口，格式为始发港-目的港
        "吊机数量":  ...,# int类型
        "是否有船吊": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空
        "吊机类型": "...",
        "舱口尺寸": "...",
        "舱容（立方米）":  ...,# int类型
        "舱数":  ...,# int类型
        "舱盖类型": "...",
        "甲板载重能力": "...",
        "是否可装危险品": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空
        "冷藏插座数量":  ...,# int类型
        "是否有喷淋系统": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空
        "燃料类型": "...",
        "所属公司": "...",
        "IMO设备等级": "...",
        "船速（节）":  ...,# float类型
        "载货设备描述": "...",
        "租船类型":"..." # 值为spot,TCT、LINER或者period四者其一,spot表示单航次租赁，TCT为定期航次租船，LINER班轮运输/订舱，period表示定期租赁，如果没有提到就为空,
        "是否可跑CIS航线": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空,
        "是否可跑BH航线": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空,
        "是否可跑AUS航线": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空,
        "是否是BOX HOLD": ...,# int类型,值为0或1，0表示否，1表示是,未提及为空，
        “是否是NO IRAN/ISRAEL/YEMEN": ..., #禁止往来或靠港于伊朗（Iran）或者以色列（Israel）或者也门（Yemen），int类型,值为0或1，0表示否，1表示是,未提及为空
      }
    ]
  }
}

注意：
1. `intent` 必须是数组，且只包含 "cargo", "openvessels", "unknown" 之一或组合，除了船盘和货盘，其他意图都为unknown，邮件中提到的SP表示的是买卖船，意图为买卖船属于unknown，“FLWG LADIES HAS BEEN FIXED”指的是船盘，这可能是二船东发出的找货的邮件。
2. `data` 必须是一个字典，即使只有 cargo 或 openvessels，也必须返回 {"cargo": [{....}], "open vessels": []}或者{"cargo": [], "openvessels": [{....}]}，不能直接返回数据块, JSON 中的 cargo 和 open vessels 必须是数组，每个元素都是一个字典。
3. 只提取指定字段，不要额外添加字段。
4. 时间格式严格为 `yyyy-MM-dd HH:mm:ss`。
5. 邮件中未提到该字段，则字段值设为空: None
6. 如果邮件中说明的是船龄没有说明建造年份，那么你需要推算下建造年份，也就是距离今年前多少年建造的，
7. 邮件中如果提到了多条船舶的租船需求，需要全部识别下来，都保存到json数据的data中
8. 即使邮件中只有一条船盘或货盘的信息，也必须将信息放在一个字典内，并将该字典放入相应的数组中。
9. 若船盘中同一条船的航线意向有多条，请分开存储到多个字典中。
10. 若提到的open日期或者装港消约期开始日期是today，请保留当前北京日期，格式为yyyy-MM-dd，如果日期为end，代表该月的30号，mid表示15号
11. 注意货盘的载重吨要求的可能是个范围, 在分析邮件内容时，如果载重吨、TEU或年份只提到一个数字，且表述为“A左右”、“超过A”或“不超过A”，请根据以下规则处理：

载重吨和TEU：
- A左右：上下各加减25%。例如，如果A是100000，则范围是“75000-125000”。
- 超过A：上限加50%。例如，如果A是100000，则范围是“100000-150000”。
- 不超过A：下限减50%。例如，如果A是100000，则范围是“50000-100000”。
"""
user_text = """邮件内容：{content}"""
shiptype_system = """你是一个船舶类型分类助手。

任务：我会给你船舶类型名称，请你根据以下船型列表，判断这个船舶类型属于哪个船型，并返回该船型。

区域列表：
{散货船、集装箱船、石油化学品船、近海供应船、杂货船、拖轮、干散液散兼用船、工程及服务船、近海作业船、渔船、油船、客船、滚装船、游艇、气槽船、专用船、拖带船、未知类型液货船、其他类型液货船、其他类型干货船、未知类型干货船}，返回该船型（只能返回最符合的一个）

输入船舶类型：{{船舶类型}}

**返回 JSON 结构必须严格遵循标准格式，确保如下格式：**
{
    shiptype：船舶类型
}
"""
region_system = """你是一个全球港口区域分类助手。

任务：我会给你港口或者位置名称，请你根据以下区域列表，判断这个港口属于哪个区域，并返回该区域的中文名和英文名，以及该港口的UN/LOCODE 5位代码。

区域列表：
South Pacific,南太平洋
North Pacific,北太平洋
South Atlantic,南大西洋
India East Coast,印度东海岸
Far East,远东
North China,北中国
South China,南中国
Bay of Bengal(East),东孟加拉湾
South East Asia,东南亚
South America West Coast,南美洲西海岸
South America East Coast,南美洲东海岸
Caribbean,加勒比海
South Africa,南非
South East Africa,东南非
East Africa,东非
South America North Coast,南美洲北海岸
US West Coast,美国西海岸
West Coast Central America,中美洲西海岸
Gulf of Mexico,墨西哥湾
North Atlantic,北大西洋
East Coast Canada,加拿大东海岸
Greenland Sea,格林兰海
West Africa,西非
North West Africa,西北非
West Europe,西欧
North West Europe,西北欧
West Mediterranean,西地中海地区
Baltic,巴伦支地区
East Mediterranean,东地中海地区
Black Sea,黑海
Fertile Crescent,新沃月地
Hudson Bay,哈德森湾
Red Sea,红海
Middle East Gulf,中东湾
India West Coast,印度西海岸
Caspian Sea,里海
Indian Ocean,印度洋
West Coast Australia,澳大利亚西海岸
Russia Pacific,俄罗斯太平洋
South Coast Australia,澳大利亚南海岸
East Coast Australia,澳大利亚东海岸
US East Coast,美国东海岸
Bering Sea,白令海
Gulf of Alaska,阿拉斯加湾
New Zealand,新西兰

输入港口：{{港口}}

**返回 JSON 结构必须严格遵循标准格式，确保如下格式：**
{
    region_name：XXXX英文名，
    region_cn_name：XXXX中文名，
    portcode：该港口的UN/LOCODE 5位代码
}
"""

sp_system_text = """请分析以下邮件内容，判断是否为buy：买船，sell：卖船意图，unknown：其他意图。如果文本中同时提到了买船和卖船，请分别进行提取，并按照买船/卖船按顺序提取以下字段：
- 买船需要提取：船舶类型, 建造国, 建造年份（只保留年份）, 船长, 载重吨, TEU, 发动机, 交付条件；
- 卖船需要提取：船名, IMO, 船旗, 船舶类型, 建造国, 建造年份（只保留年份）, 船长, 总吨, 净吨, 载重吨, TEU, 发动机, 交付条件。

**返回 JSON 结构必须严格遵循标准格式，确保如下格式：**
{
  "intent": ["buy", "sell"],  # 可能的值为 ["buy"], ["sell"], ["unknown"], ["buy", "sell"]
  "data": {
    "buy": [
      {
        "船舶类型": "...",# 返回AIS Ship Type Codes格式
        "建造国": "...",# 返回ISO 3166-1 alpha-3国家码
        "建造年份": "...",
        "船长": "...",
        "载重吨": "...",
        "TEU": "...",
        "发动机": "...",
        "交付条件": "..."
      }
    ],
    "sell": [
      {
        "船名": "...",
        "IMO": "...",
        "船旗": "...",
        "船舶类型": "...",# 返回AIS Ship Type Codes格式
        "建造国": "...",# 返回ISO 3166-1 alpha-3国家码
        "建造年份": "...",
        "船长": "...",
        "总吨": "...",
        "净吨": "...",
        "载重吨": "...",
        "TEU": "...",
        "发动机": "...",
        "交付条件": "..."
      }
    ]
  }
}

注意：
1. `intent` 必须是数组，且只包含 "buy", "sell", "unknown" 之一或组合。
2. `data` 必须是一个字典，即使只有 buy 或 sell，也必须返回 {"buy": [{....}], "sell": []}或者{"buy": [], "sell": [{....}]}，不能直接返回数据块, JSON 中的 sell 和 buy 必须是数组，每个元素都是一个字典。
3. 只提取指定字段，不要额外添加字段。
4. 时间格式严格为 `yyyy-MM-dd HH:mm:ss`。
5. 邮件中未提到该字段，则字段值设为空: None
6. "船长", "总吨", "净吨", "载重吨", "TEU"保留float型数字,其余字段为string
7. 输出为英文，其他语言全部翻译为英文.
8. 注意买船的建造年份/建造国/载重吨要求的可能是个范围, 在分析邮件内容时，如果载重吨、TEU或年份只提到一个数字，且表述为“A左右”、“超过A”或“不超过A”，请根据以下规则处理：

载重吨和TEU：
- A左右：上下各加减25%。例如，如果A是100000，则范围是“75000-125000”。
- 超过A：上限加50%。例如，如果A是100000，则范围是“100000-150000”。
- 不超过A：下限减50%。例如，如果A是100000，则范围是“50000-100000”。

建造年份：
- A左右：上下各加减2年。例如，如果A是2005年，则范围是“2003-2007”。
- 超过A：上限为A到当前年份。例如，如果A是2005年且当前年份为2025年，则范围是“2005-2025”。
- 不超过A：下限为1990年到A年。例如，如果A是2005年，则范围是“1990-2005”。建造国用逗号分隔开
9. 如果邮件中说明的是船龄没有说明建造年份，那么你需要推算下建造年份，也就是距离今年前多少年建造的，
10. 邮件中如果提到了多条船舶的买卖需求，需要全部识别下来，都保存到json数据的data中
11. 即使邮件中只有一条买船或卖船的信息，也必须将信息放在一个字典内，并将该字典放入相应的数组中。
"""
sp_user_text = """邮件内容：{content}"""