import os
import re

# 解决路径问题
os.chdir(os.path.dirname(__file__))
os.chdir('../umineko-scripting')

# 文件路径定义
languages = ['jp', 'cn', 'cht']
base_path = 'story/ep8/{}/umi8_9.txt'
menu_path = 'script/{}/menu.txt'
exefs_path = '../../exefs_texts.txt'

jp_file = base_path.format('jp')
cn_file = base_path.format('cn')
cht_file = base_path.format('cht')
cn_menu_file = menu_path.format('cn')
cht_menu_file = menu_path.format('cht')

# 其他常量定义
purple_code = '{p:42:'
red_code = '{p:1:'
jp_pattern = [
    '「ひょっとしたら生きているかもと。',
    '「紗音さんは薔薇庭園に倒れておりました。',
    '「僕が殺すものか！',
    '譲治お兄ちゃんには殺せないね、うー」',
    '「そんなことはないよ。',
    '「でも、いとこ全員も、そして南條先生も返り血は浴びてないね」',
    '「犯人はやはり、マスターキーを持っているのかもしれません…」'
]
translate_pallate = {
    '蔵臼': ('藏臼', '藏臼'),
    '夏妃': ('夏妃', '夏妃'),
    '朱志香': ('朱志香', '朱志香'),
    '南條': ('南条', '南條'),
    '譲治': ('让治', '讓治'),
    '戦人': ('战人', '戰人'),
    '真里亞': ('真里亚', '真里亞'),
    '紗音': ('纱音', '紗音'),
    '嘉音': ('嘉音', '嘉音'),
    '郷田': ('乡田', '鄉田'),
    '熊沢': ('熊泽', '熊澤'),
    '第五・六': ('第五·第六', '第五·第六'),
    'の晩': ('晚', '晚')
}
exefs_convert_pallate = {
    '.@c999.': '@c999.',
    'ひょっとしたら生きてるかもと。': 'ひょっとしたら生きているかもと。',
    '南條先生がすぐ脈を取ったぜ。': '南條先生がすぐに脈を取ったぜ。',
    'ゲストハウス内で南條先生を殺すことは不可能なんだ！@c999.': 'ゲストハウス内で南條先生を殺すことは不可能@c999.なんだ！',
    'うん、@c649.私たち３人に朱志香は殺せない': 'うん。@c649.私たち３人に朱志香は殺せない',
    '食堂内何者かが隠れているということもなかったよ': '食堂内に何者かが隠れているということもなかったよ',
}
offsets = [
    ('0x15bd60', '0x15d6cb'),
    ('0x15d6cb', '0x162c2a'),
    # ('0x15C1DB', '0x15F2F8')
]

# 正则表达式匹配内容
quote_line_pattern = r'^「.*」$'
BRACKET_replaces = {
    r"\{p:42+:(.*?)\}": lambda m: rf"@c649.{m.group(1)}@c999.",  # 紫字
    r"\{p:1:(.*?)\}": lambda m: rf"{m.group(1)}",  # 红字
}
BRACKET_rev_replaces = {
    r"@c649\.": r"{p:42:",
    r"@c999\.": r"}",
    r"@z[0-9]+\.": r"",
    r"@r": r"{n}",
    r"\{n\}\{n\}(?!■)": r"{n}"
}
BRACKET_rev_red = {r"(.*)": lambda m: rf"{{p:1:{m.group(1)}}}"}  # 红字
menu_night_pattern = r'stralias ep8_9_page_(.*)_t,":s;#FFFFFF`\{p:3:(.*)\}"'
menu_chara_pattern = r'stralias chars_bernquiz_(.*),":s;#FFFFFF`\{p:3:(.*)\}"'

# 读取文件并去除每行左右的`
def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        # 读取文件的每一行，并去除每行左右的`
        return [line.lstrip('`').rstrip('`\r\n') for line in file.readlines()]

# 获取特定行号的内容
def get_lines(file_path, line_numbers):
    lines = read_file(file_path)
    # 返回指定行号的内容
    return [lines[i] for i in line_numbers if i < len(lines)]

# 获取jp_pattern中的每一行所在的行号
jp_lines = read_file(jp_file)
jp_num = [i for i, line in enumerate(jp_lines) if line in jp_pattern]

# 获取cn和cht文件中对应行号的内容
cn_pattern = get_lines(cn_file, jp_num)
cht_pattern = get_lines(cht_file, jp_num)

# 通过3个语言的umi8_9.txt生成3个语言的关键内容并存储在变量中
def process_script(input_file, certain):
    lines = read_file(input_file)
    texts = []
    i = 0
    while i < len(lines):
        if purple_code in lines[i] or any(certain in lines[i] for certain in certain):
            # 找到此前最近的行首是「的行
            start = i
            while start >= 0 and not lines[start].startswith('「'):
                start -= 1
            # 找到此后最近的行尾是」的行
            end = i
            while end < len(lines) and not lines[end].endswith('」'):
                end += 1
            if start >= 0 and end < len(lines):
                # 将从start到end的内容放在同一行内
                text = ''.join(lines[start:end+1])
                texts.append(text)
            i = end + 1
        elif red_code in lines[i]:
            # 找到red_code的位置
            start = (i, lines[i].index(red_code))
            # 找到最近的}
            end = start
            while end[0] < len(lines) and '}' not in lines[end[0]][end[1]:]:
                end = (end[0] + 1, 0)
            if end[0] < len(lines) and '}' in lines[end[0]][end[1]:]:
                end = (end[0], lines[end[0]].index('}', end[1]) + 1)
            # 将从start到end的内容放在同一行内
            if start[0] == end[0]:
                text = lines[start[0]][start[1]:end[1]]
            else:
                text = ''.join(lines[start[0]][start[1]:] + ''.join(lines[start[0]+1:end[0]]) + lines[end[0]][:end[1]])
            texts.append(text)
            i = end[0] + 1
        else:
            i += 1
    return texts

# 使用BRACKET_replaces替换文本
def replace_brackets(texts):
    for pattern, repl in BRACKET_replaces.items():
        # 使用正则表达式替换文本
        texts = [re.sub(pattern, repl, text) for text in texts]
    return texts

# 读取exefs_text.txt文件
def read_exefs_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        # 读取文件的每一行，并按制表符分割
        return [line.strip().split('\t') for line in file.readlines()]

# 使用offsets变量的值来确定要读取的行的范围
def get_texts_by_offset(exefs_lines, offsets):
    texts = []
    for start_offset, end_offset in offsets:
        # 找到起始和结束偏移量对应的行号
        start_index = next(i for i, line in enumerate(exefs_lines) if line[0] == start_offset)
        end_index = next(i for i, line in enumerate(exefs_lines) if line[0] == end_offset)
        # 获取对应范围内的文本
        texts.append(exefs_lines[start_index:end_index])
    return texts

# 处理文本替换的通用函数
def process_texts(jp_texts, jp_convert_texts, cn_convert_texts, cht_convert_texts):
    cn_texts = []
    cht_texts = []
    for jp_text in jp_texts:
        cn_text = jp_text
        cht_text = jp_text
        for i, jp_convert_text in enumerate(jp_convert_texts):
            if re.match(quote_line_pattern, jp_convert_text):
                # 完全匹配quote_line_pattern的文本
                if jp_convert_text in jp_text:
                    cn_text = cn_text.replace(jp_convert_text, cn_convert_texts[i])
                    cht_text = cht_text.replace(jp_convert_text, cht_convert_texts[i])
            else:
                # 按句号拆分red_code_line_pattern的文本
                jp_parts = jp_convert_text.split('。')
                cn_parts = cn_convert_texts[i].split('。')
                cht_parts = cht_convert_texts[i].split('。')
                for jp_part, cn_part, cht_part in zip(jp_parts, cn_parts, cht_parts):
                    if jp_part in jp_text:
                        cn_text = cn_text.replace(jp_part, cn_part)
                        cht_text = cht_text.replace(jp_part, cht_part)
        cn_texts.append(cn_text)
        cht_texts.append(cht_text)
    return cn_texts, cht_texts

# 使用translate_pallate匹配并替换文本内容
def translate_texts(texts, translate_pallate, lang):
    for key, value in translate_pallate.items():
        # 替换文本中的特定字符
        texts = [text.replace(key, value[lang]) for text in texts]
    return texts

# 把cn_night_texts和cn_chara_texts写回exefs_texts中相应行的第二部分信息
def update_exefs_texts(exefs_lines, texts, offsets):
    for (start_offset, end_offset), new_texts in zip(offsets, texts):
        # 找到起始和结束偏移量对应的行号
        start_index = next(i for i, line in enumerate(exefs_lines) if line[0] == start_offset)
        end_index = next(i for i, line in enumerate(exefs_lines) if line[0] == end_offset)
        # 更新对应范围内的文本
        for i, new_text in enumerate(new_texts):
            exefs_lines[start_index + i][1] = new_text
    return exefs_lines

# 将更新后的exefs_lines写回文件
def write_exefs_file(file_path, exefs_lines):
    with open(file_path, 'w', encoding='utf-8') as file:
        # 将每一行写回文件
        for line in exefs_lines:
            file.write('\t'.join(line) + '\n')

if __name__ == "__main__":
    # 1. 通过3个语言的umi8_9.txt生成3个语言的关键内容并存储在变量中
    key_texts = {lang: process_script(base_path.format(lang), get_lines(base_path.format(lang), jp_num)) for lang in languages}

    # 2. 通过3个语言的关键内容，来匹配、替换exefs_text.txt
    # 2.1 转换格式
    convert_texts = {lang: replace_brackets(key_texts[lang]) for lang in languages}

    # 2.2 读取exefs_texts中的信息
    exefs_lines = read_exefs_file(exefs_path)
    texts_by_offset = get_texts_by_offset(exefs_lines, offsets)
    night_texts, chara_texts = texts_by_offset

    # 2.3 从night_texts和chara_texts中读取每一个项目的第三项为jp_texts
    jp_texts = {category: [item[2] for item in texts] for category, texts in zip(['night', 'chara'], texts_by_offset)}
    for category in jp_texts:
        for key, value in exefs_convert_pallate.items():
            jp_texts[category] = [text.replace(key, value) for text in jp_texts[category]]

    # 2.4 使用jp_convert_texts中的项目匹配jp_night_text和jp_chara_text，并替换
    cn_texts, cht_texts = {}, {}
    for category in ['night', 'chara']:
        cn_texts[category], cht_texts[category] = process_texts(jp_texts[category], convert_texts['jp'], convert_texts['cn'], convert_texts['cht'])

    # 2.5 使用translate_pallate匹配并替换cn_night_texts和cn_chara_texts的内容
    for category in ['night', 'chara']:
        cn_texts[category] = translate_texts(cn_texts[category], translate_pallate, 0)
        cht_texts[category] = translate_texts(cht_texts[category], translate_pallate, 1)

    # 2.6 使用cn/cht_night/chara_texts的内容，更新menu.txt中的内容
    def update_menu_texts(menu_file, menu_texts):
        # 1. 对(语言)_texts的每一项进行判断
        for category in ['night', 'chara']:
            for i, text in enumerate(menu_texts[category]):        
                # 1.1 使用BRACKET_rev_replaces进行匹配替换
                for pattern, repl in BRACKET_rev_replaces.items():
                    menu_texts[category][i] = re.sub(pattern, repl, menu_texts[category][i])

        # 2. 打开各自语言的(语言)_menu_file
        with open(menu_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # 2.1 使用menu_night_pattern匹配行并替换
        for i, line in enumerate(lines):
            if re.search(menu_night_pattern, line):
                lines[i] = re.sub(menu_night_pattern, lambda m: f'stralias ep8_9_page_{m.group(1)}_t,":s;#FFFFFF`{{p:3:{menu_texts["night"].pop(0)}}}"', line)

        # 2.2 使用menu_chara_pattern匹配行并替换
        for i, line in enumerate(lines):
            if re.search(menu_chara_pattern, line):

                lines[i] = re.sub(menu_chara_pattern, lambda m: f'stralias chars_bernquiz_{m.group(1)},":s;#FFFFFF`{{p:3:{menu_texts["chara"].pop(0)}}}"', line)

        # 3. 保存修改后的该语言版本的menu.txt
        with open(menu_file, 'w', encoding='utf-8') as file:
            file.writelines(lines)

    # 更新cn和cht语言的menu.txt
    update_menu_texts(cn_menu_file, cn_texts)
    update_menu_texts(cht_menu_file, cht_texts)

    # 2.7 更新exefs_lines中的内容
    exefs_lines = update_exefs_texts(exefs_lines, [cn_texts['night'], cn_texts['chara']], offsets)
    write_exefs_file(exefs_path, exefs_lines)


