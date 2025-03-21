HALFWIDTH = "—｢｣ｧｨｩｪｫｬｭｮｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝｰｯ､ﾟﾞ･｡`ゞ"
HALFWIDTH_REPLACE = "―「」ぁぃぅぇぉゃゅょあいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんーっ、？！…。　'，"
trans_table_jp = str.maketrans(HALFWIDTH_REPLACE[:-1], HALFWIDTH[:-1])

def convert_and_print(input_str):
    converted_str = input_str.translate(trans_table_jp)
    print(converted_str)

if __name__ == "__main__":
    input_str = input("输入要转换的文本：")
    convert_and_print(input_str)
