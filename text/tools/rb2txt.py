import os
import re
import sys
import json

# 解决路径问题
os.chdir(os.path.dirname(__file__))
os.chdir('..')

# 路径
JPscript = os.path.abspath("misc/main.rb")  # .rs文件路径
FIXjson = os.path.abspath("misc/script_fix.json")  # 代码修正.json文件路径
REjson = os.path.abspath("misc/script_restore.json")  # 代码反和谐.json文件路径
JP_dir = os.path.abspath("story_jp")  # 输入文件保存目录
JP_RE_dir = os.path.abspath("story_re_jp")  # 输出文件保存目录

# 表达式
FILENAME_pattern = r"{EP}_{CH}.txt" # 文件名
# 源文本匹配
USHORT_pattern = r's\.ins 0x86, ushort\({ushort}\), byte\([01]\), byte\([01]\),'
SCRIPT_pattern = r"s\.ins\s.*byte.*,\s'(.*)'" # 匹配源文本
SCRIPT_EP_pattern = "s.ins 0xa0, byte(0)," # 匹配EP标题
SCRIPT_CH_pattern = "s.ins 0xa0, byte(1)," # 匹配章节标题
EP_TITLE_patterns = {
    r"Episode([1-8]) ": r"umi{num}",
    r"うみねこのなく頃に翼": "tsubasa",
    r"うみねこのなく頃に羽": "hane",
    r"うみねこのなく頃に咲": "saku"
    }
CH_NUM_pattern = r"Story([0-9]+)"

# 括号类
BRACKET_replaces = {
    r"@c900.@\[(.*?)@\]@c.": r"#c900.#<{text}#>#c.",  # 红字
    r"@c279.@\[(.*?)@\]@c.": r"#c279.#<{text}#>#c.",  # 蓝字
    r"@c960.@\[(.*?)@\]@c.": r"#c960.#<{text}#>#c.",  # 金字
    r"@c649.(.*?)@c.": r"#c649.{text}#c.",  # 紫字
    # r"@\{(.*?)@\}": r"{{i:{text}}}",  # @{???@} 粗体
    r"@\[(.*?)@\]": r"\n{text}\n",  # @[???@] 颜色停顿
    r"@\[(.*?)": r"\n{text}\n",  # @[???@] 颜色停顿补漏
    r"@c[0-9]+.(.*?)@c.": r"\n{text}\n",  # @c999.???@c. 颜色字
    # r"@b(.*?).@<(.*?)@>": r"{kanji}",  # @b???@<???@> ruby注音
    }

# 起行类
R_start_pattern = r"@r" # @r 对话开头
ENTER_patterns = [
    r"@[cvwz][a-zA-Z0-9_/|]+\.",  # @v000/_ABC.、@w999. 、@z999. 新起行
    r"@c\.",  # @c. 新起行
    r"@[kty]",  # @k、@t、@y 新起行
    r"@\|@y"  # @|@y 未知新起行
    ]

# 杂项去除类
CODE_pattern = r"@[acvwosz](?:[a-zA-Z0-9_/|])*+\." # @x999/_ABC. 各类杂项长代码
NORMAL_pattern = r"@[cekrtyz|-]" # @x 各类杂项短代码

# 颜色字还原类
r_COLOR_replaces = {
    r"#c([0-9]+).": r"@c{text}.",
    r"#<": r"@[",
    r"#>": r"@]",
    r"#c.": r"@c."
}
# 转换
HALFWIDTH = '｢｣ｧｨｩｪｫｬｭｮｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝｰｯ—､ﾟﾞ･｡ゞ'
HALFWIDTH_REPLACE = '「」ぁぃぅぇぉゃゅょあいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんーっ―、？！…。　，'

def restore_text(target_script, restore_json):
    script_str = "\n".join(target_script)
    for item in restore_json:
        if "pc" in item and not item["pc"].startswith(("text_", "voice_")):
            if "ushort" in item:
                # 单ushort只替换一次
                if re.fullmatch(r"\d+", item["ushort"]):
                    pattern = USHORT_pattern.replace("{ushort}", item["ushort"])
                    match = re.search(pattern, script_str)
                    if match:
                        end_pos = match.end()
                        before = script_str[:end_pos]
                        after = script_str[end_pos:]
                        after = after.replace(item["cs"], item["pc"], 1)
                        script_str = before + after
                # 双ushort替换中间所有内容
                elif re.fullmatch(r"\d+-\d+", item["ushort"]):
                    start_ushort, end_ushort = item["ushort"].split("-")
                    start_pattern = USHORT_pattern.replace("{ushort}", start_ushort)
                    end_pattern = USHORT_pattern.replace("{ushort}", end_ushort)

                    start_match = re.search(start_pattern, script_str)
                    end_match = re.search(end_pattern, script_str)
                    if start_match and end_match:
                        start_pos = start_match.end()
                        end_pos = end_match.start()

                        before = script_str[:start_pos]
                        middle = script_str[start_pos:end_pos]
                        after = script_str[end_pos:]
                        middle = middle.replace(item["cs"], item["pc"])

                        script_str = before + middle + after
            else:
                # 无ushort替换全文所有内容
                script_str = script_str.replace(item["cs"], item["pc"])
    changed_script = script_str.split("\n")
    return changed_script
        
# 一. 脚本文件读取
with open(FIXjson, 'r', encoding='utf-8') as json_file:
    restore_json = json.load(json_file)
with open(REjson, 'r', encoding='utf-8') as json_file:
    restore_json.extend(json.load(json_file))

with open(JPscript, 'r', encoding='utf-8') as file:
    file = [line.strip() for line in file.readlines()]
    file = restore_text(file, restore_json)

    SCRIPT_lines = []
    CHAPTER_map = []
    EP_history= ""
    # 1. 读取
    for line in file:
        if match := re.search(SCRIPT_pattern, line):
            text = match.group(1)
            SCRIPT_lines.append(text)
            # 2. 得到EP序号
            if SCRIPT_EP_pattern in line:
                for pattern, replace in EP_TITLE_patterns.items():
                    if EP_match := re.search(pattern, text):
                        EP = re.sub(pattern + r"(.*)", lambda m: replace.format(num=m.group(1)), text)
                if text != EP_history:
                    CH = -1
                EP_history = text
            # 2. 得到章节序号
            elif SCRIPT_CH_pattern in line:
                if CH_match:= re.search(CH_NUM_pattern, text): # 如果是外传
                    CH = int(CH_match.group(1))
                else: # 如果是正篇或茶会   
                    CH += 1
                CHAPTER_map.append(((text, EP, CH)))
                    
# 二. 文本处理
PARSE_lines = []
for script_line in SCRIPT_lines:
    # 1. 粗处理（保留代码（括号类除外））
    ROUGH_lines = []
    rough_line = script_line
    # 1-1. @c、@b、BOLD 括号类整体去除
    for pattern, replace in BRACKET_replaces.items():
        if r"kanji" in replace:
            rough_line = re.sub(pattern, lambda m: replace.format(ruby=m.group(1), kanji=m.group(2)), rough_line)
        else:
            rough_line = re.sub(pattern, lambda m: replace.format(text=m.group(1)), rough_line)
    
    # 1-2. @r 处理对话开头
    R_match = re.search(R_start_pattern, rough_line)
    if R_match:
        rough_line = rough_line[R_match.start():]

    # 1-3. @k、@v、@w、@|@y 处理其余新起行
    segments = re.split(f"({'|'.join(ENTER_patterns)})", rough_line)

    # 1-4. 过滤空字符串并添加到 ROUGH_lines
    ROUGH_lines.extend(filter(None, segments))

    # 2. 精处理（去除代码）
    FINE_lines = []

    i = 0
    while i < len(ROUGH_lines):
        fine_line = ROUGH_lines[i]
        # 2-1. 去除行首行尾代码
        previous_fine_line = None
        while fine_line != previous_fine_line:
            # 保存上一次的 fine_line
            previous_fine_line = fine_line
            for r in range (0, 1):
                # 处理 CODE_pattern
                fine_line = re.sub(f"^(｢?)" + CODE_pattern, lambda m: m.group(1), fine_line)           
                # 处理 NORMAL_pattern
                fine_line = re.sub(f"^(｢?)" + NORMAL_pattern, lambda m: m.group(1), fine_line)
                fine_line = re.sub(NORMAL_pattern + f"$", "", fine_line)

        # 2-x. 还原颜色字代码
        for pattern, replace in r_COLOR_replaces.items():
            if r"text" in replace:
                fine_line = re.sub(pattern, lambda m: replace.format(text=m.group(1)), fine_line)
            else:
                fine_line = re.sub(pattern, replace, fine_line)
            
        # 2-2. 切割包含 '\n' 的行
        if '\\n' in fine_line:
            split_lines = fine_line.split('\\n')
            # 在切割后，需要在ROUGH_lines中插入切割出来的行
            ROUGH_lines[i:i+1] = split_lines  # 替换当前行并插入新行
            fine_line = ROUGH_lines[i]

        # 2-3. 单行空格接到下一行
        if re.fullmatch("()+", fine_line):
            fine_line = ""
            # try:
            #     ROUGH_lines[i + 1] = "" + ROUGH_lines[i + 1]
            # except IndexError:
            #     pass

        if fine_line:
            FINE_lines.append(fine_line)
        i += 1

    PARSE_lines.extend(FINE_lines)

# 三. 半角转换处理
CONVERTED_lines = []
translation_table = str.maketrans(HALFWIDTH, HALFWIDTH_REPLACE)
CONVERTED_lines = [parse_line.translate(translation_table) for parse_line in PARSE_lines]

# 四. 遍历目录，并生成对应的文件
remaining_chapters = list(CHAPTER_map)  # 按顺序处理章节
current_chapter_index = 0
i = 0
num_lines = len(CONVERTED_lines)

while i < num_lines and current_chapter_index < len(remaining_chapters):
    line = CONVERTED_lines[i]

    # 处理当前章节
    chapter, ep, ch = remaining_chapters[current_chapter_index]
    
    # 查找当前章节标题行
    if line == chapter:
        start_index = i + 1  # 从章节标题行的下一行开始
        end_index = num_lines  # 默认到文件末尾
        
        # 查找下一章节的起始行
        while current_chapter_index + 1 < len(remaining_chapters):
            next_chapter = remaining_chapters[current_chapter_index + 1][0]
            if next_chapter in CONVERTED_lines:
                next_index = CONVERTED_lines.index(next_chapter, i + 1)
                if next_index > start_index:
                    end_index = next_index
                    break
            else:
                break
        
        # 提取当前章节内容
        content_lines = CONVERTED_lines[start_index:end_index]
        
        # 排除 EP_TITLE_patterns 的匹配行
        content_lines = [line for line in content_lines if not any(re.search(pattern, line) for pattern in EP_TITLE_patterns.keys())]
        
        # 文件名格式化
        filename = FILENAME_pattern.format(EP=ep, CH=ch)
        output_path = os.path.join(JP_RE_dir, filename)
        existing_file_path = os.path.join(JP_dir, filename)
        print(output_path)


        # 检查现有文件是否存在并读取内容
        if os.path.exists(existing_file_path):
            with open(existing_file_path, 'r', encoding='utf-8') as existing_file:
                existing_content = existing_file.read()
        else:
            existing_content = None

        # 准备新内容
        new_content = "\n".join(content_lines) + "\n"

        # 比较内容，如果不一致则写入新文件
        if existing_content != new_content:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"生成文件: {filename}")
        else:
            print(f"文件未变化: {filename}")

        # # 写入文件
        # os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # with open(output_path, 'w', encoding='utf-8') as file:
        #     file.write("\n".join(content_lines) + "\n")
        
        # # 打印生成的文件名
        # print(f"生成文件: {filename}")
        
        # 处理完当前章节，移动到下一个章节
        current_chapter_index += 1
    
    # 移动到下一行
    i += 1

print("文件导出完成")