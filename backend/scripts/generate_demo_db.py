"""
中文电商售后 Agent — SQLite 演示数据库生成脚本

用法:
    cd backend
    python scripts/generate_demo_db.py

输出:
    backend/app/data/demo_ecommerce.sqlite

固定随机种子: 20260514，可重复生成完全相同的数据库。
"""

import random
import sqlite3
import textwrap
from datetime import datetime, timedelta
from pathlib import Path

SEED = 20260514
DB_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "demo_ecommerce.sqlite"
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "schema.sql"

random.seed(SEED)

# ================================================================
# Chinese locale data
# ================================================================
SURNAMES = [
    "王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
    "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
    "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
    "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
    "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎",
    "余", "潘", "杜", "戴", "夏", "钟", "汪", "田", "任", "姜",
    "范", "方", "石", "姚", "谭", "廖", "邹", "熊", "金", "陆",
    "郝", "孔", "白", "崔", "康", "毛", "邱", "秦", "江", "史",
    "顾", "侯", "邵", "孟", "龙", "万", "段", "雷", "钱", "汤",
]

GIVEN_CHARS_M = [
    "伟", "强", "磊", "军", "勇", "杰", "涛", "明", "辉", "鹏",
    "斌", "峰", "浩", "宇", "宁", "博", "文", "刚", "华", "飞",
    "毅", "俊", "成", "超", "亮", "平", "建", "林", "志", "国",
    "子轩", "浩然", "宇轩", "梓豪", "一鸣", "天宇", "泽宇", "子涵",
]

GIVEN_CHARS_F = [
    "芳", "敏", "静", "丽", "婷", "雪", "玲", "萍", "红", "霞",
    "娟", "琴", "云", "洁", "秀", "兰", "凤", "慧", "怡", "瑶",
    "思雨", "雨涵", "梓萱", "一诺", "梦瑶", "诗涵", "欣怡", "晓萌",
]

PROVINCES_CITIES = {
    "北京": ["北京市"],
    "上海": ["上海市"],
    "广东": ["广州市", "深圳市", "东莞市", "佛山市", "珠海市"],
    "浙江": ["杭州市", "宁波市", "温州市", "嘉兴市", "金华市"],
    "江苏": ["南京市", "苏州市", "无锡市", "常州市", "南通市"],
    "四川": ["成都市", "绵阳市", "德阳市", "宜宾市", "南充市"],
    "湖北": ["武汉市", "宜昌市", "襄阳市", "荆州市", "黄石市"],
    "山东": ["济南市", "青岛市", "烟台市", "潍坊市", "临沂市"],
    "福建": ["福州市", "厦门市", "泉州市", "漳州市", "莆田市"],
    "湖南": ["长沙市", "株洲市", "湘潭市", "衡阳市", "岳阳市"],
    "河南": ["郑州市", "洛阳市", "开封市", "南阳市", "新乡市"],
    "安徽": ["合肥市", "芜湖市", "蚌埠市", "马鞍山市", "安庆市"],
    "辽宁": ["沈阳市", "大连市", "鞍山市", "抚顺市", "锦州市"],
    "陕西": ["西安市", "咸阳市", "宝鸡市", "渭南市", "延安市"],
    "重庆": ["重庆市"],
    "天津": ["天津市"],
}

# ================================================================
# Category-specific product data
# ================================================================
CATEGORY_BRANDS = {
    "服饰": ["优衣库", "ZARA", "海澜之家", "太平鸟", "UR", "森马", "波司登", "李宁"],
    "数码": ["华为", "小米", "OPPO", "vivo", "漫步者", "罗技", "安克", "倍思"],
    "家电": ["美的", "格力", "海尔", "苏泊尔", "九阳", "飞利浦", "戴森", "松下"],
    "家居": ["宜家", "网易严选", "全友", "顾家", "水星", "罗莱", "富安娜", "梦洁"],
    "美妆": ["欧莱雅", "兰蔻", "雅诗兰黛", "资生堂", "珀莱雅", "花西子", "完美日记", "薇诺娜"],
    "母婴": ["贝亲", "好孩子", "花王", "帮宝适", "惠氏", "飞鹤", "babycare", "英氏"],
    "运动": ["耐克", "阿迪达斯", "安踏", "李宁", "特步", "迪卡侬", "安德玛", "新百伦"],
    "食品": ["三只松鼠", "良品铺子", "百草味", "来伊份", "旺旺", "达利园", "徐福记", "蒙牛"],
}

CATEGORY_PRODUCT_TEMPLATES = {
    "服饰": [
        ("{brand}纯棉圆领T恤", 79, 139),
        ("{brand}轻薄防晒外套", 149, 259),
        ("{brand}弹力修身牛仔裤", 199, 399),
        ("{brand}羊毛双面呢大衣", 599, 1299),
        ("{brand}休闲运动卫衣", 169, 329),
        ("{brand}法式碎花连衣裙", 189, 359),
        ("{brand}商务免烫衬衫", 199, 369),
        ("{brand}冰丝阔腿裤", 129, 239),
        ("{brand}羽绒服中长款", 499, 999),
        ("{brand}针织开衫外套", 229, 429),
        ("{brand}高腰A字半身裙", 159, 299),
        ("{brand}速干运动短裤", 89, 169),
    ],
    "数码": [
        ("{brand}蓝牙降噪耳机", 299, 699),
        ("{brand}无线充电器", 49, 129),
        ("{brand}机械键盘87键", 199, 459),
        ("{brand}便携移动电源", 89, 179),
        ("{brand}USB-C扩展坞", 159, 349),
        ("{brand}智能手环", 149, 299),
        ("{brand}无线鼠标", 59, 149),
        ("{brand}Type-C数据线", 19, 49),
        ("{brand}平板保护壳", 39, 99),
        ("{brand}桌面手机支架", 29, 79),
        ("{brand}电竞游戏鼠标", 179, 399),
        ("{brand}高清摄像头", 249, 499),
    ],
    "家电": [
        ("{brand}智能变频空调", 2299, 4599),
        ("{brand}全自动洗碗机", 1999, 3999),
        ("{brand}便携咖啡机", 599, 1299),
        ("{brand}空气炸锅", 299, 699),
        ("{brand}无线吸尘器", 899, 1999),
        ("{brand}电热水壶", 79, 199),
        ("{brand}破壁料理机", 399, 899),
        ("{brand}智能电饭煲", 299, 699),
        ("{brand}空气净化器", 999, 2499),
        ("{brand}恒温热水器", 999, 2199),
        ("{brand}扫地机器人", 1499, 3299),
        ("{brand}迷你冰箱", 599, 1299),
    ],
    "家居": [
        ("{brand}记忆棉枕头", 79, 179),
        ("{brand}实木书架", 299, 599),
        ("{brand}家居凉拖鞋", 29, 69),
        ("{brand}遮光窗帘", 89, 199),
        ("{brand}乳胶床垫", 899, 1999),
        ("{brand}多功能收纳箱", 49, 119),
        ("{brand}陶瓷餐具套装", 129, 299),
        ("{brand}不锈钢锅具三件套", 299, 599),
        ("{brand}纯棉四件套", 199, 459),
        ("{brand}落地台灯", 149, 329),
        ("{brand}浴室防滑垫", 29, 69),
        ("{brand}加湿器静音", 139, 299),
    ],
    "美妆": [
        ("{brand}保湿精华液", 169, 399),
        ("{brand}防晒隔离霜", 79, 199),
        ("{brand}卸妆水", 49, 119),
        ("{brand}氨基酸洁面乳", 69, 159),
        ("{brand}眼霜抗皱", 199, 499),
        ("{brand}口红唇釉", 59, 199),
        ("{brand}气垫BB霜", 129, 299),
        ("{brand}面膜补水套装", 89, 219),
        ("{brand}粉底液持久", 149, 359),
        ("{brand}眉笔防水", 29, 89),
        ("{brand}香水淡香", 199, 499),
        ("{brand}护手霜滋润", 19, 59),
    ],
    "母婴": [
        ("{brand}婴儿纸尿裤", 69, 159),
        ("{brand}儿童安全座椅", 599, 1499),
        ("{brand}婴儿推车折叠", 499, 1299),
        ("{brand}宝宝辅食机", 199, 459),
        ("{brand}儿童保温杯", 79, 179),
        ("{brand}婴儿湿巾80抽", 19, 49),
        ("{brand}儿童积木拼装", 99, 249),
        ("{brand}孕妇抱枕", 149, 329),
        ("{brand}婴儿睡袋", 89, 219),
        ("{brand}儿童牙刷电动", 59, 139),
        ("{brand}奶粉便携盒", 29, 69),
        ("{brand}婴儿浴巾纯棉", 39, 99),
    ],
    "运动": [
        ("{brand}跑步鞋轻便", 249, 599),
        ("{brand}瑜伽垫加厚", 59, 159),
        ("{brand}运动水壶", 49, 119),
        ("{brand}速干毛巾", 19, 49),
        ("{brand}运动背包", 149, 349),
        ("{brand}哑铃套装", 99, 299),
        ("{brand}跳绳钢丝", 19, 59),
        ("{brand}运动护膝", 39, 99),
        ("{brand}篮球室外", 99, 259),
        ("{brand}运动T恤速干", 69, 159),
        ("{brand}登山杖折叠", 89, 219),
        ("{brand}泳镜防雾", 49, 129),
    ],
    "食品": [
        ("{brand}坚果礼盒", 69, 169),
        ("{brand}有机绿茶", 39, 109),
        ("{brand}牛肉干五香", 29, 79),
        ("{brand}黑巧克力", 19, 59),
        ("{brand}燕麦片即食", 29, 69),
        ("{brand}红枣枸杞茶", 19, 49),
        ("{brand}螺蛳粉速食", 9, 29),
        ("{brand}蜂蜜柚子茶", 29, 69),
        ("{brand}海苔夹心脆", 15, 39),
        ("{brand}芒果干", 19, 49),
        ("{brand}藕粉桂花", 25, 59),
        ("{brand}小麻花零食", 12, 29),
    ],
}

CATEGORY_COLORS = {
    "服饰": ["黑色", "白色", "红色", "蓝色", "灰色", "卡其色", "绿色"],
    "数码": ["黑色", "白色", "银色", "蓝色", "深空灰"],
    "家电": ["白色", "黑色", "银色", "香槟金"],
    "家居": ["原木色", "白色", "灰色", "黑色", "胡桃色"],
    "美妆": ["自然色", "象牙白", "亮肤色", "柔肤色"],
    "母婴": ["粉色", "蓝色", "白色", "黄色", "绿色"],
    "运动": ["黑色", "白色", "红色", "蓝色", "荧光绿"],
    "食品": ["原味", "麻辣", "五香", "酸甜"],
}

CATEGORY_SIZES = {
    "服饰": ["S", "M", "L", "XL", "XXL"],
    "数码": ["标准版", "高配版", "Pro版"],
    "家电": ["标准版", "升级版", "旗舰版"],
    "家居": ["小号", "中号", "大号", "加大号"],
    "美妆": ["30ml", "50ml", "100ml", "150ml"],
    "母婴": ["S", "M", "L", "XL"],
    "运动": ["S", "M", "L", "XL", "XXL"],
    "食品": ["100g", "250g", "500g", "1kg"],
}

# Issue type distribution by product category (weights)
CATEGORY_ISSUE_WEIGHTS = {
    "服饰": {
        "七天无理由": 25, "质量问题": 15, "尺码不合适": 35, "物流破损": 5,
        "少件漏发": 5, "未发货退款": 5, "发票问题": 3, "地址修改": 5, "催发货": 2,
    },
    "数码": {
        "七天无理由": 15, "质量问题": 30, "尺码不合适": 1, "物流破损": 5,
        "少件漏发": 4, "未发货退款": 5, "保修咨询": 25, "配件缺失": 8,
        "发票问题": 5, "地址修改": 2,
    },
    "家电": {
        "七天无理由": 10, "质量问题": 25, "尺码不合适": 0, "物流破损": 8,
        "少件漏发": 5, "未发货退款": 10, "保修咨询": 15, "安装问题": 18,
        "发票问题": 5, "地址修改": 4,
    },
    "家居": {
        "七天无理由": 18, "质量问题": 18, "尺码不合适": 3, "物流破损": 28,
        "少件漏发": 15, "未发货退款": 5, "保修咨询": 3, "发票问题": 5, "地址修改": 5,
    },
    "美妆": {
        "七天无理由": 12, "质量问题": 15, "尺码不合适": 0, "物流破损": 10,
        "少件漏发": 5, "未发货退款": 5, "包装破损": 20, "漏液": 15, "过敏反馈": 13,
        "发票问题": 3, "地址修改": 2,
    },
    "母婴": {
        "七天无理由": 20, "质量问题": 22, "尺码不合适": 10, "物流破损": 8,
        "少件漏发": 8, "未发货退款": 5, "保修咨询": 5, "发票问题": 5,
        "地址修改": 10, "催发货": 7,
    },
    "运动": {
        "七天无理由": 25, "质量问题": 15, "尺码不合适": 25, "物流破损": 8,
        "少件漏发": 7, "未发货退款": 5, "保修咨询": 5, "发票问题": 5, "地址修改": 5,
    },
    "食品": {
        "七天无理由": 15, "质量问题": 20, "物流破损": 30, "少件漏发": 15,
        "未发货退款": 5, "包装破损": 10, "发票问题": 3, "地址修改": 2,
    },
}

SHIPPING_COMPANIES = ["顺丰速运", "中通快递", "圆通速递", "韵达快递", "京东物流", "EMS", "申通快递", "极兔速递"]
PAYMENT_METHODS = ["微信支付", "支付宝", "银行卡", "花呗", "白条", "货到付款"]
PAYMENT_WEIGHTS = [0.38, 0.32, 0.12, 0.08, 0.06, 0.04]

# Warehouse configurations
WAREHOUSES = [
    ("华东仓(杭州)", "浙江", "杭州市"),
    ("华南仓(广州)", "广东", "广州市"),
    ("华北仓(天津)", "天津", "天津市"),
    ("华中仓(武汉)", "湖北", "武汉市"),
    ("西南仓(成都)", "四川", "成都市"),
    ("西北仓(西安)", "陕西", "西安市"),
    ("东北仓(沈阳)", "辽宁", "沈阳市"),
    ("华东二仓(南京)", "江苏", "南京市"),
]

# Status flow definitions
STATUS_FLOWS = {
    "七天无理由": ["已创建", "审核中", "待寄回", "仓库验收中", "退款中", "已完结"],
    "质量问题": ["已创建", "待补充凭证", "审核中", "待寄回", "仓库验收中", "退款中", "已完结"],
    "尺码不合适": ["已创建", "审核中", "换货处理中", "已完结"],
    "物流破损": ["已创建", "待补充凭证", "审核中", "退款中", "已完结"],
    "少件漏发": ["已创建", "待补充凭证", "审核中", "退款中", "已完结"],
    "未发货退款": ["已创建", "审核中", "退款中", "已完结"],
    "保修咨询": ["已创建", "审核中", "已完结"],
    "发票问题": ["已创建", "审核中", "已完结"],
    "地址修改": ["已创建", "审核中", "已完结"],
    "催发货": ["已创建", "审核中", "已完结"],
    "安装问题": ["已创建", "审核中", "已完结"],
    "配件缺失": ["已创建", "审核中", "换货处理中", "已完结"],
    "包装破损": ["已创建", "审核中", "退款中", "已完结"],
    "漏液": ["已创建", "待补充凭证", "审核中", "退款中", "已完结"],
    "过敏反馈": ["已创建", "待补充凭证", "审核中", "退款中", "已完结"],
}

REJECTED_FLOWS = ["已创建", "审核中", "已拒绝"]


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


# ================================================================
# Seed functions
# ================================================================

def _pick_weighted(choices: dict) -> str:
    """Pick a key from a dict of {key: weight}."""
    items = list(choices.items())
    keys = [k for k, _ in items]
    weights = [w for _, w in items]
    return random.choices(keys, weights=weights, k=1)[0]


def _random_date(start_days_ago: int, end_days_ago: int = 0) -> str:
    """Return an ISO datetime string between [start, end] days ago."""
    days = random.randint(end_days_ago, start_days_ago)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    seconds = random.randint(0, 59)
    dt = datetime.now() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _format_dt(dt: datetime) -> str:
    return dt.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def _bounded_after(base: datetime, min_minutes: int, max_minutes: int) -> datetime:
    """Return a random datetime after base, capped at now for realistic demo timelines."""
    now = datetime.now().replace(microsecond=0)
    if base >= now:
        return now

    earliest = base + timedelta(minutes=min_minutes)
    latest = min(base + timedelta(minutes=max_minutes), now)
    if earliest >= latest:
        return max(base, latest)

    delta_seconds = int((latest - earliest).total_seconds())
    return earliest + timedelta(seconds=random.randint(0, delta_seconds))


def seed_customers(conn: sqlite3.Connection, num: int = 5000) -> list[int]:
    rows = []
    for i in range(num):
        surname = random.choice(SURNAMES)
        gender = random.choice(["M", "F"])
        if gender == "M":
            given = random.choice(GIVEN_CHARS_M)
        else:
            given = random.choice(GIVEN_CHARS_F)
        name = surname + given
        phone_last4 = f"{random.randint(0, 9999):04d}"
        member = random.choices(
            ["普通会员", "银卡会员", "金卡会员", "黑卡会员"],
            weights=[0.60, 0.20, 0.13, 0.07],
            k=1,
        )[0]
        province = random.choice(list(PROVINCES_CITIES.keys()))
        city = random.choice(PROVINCES_CITIES[province])
        registered_at = _random_date(1095, 30)  # past 3 years to 30 days ago
        rows.append((name, phone_last4, member, province, city, registered_at))

    conn.executemany(
        "INSERT INTO customers (customer_name, phone_last4, member_level, province, city, registered_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    # Return list of all customer IDs (1-based since autoincrement)
    cur = conn.execute("SELECT customer_id FROM customers ORDER BY customer_id")
    return [r[0] for r in cur.fetchall()]


def seed_products_and_skus(conn: sqlite3.Connection) -> tuple[list[int], list[int]]:
    """Generate 800+ products and ~3000 SKUs. Returns (product_ids, sku_ids)."""
    product_rows = []
    sku_rows = []
    product_id = 1
    sku_id = 1

    for category, templates in CATEGORY_PRODUCT_TEMPLATES.items():
        brands = CATEGORY_BRANDS[category]
        num_per_template = max(9, (100 + len(templates) - 1) // len(templates))
        for tmpl_name, min_price, max_price in templates:
            for _ in range(num_per_template):
                brand = random.choice(brands)
                prod_name = tmpl_name.format(brand=brand)
                base_price = round(random.uniform(min_price, max_price), 2)
                status = random.choices(["在售", "下架", "缺货"], weights=[0.85, 0.08, 0.07], k=1)[0]
                return_rate = round(random.uniform(0, 0.15), 3)
                rating = round(random.uniform(3.5, 5.0), 1)
                product_rows.append((prod_name, category, brand, status, base_price, return_rate, rating))

                # Generate 2-5 SKUs per product
                colors = CATEGORY_COLORS[category]
                sizes = CATEGORY_SIZES[category]
                num_skus = random.randint(2, min(5, len(colors) * len(sizes)))
                combos = []
                for _ in range(num_skus * 3):  # try enough combinations
                    c = random.choice(colors)
                    s = random.choice(sizes)
                    if (c, s) not in combos:
                        combos.append((c, s))
                    if len(combos) == num_skus:
                        break

                for color, size in combos:
                    price = round(base_price * random.uniform(0.85, 1.2), 2)
                    supports_7days = 1 if category not in ("食品",) or random.random() < 0.7 else 0
                    warranty = 0
                    if category == "数码":
                        warranty = random.choice([12, 12, 24, 36])
                    elif category == "家电":
                        warranty = random.choice([12, 24, 36, 60])
                    sku_rows.append((product_id, color, size, price, supports_7days, warranty))
                    sku_id += 1

                product_id += 1

    conn.executemany(
        "INSERT INTO products (product_name, category, brand, status, base_price, return_rate, rating) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        product_rows,
    )
    conn.executemany(
        "INSERT INTO skus (product_id, color, size_or_version, price, supports_7days_return, warranty_months) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        sku_rows,
    )
    conn.commit()

    cur_p = conn.execute("SELECT product_id FROM products ORDER BY product_id")
    cur_s = conn.execute("SELECT sku_id FROM skus ORDER BY sku_id")
    return [r[0] for r in cur_p.fetchall()], [r[0] for r in cur_s.fetchall()]


def seed_warehouses(conn: sqlite3.Connection) -> list[int]:
    conn.executemany(
        "INSERT INTO warehouses (warehouse_name, province, city) VALUES (?, ?, ?)",
        WAREHOUSES,
    )
    conn.commit()
    cur = conn.execute("SELECT warehouse_id FROM warehouses ORDER BY warehouse_id")
    return [r[0] for r in cur.fetchall()]


def seed_inventory(conn: sqlite3.Connection, sku_ids: list[int], warehouse_ids: list[int]) -> None:
    rows = []
    for sku_id in sku_ids:
        # Each SKU is stocked in 1-4 random warehouses
        num_wh = random.randint(1, min(4, len(warehouse_ids)))
        chosen_wh = random.sample(warehouse_ids, num_wh)
        for wh_id in chosen_wh:
            available = random.randint(0, 500)
            locked = random.randint(0, min(50, available // 2))
            safety = random.randint(5, 50)
            restock_eta = None
            if available < safety:
                restock_eta = (datetime.now() + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d")
            rows.append((sku_id, wh_id, available, locked, safety, restock_eta))

    conn.executemany(
        "INSERT INTO inventory (sku_id, warehouse_id, available_stock, locked_stock, safety_stock, restock_eta) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def seed_orders(
    conn: sqlite3.Connection,
    customer_ids: list[int],
    product_ids: list[int],
    sku_ids: list[int],
    num: int = 20000,
) -> list[str]:
    """Generate orders + order_items. Returns list of order IDs."""
    # Pre-load sku info for price lookup
    cur = conn.execute("SELECT sku_id, product_id, price FROM skus")
    sku_info = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    order_rows = []
    order_item_rows = []

    statuses = ["待支付", "待发货", "已发货", "运输中", "已签收", "已完成", "已取消", "退款中", "退款成功"]
    status_weights = [0.05, 0.10, 0.08, 0.12, 0.25, 0.30, 0.04, 0.03, 0.03]

    for idx in range(1, num + 1):
        order_id = f"SO{datetime.now().strftime('%Y%m%d')}{idx:06d}"
        customer_id = random.choice(customer_ids)
        order_status = random.choices(statuses, weights=status_weights, k=1)[0]

        # Keep order lifecycle timestamps in a realistic sequence.
        created_dt = datetime.strptime(_random_date(365, 0), "%Y-%m-%d %H:%M:%S")
        created_at = _format_dt(created_dt)

        # Determine number of items
        num_items = random.choices([1, 2, 3, 4, 5], weights=[0.15, 0.35, 0.30, 0.15, 0.05], k=1)[0]

        # Pick SKUs ensuring no duplicates
        chosen_sku_ids = random.sample(sku_ids, min(num_items, len(sku_ids)))
        if len(chosen_sku_ids) < num_items:
            chosen_sku_ids += random.choices(sku_ids, k=num_items - len(chosen_sku_ids))

        order_total = 0.0
        items_for_order = []
        for sku_id_item in chosen_sku_ids:
            prod_id, sku_price = sku_info[sku_id_item]
            qty = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1], k=1)[0]
            order_total += sku_price * qty
            items_for_order.append((sku_id_item, prod_id, sku_price, qty))

        shipping_fee = round(random.uniform(0, 15), 2) if order_total < 99 else 0
        coupon_amount = round(random.uniform(0, min(50, order_total * 0.2)), 2) if random.random() < 0.4 else 0
        paid_amount = round(order_total + shipping_fee - coupon_amount, 2)
        if paid_amount < 0:
            paid_amount = 0

        paid_at = None
        completed_at = None

        if order_status == "待支付":
            paid_at = None
            paid_amount = 0
        elif order_status == "已取消":
            paid_at = None
            completed_at = _format_dt(_bounded_after(created_dt, 10, 3 * 24 * 60))
        else:
            paid_dt = _bounded_after(created_dt, 5, 24 * 60)
            paid_at = _format_dt(paid_dt)
            if order_status in ("已完成", "退款成功"):
                completed_at = _format_dt(_bounded_after(paid_dt, 2 * 24 * 60, 30 * 24 * 60))

        order_rows.append((
            order_id, customer_id, order_status, "无",
            round(order_total, 2), round(paid_amount, 2), round(coupon_amount, 2),
            round(shipping_fee, 2), created_at, paid_at, completed_at,
        ))

        for sku_id_item, prod_id, price, qty in items_for_order:
            # Get product/sku names for snapshot
            cur2 = conn.execute("SELECT product_name FROM products WHERE product_id = ?", (prod_id,))
            prod_name = cur2.fetchone()[0]
            cur3 = conn.execute("SELECT color, size_or_version FROM skus WHERE sku_id = ?", (sku_id_item,))
            sku_row = cur3.fetchone()
            sku_snap = f"{sku_row[0]}/{sku_row[1]}" if sku_row[0] and sku_row[1] else (sku_row[0] or sku_row[1] or "默认")

            refund_eligible = 1 if order_status not in ("已取消", "退款成功") else 0
            order_item_rows.append((
                order_id, prod_id, sku_id_item, prod_name, sku_snap,
                price, qty, refund_eligible,
            ))

    # Batch insert
    conn.executemany(
        "INSERT INTO orders (order_id, customer_id, order_status, after_sales_status, "
        "order_total, paid_amount, coupon_amount, shipping_fee, created_at, paid_at, completed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        order_rows,
    )
    conn.executemany(
        "INSERT INTO order_items (order_id, product_id, sku_id, product_name_snapshot, "
        "sku_snapshot, unit_price, quantity, refund_eligible) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        order_item_rows,
    )
    conn.commit()
    return [r[0] for r in order_rows]


def seed_payments(conn: sqlite3.Connection, order_ids: list[str]) -> None:
    """Create payments for orders that have been paid."""
    # Fetch orders with their status and paid_amount
    cur = conn.execute(
        "SELECT order_id, order_status, paid_amount, paid_at FROM orders"
    )
    orders = {r[0]: (r[1], r[2], r[3]) for r in cur.fetchall()}

    rows = []
    for order_id in order_ids:
        status, paid_amount, paid_at = orders[order_id]
        if status == "待支付":
            payment_status = "待支付"
            method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]
            txn_no = None
            pa = None
            refunded = 0
        elif status == "已取消":
            continue
        else:
            payment_status = random.choices(
                ["支付成功", "已退款", "部分退款"],
                weights=[0.85, 0.10, 0.05],
                k=1,
            )[0]
            method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS, k=1)[0]
            txn_no = f"TXN{random.randint(100000000, 999999999)}"
            pa = paid_at
            refunded = round(random.uniform(0, paid_amount * 0.5), 2) if payment_status in ("已退款", "部分退款") else 0

        rows.append((order_id, method, payment_status, txn_no, round(paid_amount, 2), pa, round(refunded, 2)))

    conn.executemany(
        "INSERT INTO payments (order_id, payment_method, payment_status, transaction_no, "
        "paid_amount, paid_at, refunded_amount) VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def seed_shipments(
    conn: sqlite3.Connection,
    order_ids: list[str],
    warehouse_ids: list[int],
) -> list[int]:
    """Create shipments for orders that are shipped or beyond. Returns shipment_ids."""
    cur = conn.execute(
        "SELECT order_id, order_status, customer_id, created_at, paid_at FROM orders "
        "WHERE order_status IN ('已发货', '运输中', '已签收', '已完成', '退款中', '退款成功')"
    )
    eligible = {r[0]: (r[1], r[2], r[3], r[4]) for r in cur.fetchall()}

    cur2 = conn.execute("SELECT customer_id, province, city FROM customers")
    customer_addr = {r[0]: (r[1], r[2]) for r in cur2.fetchall()}

    rows = []
    shipment_id = 1

    for order_id, (status, cust_id, created_at, paid_at) in eligible.items():
        wh_id = random.choice(warehouse_ids)
        company = random.choice(SHIPPING_COMPANIES)
        tracking = f"{company[:2].upper()}{random.randint(100000000, 999999999)}"

        if status == "已发货":
            del_status = "已发货"
        elif status == "运输中":
            del_status = "运输中"
        elif status in ("已签收", "已完成"):
            del_status = "已签收"
        else:
            del_status = random.choice(["已签收", "运输中"])

        prov, city = customer_addr.get(cust_id, ("北京", "北京市"))
        address = f"{prov}{city}区测试路{random.randint(1, 300)}号"

        ship_base = datetime.strptime(paid_at or created_at, "%Y-%m-%d %H:%M:%S")
        shipped_at = _bounded_after(ship_base, 30, 2 * 24 * 60)
        est_delivery = (shipped_at + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d")
        shipped_at_str = _format_dt(shipped_at)
        signed_at = _format_dt(_bounded_after(shipped_at, 12 * 60, 4 * 24 * 60)) if del_status == "已签收" else None

        rows.append((
            order_id, wh_id, company, tracking, del_status,
            est_delivery, address, shipped_at_str, signed_at,
        ))
        shipment_id += 1

    conn.executemany(
        "INSERT INTO shipments (order_id, warehouse_id, shipping_company, tracking_no, "
        "delivery_status, estimated_delivery, shipping_address, shipped_at, signed_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()

    cur = conn.execute("SELECT shipment_id FROM shipments ORDER BY shipment_id")
    return [r[0] for r in cur.fetchall()]


def seed_shipment_events(conn: sqlite3.Connection, shipment_ids: list[int]) -> None:
    """Generate tracking events for each shipment."""
    rows = []
    event_templates = [
        "【{location}】快件已揽收",
        "【{location}】快件离开{location}营业点",
        "【{location}】快件到达{location}分拣中心",
        "【{location}】快件离开{location}分拣中心",
        "【{location}】快件到达{location}中转站",
        "【{location}】快件离开{location}中转站",
        "【{location}】快件到达{location}派送点",
        "【{location}】快递员{name}正在为您派送，电话{phone}",
        "【{location}】快件已签收，签收人：本人",
        "【{location}】快件已放入{location}快递柜/驿站",
    ]
    locations = [
        "杭州", "广州", "深圳", "北京", "上海", "武汉", "成都", "西安",
        "南京", "天津", "重庆", "郑州", "长沙", "济南", "福州", "沈阳",
    ]
    couriers = ["张师傅", "李师傅", "王师傅", "赵师傅", "刘师傅", "陈师傅", "杨师傅", "周师傅"]

    cur = conn.execute(
        "SELECT s.shipment_id, s.shipped_at, s.signed_at, s.delivery_status "
        "FROM shipments s"
    )
    shipments = {r[0]: (r[1], r[2], r[3]) for r in cur.fetchall()}

    for sid, (shipped_at, signed_at, del_status) in shipments.items():
        if not shipped_at:
            continue

        shipped_dt = datetime.strptime(shipped_at, "%Y-%m-%d %H:%M:%S")
        signed_dt = datetime.strptime(signed_at, "%Y-%m-%d %H:%M:%S") if signed_at else shipped_dt + timedelta(days=3)

        # Generate 1-3 events
        num_events = random.randint(1, 3)
        duration = (signed_dt - shipped_dt).total_seconds()
        if duration <= 0:
            duration = 86400  # default 1 day

        for i in range(num_events):
            fraction = i / (num_events - 1) if num_events > 1 else 0
            event_dt = shipped_dt + timedelta(seconds=duration * fraction)

            if i == 0:
                tmpl = event_templates[0]
            elif i == num_events - 1 and del_status == "已签收":
                tmpl = event_templates[8]
            elif i == num_events - 2 and del_status == "已签收":
                tmpl = event_templates[7]
            else:
                tmpl = random.choice(event_templates[1:7])

            loc1 = random.choice(locations)
            loc2 = random.choice(locations)
            cname = random.choice(couriers)
            phone = f"138{random.randint(10000000, 99999999)}"

            desc = tmpl.format(location=loc1, name=cname, phone=phone)
            # Fix double location patterns
            desc = desc.replace(f"{loc1}快递柜/驿站", f"快递柜/驿站")
            desc = desc.replace(f"离开{loc1}营业点", f"离开营业点")
            # Simplify: replace second location placeholder
            import re
            # Just use the description as template with simple replacements
            event_time = event_dt.strftime("%Y-%m-%d %H:%M:%S")
            rows.append((sid, event_time, loc1, desc))

    conn.executemany(
        "INSERT INTO shipment_events (shipment_id, event_time, event_location, event_description) "
        "VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()


def seed_refund_rules(conn: sqlite3.Connection) -> None:
    rules = [
        ("RR001", "通用", "七天无理由", "签收后7天内可退货，商品须保持原状、未使用、包装完好",
         "已签收,已完成", "7天内申请，商品不影响二次销售", "商品完整照片、包装照片", "1-3个工作日", "全额退款（不含运费）"),
        ("RR002", "数码", "质量问题", "签收后15天内，经检测确认为非人为质量问题，可退货/换货",
         "已签收,已完成", "15天内申请，需官方检测确认", "故障视频、检测报告", "3-7个工作日", "全额退款或换货"),
        ("RR003", "服饰", "尺码不合适", "签收后7天内可换码，限一次",
         "已签收,已完成", "7天内申请，吊牌完好未下水", "吊牌照片、商品照片", "1-3个工作日", "换货免运费"),
        ("RR004", "家电", "未发货退款", "未发货前可申请全额退款",
         "待支付,待发货", "发货前可无理由取消", "无需凭证", "即时-24小时", "全额退款"),
        ("RR005", "数码", "保修咨询", "保修期内非人为故障可享受免费维修服务",
         "已签收,已完成", "保修期内，非人为损坏", "购买凭证、故障描述", "7-15个工作日", "免费维修或换新"),
        ("RR006", "家居", "物流破损", "签收时发现商品破损，需在24小时内拍照留证",
         "已签收,已完成", "签收24小时内反馈", "破损商品照片（含外包装）", "1-3个工作日", "退款或补发"),
        ("RR007", "美妆", "过敏反馈", "使用后出现过敏反应，需提供皮肤科诊断证明",
         "已签收,已完成", "7天内反馈，需医院证明", "过敏部位照片、诊断证明", "3-7个工作日", "退款或换货"),
        ("RR008", "通用", "少件漏发", "收到商品后发现少件/漏发",
         "已签收,已完成", "签收48小时内反馈", "开箱视频或照片", "1-3个工作日", "补发或退款"),
        ("RR009", "家电", "安装问题", "商品安装过程中遇到问题或安装损坏",
         "已签收,已完成", "安装后7天内反馈", "安装现场照片、安装工单", "3-7个工作日", "免费维修或换货"),
        ("RR010", "通用", "发票问题", "发票信息错误或未收到发票",
         "所有状态", "任意时间可申请", "无需凭证", "1-3个工作日", "补开发票"),
        ("RR011", "数码", "配件缺失", "收到商品后发现有配件缺失",
         "已签收,已完成", "签收48小时内反馈", "开箱照片、配件清单对照", "1-3个工作日", "补发配件"),
        ("RR012", "美妆", "包装破损", "收到商品时包装破损影响使用",
         "已签收,已完成", "签收24小时内反馈", "破损包装照片", "1-3个工作日", "退款或换货"),
    ]
    conn.executemany(
        "INSERT INTO refund_rules (rule_id, category, issue_type, rule_summary, eligible_order_status, "
        "conditions, required_evidence, processing_time, refund_scope) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rules,
    )
    conn.commit()


def _parse_dt(dt_str: str | None) -> datetime | None:
    if not dt_str:
        return None
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


def seed_after_sales(
    conn: sqlite3.Connection,
    order_ids: list[str],
    customer_ids: list[int],
) -> list[str]:
    """Generate after-sales tickets + events + refunds + exchanges + compensations + attachments."""
    # Only create tickets for orders that are 已签收, 已完成, 退款中, 退款成功
    # plus a few for 已发货/运输中 (催发货, 地址修改, 未发货退款)
    cur = conn.execute(
        "SELECT o.order_id, o.customer_id, o.order_status, o.paid_amount, "
        "o.created_at, o.paid_at, s.shipped_at, s.signed_at, "
        "oi.product_id, oi.sku_id, oi.unit_price, oi.quantity, p.category "
        "FROM orders o "
        "LEFT JOIN shipments s ON o.order_id = s.order_id "
        "JOIN order_items oi ON o.order_id = oi.order_id "
        "JOIN products p ON oi.product_id = p.product_id "
        "WHERE o.order_status IN ('已签收', '已完成', '退款中', '退款成功', '已发货', '运输中')"
    )
    order_details = {}
    for r in cur.fetchall():
        oid = r[0]
        if oid not in order_details:
            order_details[oid] = {
                "customer_id": r[1],
                "status": r[2],
                "paid_amount": r[3],
                "created_at": r[4],
                "paid_at": r[5],
                "shipped_at": r[6],
                "signed_at": r[7],
                "items": [],
            }
        order_details[oid]["items"].append({
            "product_id": r[8],
            "sku_id": r[9],
            "unit_price": r[10],
            "quantity": r[11],
            "category": r[12],
        })

    # Determine how many tickets to create (~2500-3500)
    num_tickets = random.randint(2500, 3500)
    eligible_orders = list(order_details.keys())
    chosen_orders = random.sample(eligible_orders, min(num_tickets, len(eligible_orders)))
    if len(chosen_orders) < num_tickets:
        extras = random.choices(eligible_orders, k=num_tickets - len(chosen_orders))
        chosen_orders += extras

    ticket_rows = []
    ticket_event_rows = []
    refund_rows = []
    exchange_rows = []
    compensation_rows = []
    attachment_rows = []

    assignment_groups = ["售后客服组", "售后质检组", "退款审核组", "仓储物流组", "VIP客服组", "技术支持组"]

    for idx, order_id in enumerate(chosen_orders):
        detail = order_details[order_id]
        cust_id = detail["customer_id"]
        order_status = detail["status"]
        paid_amount = detail["paid_amount"]

        # Determine primary category from items
        categories = [item["category"] for item in detail["items"]]
        primary_cat = max(set(categories), key=categories.count)

        # Pick issue type based on category weights
        weights = CATEGORY_ISSUE_WEIGHTS.get(primary_cat, CATEGORY_ISSUE_WEIGHTS["服饰"])
        issue_type = _pick_weighted(weights)

        # Only certain issue types are valid for pending orders
        if order_status in ("已发货", "运输中"):
            allowed = {"催发货", "地址修改", "未发货退款", "发票问题"}
            if issue_type not in allowed:
                issue_type = random.choice(list(allowed))

        # Generate ticket ID
        ticket_id = f"AS{datetime.now().strftime('%Y%m%d')}{idx + 1:06d}"

        # Determine flow and final status
        flow = STATUS_FLOWS.get(issue_type, ["已创建", "审核中", "已完结"])
        # ~12% chance of being rejected
        if random.random() < 0.12:
            flow = REJECTED_FLOWS
            status = random.choice(REJECTED_FLOWS)
        else:
            # Weight toward later stages so more refunds/exchanges are generated
            weights = [1, 1, 2, 2, 3, 4, 5][:len(flow)]
            status = random.choices(flow, weights=weights, k=1)[0]

        # Priority: higher for VIP customers, quality issues, high-value orders
        cur_member = conn.execute(
            "SELECT member_level FROM customers WHERE customer_id = ?", (cust_id,)
        ).fetchone()
        member = cur_member[0] if cur_member else "普通会员"

        priority = "中"
        if issue_type == "质量问题":
            priority = random.choices(["中", "高", "紧急"], weights=[0.3, 0.5, 0.2], k=1)[0]
        elif paid_amount > 500:
            priority = random.choices(["中", "高"], weights=[0.5, 0.5], k=1)[0]
        elif member in ("金卡会员", "黑卡会员"):
            priority = random.choices(["中", "高"], weights=[0.4, 0.6], k=1)[0]

        assigned = random.choice(assignment_groups)
        if member == "黑卡会员":
            assigned = "VIP客服组"

        if order_status in ("已签收", "已完成", "退款中", "退款成功"):
            base_dt = (
                _parse_dt(detail.get("signed_at"))
                or _parse_dt(detail.get("shipped_at"))
                or _parse_dt(detail.get("paid_at"))
                or _parse_dt(detail["created_at"])
            )
        else:
            base_dt = (
                _parse_dt(detail.get("shipped_at"))
                or _parse_dt(detail.get("paid_at"))
                or _parse_dt(detail["created_at"])
            )
        created_dt = _bounded_after(base_dt, 60, 30 * 24 * 60)
        created_at = _format_dt(created_dt)
        closed_at = (
            _format_dt(_bounded_after(created_dt, 24 * 60, 30 * 24 * 60))
            if status in ("已完结", "已拒绝", "已取消")
            else None
        )
        sla = "24 小时内首次响应" if priority in ("高", "紧急") else "48 小时内首次响应"

        # Generate description based on issue type
        descriptions = {
            "七天无理由": "商品不满意，申请七天无理由退货，包装完好未使用。",
            "质量问题": "收到商品后发现存在质量问题，已影响正常使用，要求处理。",
            "尺码不合适": "购买的商品尺码偏大/偏小，穿着不合适，申请换码。",
            "物流破损": "收到包裹时发现外包装破损，内部商品有损坏。",
            "少件漏发": "收到的包裹中少了一件商品，与实际订单不符。",
            "未发货退款": "订单长时间未发货，申请取消订单并退款。",
            "保修咨询": "商品在使用中出现故障，咨询保修政策和维修流程。",
            "发票问题": "需要补开发票/发票信息有误需要修改。",
            "地址修改": "需要修改收货地址，请协助处理。",
            "催发货": "订单已支付多日仍未发货，催促尽快安排发货。",
            "安装问题": "收到商品后自己安装遇到困难，申请安装指导。",
            "配件缺失": "开箱后发现缺少配件，影响正常使用。",
            "包装破损": "收到商品时包装已破损，怀疑商品可能受损。",
            "漏液": "收到商品时发现液体泄漏，包装内部已污染。",
            "过敏反馈": "使用该产品后出现皮肤过敏反应，要求处理。",
        }
        description = descriptions.get(issue_type, "售后咨询，请协助处理。")

        contact_phone = f"138{random.randint(10000000, 99999999)}"

        ticket_rows.append((
            ticket_id, order_id, cust_id, issue_type, description, contact_phone,
            status, priority, assigned, created_at, closed_at, sla,
        ))

        # Generate ticket events along the flow
        flow_idx = flow.index(status) if status in flow else 0
        current_flow = flow[:flow_idx + 1]
        for fi, fs in enumerate(current_flow):
            event_time_dt = _bounded_after(created_dt, fi * 4 * 60, fi * 24 * 60 + 12 * 60)
            event_time = _format_dt(event_time_dt)

            if fs == "已创建":
                event_type = "创建"
                role = "系统"
                note = f"客户提交售后申请：{issue_type}"
            elif fs == "待补充凭证":
                event_type = "要求补充凭证"
                role = "审核专员"
                note = "请客户提供商品问题相关凭证（照片/视频）"
            elif fs == "审核中":
                if fi == 1:
                    event_type = "提交凭证"
                    role = "客户"
                    note = "客户已上传相关凭证材料"
                else:
                    event_type = "审核通过"
                    role = "审核专员"
                    note = f"审核通过，问题类型：{issue_type}，进入后续处理流程"
            elif fs == "待寄回":
                event_type = "待寄回通知"
                role = "系统"
                note = "请客户将商品寄回指定仓库地址"
            elif fs == "仓库验收中":
                event_type = "仓库验收"
                role = "仓库人员"
                note = "仓库已收到退回商品，正在进行验收"
            elif fs == "退款中":
                event_type = "退款发起"
                role = "财务专员"
                note = "退款申请已提交财务处理"
            elif fs == "换货处理中":
                event_type = "换货发出"
                role = "仓库人员"
                note = "换货商品已发出，请注意查收"
            elif fs == "已完结":
                event_type = "完结"
                role = "系统"
                note = "工单处理完成，已结案"
            elif fs == "已拒绝":
                event_type = "拒绝"
                role = "审核专员"
                note = "经审核，该申请不符合售后条件，予以拒绝"
            else:
                event_type = "备注"
                role = "客服"
                note = "工单状态更新"

            ticket_event_rows.append((ticket_id, event_time, role, event_type, note))

        # Generate refunds for statuses that involve refund
        refund_eligible_types = {"七天无理由", "质量问题", "物流破损", "少件漏发", "未发货退款",
                                  "包装破损", "漏液", "过敏反馈", "尺码不合适"}
        if status in ("退款中", "已完结") and issue_type in refund_eligible_types:
            refund_amount = round(paid_amount * random.uniform(0.5, 1.0), 2)
            refund_amount = min(refund_amount, paid_amount)
            refund_status = "已退款" if status == "已完结" else "退款中"
            approved_at = _bounded_after(created_dt, 24 * 60, 3 * 24 * 60)
            refunded_at = _bounded_after(approved_at, 24 * 60, 5 * 24 * 60) if refund_status == "已退款" else None
            refund_rows.append((
                ticket_id, order_id, refund_status, refund_amount, issue_type,
                created_at,
                _format_dt(approved_at),
                _format_dt(refunded_at) if refunded_at else None,
            ))

        # Generate exchanges for issue types that commonly result in exchange
        exchange_eligible = {"尺码不合适", "配件缺失", "质量问题", "物流破损", "漏液", "少件漏发", "包装破损"}
        should_exchange = (
            (issue_type in exchange_eligible and status in ("换货处理中", "已完结"))
            or (status == "已完结" and random.random() < 0.12)
        )
        if should_exchange:
            items_list = detail["items"]
            if items_list:
                item = random.choice(items_list)
                old_sku = item["sku_id"]
                # Pick a different SKU from the same product
                cur_sku = conn.execute(
                    "SELECT sku_id FROM skus WHERE product_id = ? AND sku_id != ? ORDER BY RANDOM() LIMIT 1",
                    (item["product_id"], old_sku),
                ).fetchone()
                new_sku = cur_sku[0] if cur_sku else old_sku
                exch_status = "已完结" if status == "已完结" else "换货中"
                new_tracking = f"EX{random.choice(SHIPPING_COMPANIES)[:2].upper()}{random.randint(100000000, 999999999)}" if exch_status == "已完结" else None
                exchange_rows.append((
                    ticket_id, order_id, old_sku, new_sku, exch_status,
                    new_tracking, created_at,
                ))

        # Generate compensations (~45% chance for VIP/金卡/黑卡, ~25% for others)
        comp_prob = 0.45 if member in ("金卡会员", "黑卡会员") else 0.25
        if random.random() < comp_prob:
            comp_type = random.choice(["优惠券", "现金补偿", "积分补偿", "免运费", "赠品"])
            comp_amount = None
            if comp_type == "优惠券":
                comp_amount = round(random.uniform(5, 50), 2)
            elif comp_type == "现金补偿":
                comp_amount = round(random.uniform(10, 100), 2)
            elif comp_type == "积分补偿":
                comp_amount = round(random.uniform(100, 1000), 0)
            comp_desc = f"因{issue_type}问题，给予客户{comp_type}作为补偿"
            comp_time = _bounded_after(created_dt, 24 * 60, 7 * 24 * 60)
            compensation_rows.append((
                ticket_id, comp_type, comp_amount, comp_desc,
                _format_dt(comp_time),
            ))

        # Generate attachments (1-3 per ticket, for issue types that typically need evidence)
        evidence_types = {"质量问题", "物流破损", "少件漏发", "包装破损", "漏液", "过敏反馈",
                          "配件缺失", "七天无理由", "尺码不合适", "安装问题"}
        if issue_type in evidence_types:
            num_att = random.randint(1, 3)
            for a in range(num_att):
                att_type = random.choice(["图片", "图片", "图片", "视频", "截图"])
                ext = "jpg" if att_type == "图片" else ("mp4" if att_type == "视频" else "png")
                file_name = f"{issue_type}_凭证_{a + 1}.{ext}"
                mock_url = f"/mock/attachments/{ticket_id}/{file_name}"
                upload_time = _bounded_after(created_dt, 60, 48 * 60)
                attachment_rows.append((
                    ticket_id, att_type, file_name, mock_url,
                    _format_dt(upload_time),
                ))

    # Batch insert all
    conn.executemany(
        "INSERT INTO after_sales_tickets (ticket_id, order_id, customer_id, issue_type, "
        "description, contact_phone, status, priority, assigned_to, created_at, closed_at, sla) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ticket_rows,
    )
    conn.executemany(
        "INSERT INTO ticket_events (ticket_id, event_time, operator_role, event_type, event_note) "
        "VALUES (?, ?, ?, ?, ?)",
        ticket_event_rows,
    )
    if refund_rows:
        conn.executemany(
            "INSERT INTO refunds (ticket_id, order_id, refund_status, refund_amount, refund_reason, "
            "requested_at, approved_at, refunded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            refund_rows,
        )
    if exchange_rows:
        conn.executemany(
            "INSERT INTO exchanges (ticket_id, order_id, old_sku_id, new_sku_id, exchange_status, "
            "new_tracking_no, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            exchange_rows,
        )
    if compensation_rows:
        conn.executemany(
            "INSERT INTO compensations (ticket_id, compensation_type, amount, description, issued_at) "
            "VALUES (?, ?, ?, ?, ?)",
            compensation_rows,
        )
    if attachment_rows:
        conn.executemany(
            "INSERT INTO attachments (ticket_id, attachment_type, file_name, mock_url, uploaded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            attachment_rows,
        )

    conn.commit()
    return [r[0] for r in ticket_rows]


def update_order_after_sales_status(conn: sqlite3.Connection) -> None:
    """Update orders.after_sales_status based on existing tickets."""
    conn.execute("""
        UPDATE orders SET after_sales_status = '无'
    """)
    conn.execute("""
        UPDATE orders SET after_sales_status = '部分售后'
        WHERE order_id IN (
            SELECT DISTINCT order_id FROM after_sales_tickets WHERE status != '已完结'
        )
    """)
    conn.execute("""
        UPDATE orders SET after_sales_status = '售后完结'
        WHERE order_id IN (
            SELECT order_id FROM after_sales_tickets
            GROUP BY order_id HAVING COUNT(CASE WHEN status != '已完结' THEN 1 END) = 0
        )
        AND order_id IN (SELECT order_id FROM after_sales_tickets)
    """)
    conn.commit()


def update_locked_stock(conn: sqlite3.Connection) -> None:
    """Simulate locked stock for 待发货 orders."""
    conn.execute("UPDATE inventory SET locked_stock = 0")
    conn.execute("""
        UPDATE inventory SET locked_stock = (
            SELECT COALESCE(SUM(oi.quantity), 0)
            FROM order_items oi
            JOIN orders o ON o.order_id = oi.order_id
            WHERE o.order_status = '待发货'
            AND oi.sku_id = inventory.sku_id
        )
    """)
    conn.commit()


def main() -> None:
    print("========================================")
    print("  中文电商售后 Agent — 演示数据库生成")
    print(f"  随机种子: {SEED}")
    print(f"  输出路径: {DB_PATH}")
    print("========================================")

    # Ensure output directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove old database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("[INFO] 已删除旧数据库文件")

    conn = db()

    print("[1/10] 创建表结构...")
    create_schema(conn)

    print("[2/10] 生成客户数据 (5,000)...")
    customer_ids = seed_customers(conn, 5000)
    print(f"      已插入 {len(customer_ids)} 条客户记录")

    print("[3/10] 生成商品和 SKU 数据...")
    product_ids, sku_ids = seed_products_and_skus(conn)
    print(f"      已插入 {len(product_ids)} 个 SPU, {len(sku_ids)} 个 SKU")

    print("[4/10] 生成仓库与库存...")
    warehouse_ids = seed_warehouses(conn)
    seed_inventory(conn, sku_ids, warehouse_ids)
    print(f"      已插入 {len(warehouse_ids)} 个仓库, 库存记录已生成")

    print("[5/10] 生成订单和订单明细 (20,000)...")
    order_ids = seed_orders(conn, customer_ids, product_ids, sku_ids, 20000)
    print(f"      已插入 {len(order_ids)} 条订单, 订单明细已生成")

    print("[6/10] 生成支付记录...")
    seed_payments(conn, order_ids)
    print("      支付记录已生成")

    print("[7/10] 生成物流与轨迹...")
    shipment_ids = seed_shipments(conn, order_ids, warehouse_ids)
    seed_shipment_events(conn, shipment_ids)
    print(f"      已插入 {len(shipment_ids)} 条物流记录, 物流轨迹已生成")

    print("[8/10] 生成退款规则...")
    seed_refund_rules(conn)
    print("      退款规则已生成")

    print("[9/10] 生成售后工单、流转记录、退款、换货、补偿、附件...")
    ticket_ids = seed_after_sales(conn, order_ids, customer_ids)
    print(f"      已插入 {len(ticket_ids)} 条售后工单及相关数据")

    print("[10/10] 更新订单售后状态与锁定库存...")
    update_order_after_sales_status(conn)
    update_locked_stock(conn)
    print("      订单售后状态与库存锁定已更新")

    conn.close()

    # Print statistics
    conn2 = db()
    tables = [
        "customers", "products", "skus", "warehouses", "inventory",
        "orders", "order_items", "payments", "shipments", "shipment_events",
        "after_sales_tickets", "ticket_events", "refunds", "exchanges",
        "compensations", "attachments", "refund_rules",
    ]
    print("\n========================================")
    print("  生成统计")
    print("========================================")
    for t in tables:
        cnt = conn2.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:25s}: {cnt:>8,}")
    conn2.close()

    size_mb = DB_PATH.stat().st_size / (1024 * 1024)
    print(f"\n  数据库文件大小: {size_mb:.1f} MB")
    print("========================================")
    print("  生成完成！")
    print("========================================")


if __name__ == "__main__":
    main()
