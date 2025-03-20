import os
import re
import sys

# 解决路径问题
os.chdir(os.path.dirname(__file__))
os.chdir('..')

# 路径
JPscript = os.path.abspath("misc/main.rb")  # .rs文件路径
JPoutput_dir = os.path.abspath("story_re_jp")  # 输出文件保存目录
os.makedirs('JPoutput_dir', exist_ok=True)

# 表达式
FILENAME_pattern = r"{EP}_{CH}.txt" # 文件名
# 源文本匹配
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

# 一. 脚本文件读取
with open(JPscript, 'r', encoding='utf-8') as file:
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
        output_path = os.path.join(JPoutput_dir, filename)
        print(output_path)
        
        # 写入文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write("\n".join(content_lines) + "\n")
        
        # 打印生成的文件名
        print(f"生成文件: {filename}")
        
        # 处理完当前章节，移动到下一个章节
        current_chapter_index += 1
    
    # 移动到下一行
    i += 1

print("文件导出完成")