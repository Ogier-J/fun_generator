import httpx
import base64
import re
import random
import json
import os
import datetime
import requests
from io import BytesIO
from random import choice

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 兼容 Pillow 新旧版本的 resize 采样方式
try:
    # Pillow >=10.0 的新方式
    Resampling = Image.Resampling
except AttributeError:
    # Pillow <10.0 的旧方式
    Resampling = Image

from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from nonebot.matcher import Matcher

__plugin_meta__ = PluginMetadata(
    name="趣味生成器合集",
    description="营销号、狗屁不通文章、记仇、无中生友、舔狗日记",
    usage="使用对应指令，输入“生成器帮助”查看详细用法",
    extra={"author": "Ogier"}
)

driver = get_driver()

# ==================== 工具函数 ====================
def pic2b64(im: Image.Image) -> str:
    bio = BytesIO()
    im.save(bio, format='PNG')
    base64_str = base64.b64encode(bio.getvalue()).decode()
    return 'base64://' + base64_str

def load_config(path: str) -> dict:
    try:
        with open(path, 'r', encoding='utf8') as f:
            return json.load(f)
    except Exception:
        return {}

def measure(msg: str, font_size: int, img_width: int) -> list[int]:
    i = 0
    l = len(msg)
    length = 0
    positions = []
    while i < l:
        if re.search(r'[0-9a-zA-Z]', msg[i]):
            length += font_size // 2
        else:
            length += font_size
        if length >= img_width:
            positions.append(i)
            length = 0
            i -= 1
        i += 1
    return positions

def get_pic(qq: str) -> bytes:
    api = f'http://q1.qlogo.cn/g?b=qq&nk={qq}&s=100'
    return requests.get(api, timeout=20).content

def get_name(qq: str) -> str:
    try:
        res = requests.get(f"https://api.usuu.ru/qq/?qq={qq}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("name", "富婆")
    except:
        pass
    return '富婆'

# ==================== 资源路径 ====================
BASE_PATH = os.path.dirname(__file__)
DATA_JSON = os.path.join(BASE_PATH, 'data.json')
JICHOU_IMG = os.path.join(BASE_PATH, 'jichou.jpg')
DIARY_BG = os.path.join(BASE_PATH, 'diary.png')
FONT_PATH = os.path.join(BASE_PATH, 'simhei.ttf')  # 建议放一个黑体字体

# ==================== 营销号 ====================
yingxiaohao = on_command("营销号", aliases={"yingxiaohao"}, block=True, priority=5)

@yingxiaohao.handle()
async def _(arg: Message = CommandArg()):
    kw = arg.extract_plain_text().strip()
    if not kw or '/' not in kw or kw.count('/') < 2:
        await yingxiaohao.finish("用法：营销号 A/B/C\n例如：营销号 蔡徐坤/打篮球/玩得好")
        return
    arr = kw.split('/', 2)
    a, b, c = arr[0].strip(), arr[1].strip(), arr[2].strip()
    msg = (
        f" {a}{b}是怎么回事呢？{a}相信大家都很熟悉，但是{a}{b}是怎么回事呢，下面就让小编带大家一起了解吧。\n"
        f" {a}{b}，其实就是{c}，大家可能会很惊讶{a}怎么会{b}呢？但事实就是这样，小编也感到非常惊讶。\n"
        f" 这就是关于{a}{b}的事情了，大家有什么想法呢，欢迎在评论区告诉小编一起讨论哦！"
    )
    await yingxiaohao.finish(msg)

# ==================== 狗屁不通文章 ====================
goupibutong = on_command("狗屁不通", aliases={"goupibutong", "狗屁不通文章"}, block=True, priority=5)

@goupibutong.handle()
async def _(arg: Message = CommandArg()):
    title = arg.extract_plain_text().strip()
    if not title:
        await goupibutong.finish("请提供主题，例如：狗屁不通 量子力学")
        return
    data = load_config(DATA_JSON)
    if not data:
        await goupibutong.finish("data.json 文件加载失败或不存在")
        return
    length = 500
    body = ""
    while len(body) < length:
        num = random.randint(0, 100)
        if num < 10:
            body += "\n"
        elif num < 20:
            body += choice(data.get("famous", [""])).replace("a", choice(data.get("before", [""]))) \
                .replace("b", choice(data.get("after", [""])))
        else:
            body += choice(data.get("bosh", [""]))
        body = body.replace("x", title)
    await goupibutong.finish(body.strip())

# ==================== 记仇（修复版：文字不会被截掉） ====================
jichou = on_command("记仇", aliases={"jichou"}, block=True, priority=5)

@jichou.handle()
async def _(arg: Message = CommandArg()):
    kw = arg.extract_plain_text().strip()
    if not kw:
        await jichou.finish("用法：记仇 某人/做了某事\n或：记仇 某人 做了某事")
        return

    # 智能分割（支持 / 或空格）
    if '/' in kw:
        parts = kw.split('/', 1)
        name = parts[0].strip()
        thing = parts[1].strip()
    else:
        words = kw.split()
        if len(words) < 2:
            await jichou.finish("用法：记仇 某人 做了某事\n或加 / 分隔")
            return
        name = words[0]
        thing = ' '.join(words[1:])

    if not name or not thing:
        await jichou.finish("名字或事件不能为空哦~")
        return

    # 加载底图
    image = Image.open(JICHOU_IMG)  # 假设底图高度 764
    base_height = 764  # 底图部分高度（固定）

    # 字体设置
    font_size = 80
    font = ImageFont.truetype(FONT_PATH, font_size)

    time_str = datetime.datetime.now().strftime('%Y年%m月%d日')
    msg = f'{time_str}，{name}，{thing}，这个仇我先记下了'

    # 自动换行
    positions = measure(msg, font_size, 974)
    str_list = list(msg)
    for pos in positions:
        str_list.insert(pos, '\n')
    msg_with_line = "".join(str_list)

    # 计算实际需要的文字区域高度（动态行高）
    line_count = len(positions) + 1  # 总行数
    line_height = font_size + 20  # 每行高度 = 字体大小 + 间距（可微调）
    text_area_height = line_count * line_height + 40  # 多加点底部padding防截尾

    # 创建文字画布
    image_text = Image.new('RGB', (974, text_area_height), (255, 255, 255))
    draw = ImageDraw.Draw(image_text)
    draw.text((20, 20), msg_with_line, fill=(0, 0, 0), font=font, spacing=10)  # 左上留点边距

    # 模糊文字层
    image_text = image_text.filter(ImageFilter.BLUR)

    # 最终合成画布（底图 + 文字区）
    total_height = base_height + text_area_height
    image_back = Image.new('RGB', (974, total_height), (255, 255, 255))
    image_back.paste(image, (0, 0))                  # 底图在上
    image_back.paste(image_text, (0, base_height))   # 模糊文字在下

    await jichou.finish(MessageSegment.image(pic2b64(image_back)))

# ==================== 无中生友 ====================
wuzhongshengyou = on_command("无中生友", aliases={"无中生有", "wuzhongshengyou"}, block=True, priority=5)

@wuzhongshengyou.handle()
async def _(arg: Message = CommandArg()):
    kw = arg.extract_plain_text().strip()
    if '/' not in kw:
        await wuzhongshengyou.finish("用法：无中生友 我今天好开心/QQ号")
        return
    arr = kw.split('/', 1)
    text, qq = arr[0].strip(), arr[1].strip()
    text = text.replace('他', '我').replace('她', '我')
    avatar_bytes = get_pic(qq)
    avatar = Image.open(BytesIO(avatar_bytes))
    scale = 3
    r = 100 * scale
    alpha = Image.new('L', (r, r), 0)
    draw = ImageDraw.Draw(alpha)
    draw.ellipse((0, 0, r, r), fill=255)
    alpha = alpha.resize((100, 100), Resampling.LANCZOS)
    mask_img = Image.new('RGBA', (100, 100))
    mask_img.paste(avatar.resize((100, 100)), (0, 0))
    mask_img.putalpha(alpha)
    font_name = ImageFont.truetype(FONT_PATH, 30)
    font_text = ImageFont.truetype(FONT_PATH, 25)
    name = get_name(qq)
    image_text = Image.new('RGB', (450, 150), (255, 255, 255))
    draw = ImageDraw.Draw(image_text)
    draw.text((0, 0), name, fill=(0, 0, 0), font=font_name)
    draw.text((0, 40), text, fill=(125, 125, 125), font=font_text)
    final = Image.new('RGB', (700, 150), (255, 255, 255))
    final.paste(mask_img, (25, 25), mask_img)
    final.paste(image_text, (150, 40))
    await wuzhongshengyou.finish(MessageSegment.image(pic2b64(final)))

# ==================== 舔狗日记 ====================
pre_content = ""  # 避免连续重复

TIANGOU_APIS = [
    "https://api.yujn.cn/api/tiangou.php",
    "https://v2.api-m.com/api/dog",
    "https://v.api.aa1.cn/api/tiangou"
]

async def fetch_tiangou() -> str | None:
    """从API获取舔狗日记（兼容所有驱动，不依赖 driver.http）"""
    apis = TIANGOU_APIS.copy()
    random.shuffle(apis)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }

    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        for url in apis:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue

                raw_text = resp.text.strip()

                if "api.yujn.cn" in url:
                    text = raw_text.split("----", 1)[0].strip() if "----" in raw_text else raw_text

                elif "api-m.com" in url:
                    try:
                        data = resp.json()
                        if data.get("code") == 200 and data.get("data"):
                            text = data["data"].strip()
                        else:
                            continue
                    except Exception:
                        continue

                elif "aa1.cn" in url:
                    text = re.sub(r'<[^>]+>', '', raw_text).strip()

                if text and len(text) > 15:
                    return text

            except Exception as e:
                print(f"API请求失败: {url} - {e}")  # 保留日志打印，便于调试
                continue

    return None

tiangouriji = on_command("舔狗日记", aliases={"tiangouriji"}, block=True, priority=5)

@tiangouriji.handle()
async def _(arg: Message = CommandArg()):
    global pre_content
    kw = arg.extract_plain_text().strip()
    name = '富婆'
    weather = ''
    content = ''

    if '/' in kw:
        parts = kw.split('/', 1)
        if len(parts) == 2:
            prefix, content = parts
            weather = prefix.split()[-1] if prefix.strip() else ''
            name_part = prefix.strip().split()[0] if prefix.strip() else ''
            if name_part:
                name = name_part
            content = content.strip()
    else:
        if ' ' in kw:
            name, weather = kw.split(' ', 1)
        elif kw:
            name = kw

    if not content:
        content = await fetch_tiangou()
        if not content:
            await tiangouriji.finish("舔狗日记API暂时不可用，稍后再试哦~")
            return
        attempts = 0
        while content == pre_content and attempts < 5:
            new_content = await fetch_tiangou()
            if new_content:
                content = new_content
            attempts += 1
        pre_content = content

    for s in '你她':
        content = content.replace(s, name)

    time_str = datetime.datetime.now().strftime('%Y年%m月%d日')
    bg = Image.open(DIARY_BG)
    img_w, img_h = bg.size
    font_size = img_w // 18
    font = ImageFont.truetype(FONT_PATH, font_size)
    positions = measure(content, font_size, img_w)
    str_list = list(content)
    for pos in positions:
        str_list.insert(pos, '\n')
    full_text = f'{time_str}，{weather}\n' + "".join(str_list)
    line_count = len(positions) + 2
    line_h = font_size + 4
    text_img = Image.new('RGB', (img_w, line_h * line_count), (255, 255, 255))
    draw = ImageDraw.Draw(text_img)
    draw.text((0, 0), full_text, fill=(0, 0, 0), font=font, spacing=2)
    final = Image.new('RGB', (img_w, line_h * line_count + img_h), (255, 255, 255))
    final.paste(bg, (0, 0))
    final.paste(text_img, (0, img_h))
    await tiangouriji.finish(MessageSegment.image(pic2b64(final)))

# ==================== 插件帮助（修复版：文字不会超出） ====================
help_cmd = on_command(
    "生成器帮助",
    aliases={"趣味生成器帮助", "生成器", "趣味生成器"},
    rule=to_me(),
    priority=10,
    block=True
)

@help_cmd.handle()
async def _(matcher: Matcher):
    help_text = """
🎉 趣味生成器合集 · 使用帮助

📢 营销号
指令：营销号 A/B/C
示例：营销号 蔡徐坤/打篮球/玩得好

📄 狗屁不通文章
指令：狗屁不通 主题
示例：狗屁不通 量子力学

😡 记仇
指令：记仇 某人/做了某事
示例：记仇 小明/偷吃了我的零食

👥 无中生友
指令：无中生友 内容文字/QQ号
示例：无中生友 今天天气真好/123456789
说明：自动把“他/她”替换为“我”，并显示QQ头像+昵称

🐶 舔狗日记
• 舔狗日记 → 随机一条
• 舔狗日记 小美 → 指定名字
• 舔狗日记 小美 阴天 → 加天气
• 舔狗日记 小美/今天又没回我消息 → 自定义内容

💡 提示
所有指令支持别名（如 yingxiaohao、tiangouriji）
私聊或@机器人时可直接发送“生成器帮助”查看本消息
    """.strip()

    lines = [line.strip() for line in help_text.split("\n") if line.strip()]

    font_size = 35
    title_font_size = font_size + 6
    line_height = font_size + 16
    padding_left = 50
    padding_top = 50
    padding_bottom = 60

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
        title_font = ImageFont.truetype(FONT_PATH, title_font_size)
    except:
        font = ImageFont.load_default(size=font_size)
        title_font = ImageFont.load_default(size=title_font_size + 6)

    draw_temp = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    # 计算每行实际像素宽度
    line_widths = []
    for line in lines:
        if any(emoji in line for emoji in "🎉📢📄😡👥🐶💡"):
            bbox = draw_temp.textbbox((0, 0), line, font=title_font)
        else:
            bbox = draw_temp.textbbox((0, 0), line, font=font)
        line_widths.append(bbox[2] - bbox[0])

    max_line_width = max(line_widths, default=600)
    img_width = max_line_width + padding_left * 2
    img_height = len(lines) * line_height + padding_top + padding_bottom

    img = Image.new("RGB", (int(img_width), int(img_height)), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    y = padding_top
    for i, line in enumerate(lines):
        x = padding_left

        if any(emoji in line for emoji in "🎉📢📄😡👥🐶💡"):
            # 标题行：深蓝 + 大字体
            draw.text((x, y), line, fill=(0, 100, 200), font=title_font)
        else:
            # 正文：深灰 + 正常字体
            draw.text((x, y), line, fill=(40, 40, 40), font=font)

        y += line_height

    # 可选：加个标题居中（第一行）
    first_line = "趣味生成器合集 · 使用帮助"
    bbox = draw.textbbox((0, 0), first_line, font=title_font)
    title_x = (img_width - (bbox[2] - bbox[0])) // 2
    # 画个白色底块盖掉原文字（如果需要更突出）
    draw.rectangle((title_x - 20, padding_top - 10, title_x + bbox[2] - bbox[0] + 20, padding_top + title_font_size + 10), fill=(255, 255, 255))
    draw.text((title_x, padding_top), first_line, fill=(0, 80, 180), font=title_font)

    await matcher.finish(MessageSegment.image(pic2b64(img)))