import os
import re
import shutil
import unicodedata
from itertools import chain

# 解决路径问题
os.chdir(os.path.dirname(__file__))
os.chdir('..')

# 指定路径
cn_path = 'story_cn'
jp_path = 'story_jp'
chap_path = 'misc/chapters.txt'
output_path = '../replace_chars.txt'

# 待改字体库
f_medium_lib = "f_medium"
f_bold_lib = "f_bold"
f_system_lib = "f_system"

# Chapters额外字段
chap_ex = ["选项", "汝是否要将猫杀死", "轻"] # 为防止字符错位而加入“轻”

# 特殊标点转换
other_map = {
    "，": "ゞ",
    ".": "〕",
}
# 不属于GB2312、Shift-JIS范围的字符
add_set = ['呣', '呴', '咘', '咜', '哱', '唦', '唭', '啨', '啰', '喼', '嗙', '嗞', '嗰', '嘡', '瘆', '祂', '觍']


# 读取文件
def read_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# 读取字符
def read_characters(input_data):
    unique_chars = set()
    if isinstance(input_data, list):
        for item in input_data:
            if os.path.isfile(item):  # 如果是文件路径
                text = read_text(item)
                # 过滤掉换行符
                filtered_text = text.replace('\n', '').replace('\r', '')
                unique_chars.update(filtered_text)
            else:  # 如果是文本
                unique_chars.update(item)
    elif isinstance(input_data, str):  # 如果是单个文本
        unique_chars.update(input_data)
    return sorted(list(unique_chars))

# 过滤为汉字
def filter_chinese(char_list):
    chinese_characters = [char for char in char_list if re.match(r'^[\u4e00-\u9fa5]$', char)]
    return chinese_characters

# 生成GB2312、Shift-JIS、Big5、（GBK）字符集
def chars_set():
    # ASCII字符
    ascii_chars = ''.join(chr(i) for i in range(32, 127))

    # 非中文字符
    nonchinese_chars = set()
    for code in range(0x0000, 0x10FFFF + 1):  # Unicode 全范围
        char = chr(code)
        try:
            # 检查字符是否是 CJK UNIFIED IDEOGRAPH
            if not unicodedata.name(char).startswith("CJK UNIFIED IDEOGRAPH"):
                nonchinese_chars.add(char)
        except ValueError:
            # 忽略没有名字的字符
            nonchinese_chars.add(char)

    # GB2312范围：第一字节0xA1 - 0xF7，第二字节0xA1 - 0xFE
    gb2312_chars = set()
    for lead in range(0xA1, 0xF7 + 1):
        for trail in range(0xA1, 0xFE + 1):
            try:
                char = bytes([lead, trail]).decode('gb2312')
                gb2312_chars.add(char)
            except UnicodeDecodeError:
                continue

    # Shift-JIS范围：第一字节0x81 - 0x9F, 0xE0 - 0xEF，第二字节0x40 - 0x7E, 0x80 - 0xFC
    shiftjis_chars = set()
    for lead in chain(range(0x81, 0x9F + 1), range(0xE0, 0xEF + 1)):
        for trail in chain(range(0x40, 0x7E + 1), range(0x80, 0xFC + 1)):
            if trail == 0x7F:
                continue
            try:
                char = bytes([lead, trail]).decode('shift-jis')
                shiftjis_chars.add(char)
            except UnicodeDecodeError:
                continue
    for lead in range(0xF0, 0xFC + 1):
        for trail in chain(range(0x40, 0x7E + 1), range(0x80, 0xFC + 1)):
            if trail == 0x7F:
                continue
            try:
                char = bytes([lead, trail]).decode('shift-jis')
                shiftjis_chars.add(char)
            except UnicodeDecodeError:
                continue
    
    # Big5范围：第一字节0xA1 - 0xF9，第二字节0x40 - 0x7E, 0xA1 - 0xFE
    big5_chars = set()
    for lead in range(0xA1, 0xF9 + 1):
        for trail in chain(range(0x40, 0x7F), range(0xA1, 0xFE + 1)):
            try:
                char = bytes([lead, trail]).decode("big5")
                big5_chars.add(char)
            except UnicodeDecodeError:
                continue

    # GBK范围：第一字节0x81 - 0xFE，第二字节0x40 - 0xFE
    gbk_chars = set()
    for lead in range(0x81, 0xFE + 1):
        for trail in range(0x40, 0xFE + 1):
            if trail == 0x7F:  # 跳过无效组合
                continue
            try:
                char = bytes([lead, trail]).decode("gbk")
                gbk_chars.add(char)
            except UnicodeDecodeError:
                continue

    # 上标字符范围：
    superscript_chars = set()
    for code in [0x00B2, 0x00B3, 0x00B9, 0x2070] + list(range(0x2074, 0x2079 + 1)):
        char = chr(code)
        superscript_chars.add(char)

    # GBK中存在，Shift-JIS中不存在的字符
    replace_chars = sorted(list(gbk_chars.union(superscript_chars) - shiftjis_chars))
    # 所有字符集
    charset = gb2312_chars.union(shiftjis_chars).union(nonchinese_chars)
    charset_list =  sorted(list(charset))
    # Shift-JIS + ASCII中存在，GB2312、Big5中不存在的字符
    charset_list2 = sorted(list(shiftjis_chars.union(ascii_chars) - gb2312_chars - big5_chars))
    # Shift-JIS + ASCII 字符集
    charset_list3 = sorted(list(shiftjis_chars.union(ascii_chars)))

    return(replace_chars, charset_list, charset_list2, charset_list3)

# unicode转十进制
def unicode_10(string_list):
    result = []
    for string in string_list:
        result.extend([ord(char) for char in string])
    return result


# 开始输入
mode = int(input("请选择模式 (0: 导出replace_chars , 1: 显示文本中多余字符，2: chapters字符转换)："))
if mode == 2:
    f_lib_path = input("请输入3个字体库母文件夹路径（如不需要生成则直接回车）：")

if mode == 0:
    text_set = chars_set()[mode]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # 保存到文件
    with open(output_path, "w", encoding="utf-8") as file:
        for item in text_set:
            file.write(item + "\n")

elif mode in [1, 2]:
    # 获取文件路径
    file_paths = []
    file_paths.extend([os.path.join(cn_path, file) for file in os.listdir(cn_path) if file.endswith('.txt')])
    file_paths.extend([os.path.join(jp_path, file) for file in os.listdir(jp_path) if file.endswith('.txt')])

    # 获取指定字符集中的字符
    text_set = chars_set()[mode]
    chap_text_set = chars_set()[3]

    # 读取指定文本中的字符
    text = read_characters(file_paths)
    chap_text = read_characters([chap_path])
    chap_text.extend(read_characters(chap_ex))
    print(chap_text)

    if mode == 1:
        extra_chars = sorted(set(text) - set(text_set))
        extra_uni = unicode_10(extra_chars)
        # print超出范围的字符
        print(f"超出范围的字符:\n{''.join(extra_chars)}")
        print(" ".join(map(str, extra_uni)))
        print(f"add_set = {extra_chars}" )

    elif mode == 2:
         # Shift-JIS ( - GB2312 - Big5) 中存在，文本中不存在的字符
        extra_chars = sorted(set(text_set) - set(text))
        extra_uni = unicode_10(extra_chars)
         # Chapters中存在，Shift-JIS中不存在的字符
        chap_extra_chars = sorted(set(chap_text) - set(chap_text_set))
        chap_extra_uni = unicode_10(chap_extra_chars)

        # 从后向前截取长度等于chap_extra_chars长度的项目
        convert_extra_chars = extra_chars[-len(chap_extra_chars):]
        convert_extra_uni = extra_uni[-len(chap_extra_chars):]

        # print要转换的字符
        print(f"Chapters待转换字符:\n{''.join(chap_extra_chars)}")
        print(f"Chapters转换后字符:\n{''.join(convert_extra_chars)}")

        # 字体转换
        if f_lib_path.strip():
            # 建立转换表
            chars_map = {chap_char: convert_char for chap_char, convert_char in zip(chap_extra_chars, convert_extra_chars)}
            uni_map = {str(chap_uni): str(convert_uni) for chap_uni, convert_uni in zip(chap_extra_uni, convert_extra_uni)}
            # 添加特殊标点转换
            chars_map.update(other_map) 
            uni_map.update({str(ord(k)): str(ord(v)) for k, v in other_map.items()})
            # 替换字体文件夹
            font_libs = [os.path.join(f_lib_path, f_medium_lib), os.path.join(f_lib_path, f_bold_lib), os.path.join(f_lib_path, f_system_lib)]
            for font_lib in font_libs:
                for folder in os.listdir(font_lib):
                    if folder.startswith("glyph_"):
                        # 提取文件夹名称中的“unicode”部分
                        parts = folder.split('_', 2)
                        uni_part = parts[1]
                        other_part = parts[2] if len(parts) > 2 else ""
                        # 根据uni_map匹配
                        if uni_part in uni_map:
                            # 使用该key对应的value，匹配库中每个文件夹的“unicode”部分
                            value = uni_map[uni_part]
                            for folder_to_check in os.listdir(font_lib):
                                if folder_to_check.startswith("glyph_"):
                                    check_parts = folder_to_check.split('_', 2)
                                    check_uni_part = check_parts[1]
                                    if check_uni_part == value:
                                        # 删除value匹配到的文件夹
                                        delete_folder = os.path.join(font_lib, folder_to_check)
                                        shutil.rmtree(delete_folder)
                                        break
                            # 复制key匹配到的文件夹（以及文件夹包含的所有内容）
                            src_folder = os.path.join(font_lib, folder)
                            dest_folder = os.path.join(font_lib, f"glyph_{value}_{other_part}")
                            shutil.copytree(src_folder, dest_folder)

                            print(f"已将{src_folder}，")
                            print(f"复制为{dest_folder}。")