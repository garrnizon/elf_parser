# **Описание:**

Программа-транслятор (дизассемблер), с помощью которой можно преобразовывать машинный код (извлеченный из elf-файла) в текст программы на языке ассемблера. 
Поддерживается набор команд RISC-V: RV32I, RV32M, RV32A, расширения Zifence, Zihintpause


# **Инструментарий:**

Python 3.11.5

# **Пример использования:**

Аргументы программе передаются через командную строку:
```
python3 main.py <имя_входного_elf_файла> <имя_выходного_файла>
```

Возможный вывод программы:

```
.text

00010074 	<main>:
   10074:	ff010113	   addi	sp, sp, -16
   10078:	00112623	     sw	ra, 12(sp)
   1007c:	030000ef	    jal	ra, 0x100ac <mmul>
   10080:	00c12083	     lw	ra, 12(sp)
   10084:	00000513	   addi	a0, zero, 0
   10088:	01010113	   addi	sp, sp, 16
   1008c:	00008067	   jalr	zero, 0(ra)
   10090:	00000013	   addi	zero, zero, 0
   10094:	00100137	    lui	sp, 0x100
   10098:	fddff0ef	    jal	ra, 0x10074 <main>
   1009c:	00050593	   addi	a1, a0, 0
   100a0:	00a00893	   addi	a7, zero, 10
   100a4:	0ff0000f	  fence	iorw, iorw
   100a8:	00000073	  ecall

000100ac 	<mmul>:
   100ac:	00011f37	    lui	t5, 0x11
   100b0:	124f0513	   addi	a0, t5, 292
   100b4:	65450513	   addi	a0, a0, 1620
   100b8:	124f0f13	   addi	t5, t5, 292
   100bc:	e4018293	   addi	t0, gp, -448
   100c0:	fd018f93	   addi	t6, gp, -48
   100c4:	02800e93	   addi	t4, zero, 40

000100c8 	<L2>:
   100c8:	fec50e13	   addi	t3, a0, -20
   100cc:	000f0313	   addi	t1, t5, 0
   100d0:	000f8893	   addi	a7, t6, 0
   100d4:	00000813	   addi	a6, zero, 0

000100d8 	<L1>:
   100d8:	00088693	   addi	a3, a7, 0
   100dc:	000e0793	   addi	a5, t3, 0
   100e0:	00000613	   addi	a2, zero, 0

000100e4 	<L0>:
   100e4:	00078703	     lb	a4, 0(a5)
   100e8:	00069583	     lh	a1, 0(a3)
   100ec:	00178793	   addi	a5, a5, 1
   100f0:	02868693	   addi	a3, a3, 40
   100f4:	02b70733	    mul	a4, a4, a1
   100f8:	00e60633	    add	a2, a2, a4
   100fc:	fea794e3	    bne	a5, a0, 0x100e4, <L0>
   10100:	00c32023	     sw	a2, 0(t1)
   10104:	00280813	   addi	a6, a6, 2
   10108:	00430313	   addi	t1, t1, 4
   1010c:	00288893	   addi	a7, a7, 2
   10110:	fdd814e3	    bne	a6, t4, 0x100d8, <L1>
   10114:	050f0f13	   addi	t5, t5, 80
   10118:	01478513	   addi	a0, a5, 20
   1011c:	fa5f16e3	    bne	t5, t0, 0x100c8, <L2>
   10120:	00008067	   jalr	zero, 0(ra)

.symtab

Symbol Value              Size Type     Bind     Vis       Index Name
[   0] 0x0                   0 NOTYPE   LOCAL    DEFAULT   UNDEF 
[   1] 0x10074               0 SECTION  LOCAL    DEFAULT       1 
[   2] 0x11124               0 SECTION  LOCAL    DEFAULT       2 
[   3] 0x0                   0 SECTION  LOCAL    DEFAULT       3 
[   4] 0x0                   0 SECTION  LOCAL    DEFAULT       4 
[   5] 0x0                   0 FILE     LOCAL    DEFAULT     ABS test.c
[   6] 0x11924               0 NOTYPE   GLOBAL   DEFAULT     ABS __global_pointer$
[   7] 0x118F4             800 OBJECT   GLOBAL   DEFAULT       2 b
[   8] 0x11124               0 NOTYPE   GLOBAL   DEFAULT       1 __SDATA_BEGIN__
[   9] 0x100AC             120 FUNC     GLOBAL   DEFAULT       1 mmul
[  10] 0x0                   0 NOTYPE   GLOBAL   DEFAULT   UNDEF _start
[  11] 0x11124            1600 OBJECT   GLOBAL   DEFAULT       2 c
[  12] 0x11C14               0 NOTYPE   GLOBAL   DEFAULT       2 __BSS_END__
[  13] 0x11124               0 NOTYPE   GLOBAL   DEFAULT       2 __bss_start
[  14] 0x10074              28 FUNC     GLOBAL   DEFAULT       1 main
[  15] 0x11124               0 NOTYPE   GLOBAL   DEFAULT       1 __DATA_BEGIN__
[  16] 0x11124               0 NOTYPE   GLOBAL   DEFAULT       1 _edata
[  17] 0x11C14               0 NOTYPE   GLOBAL   DEFAULT       2 _end
[  18] 0x11764             400 OBJECT   GLOBAL   DEFAULT       2 a   
```


# Описание кода:

## constants.py

Этот файл содержит почти все необходимые константы.

### Константы `e_*`, `sh_*` и `st_*`

Информация про константы `e_*`, `sh_*` : [https://ru.wikipedia.org/wiki/Executable_and_Linkable_Format](https://ru.wikipedia.org/wiki/Executable_and_Linkable_Format)

Про `st_*`: [https://docs.oracle.com/cd/E23824_01/html/819-0690/chapter6-79797.html](https://docs.oracle.com/cd/E23824_01/html/819-0690/chapter6-79797.html)

константы для заголовка elf файла, заколовков секций и символов.

эти константы содержат просто строки. Далее эти строки будут использоваться как ключи словарей, чтобы по этим ключам получать значения, соответствующие этим константам.

### Константы `*_fields` и `*_sizes`

используются для парсинга

### Константы `symbol_*`

 [https://docs.oracle.com/cd/E23824_01/html/819-0690/chapter6-79797.html](https://docs.oracle.com/cd/E23824_01/html/819-0690/chapter6-79797.html)

Эти константы - словари, которые по численным значениям (беруться из битового представления команды, выбирая нужные подотрезки) возвращают строку, которую нужно вывести в соответствии с этим полем.

### `regs`
![regs.png](pictures%2Fregs.png)
по численном значению регистра выводит соответсвующий регистр.

### `instruction_types`

По последним 6 битам (opcode) возвращает тип инструкции, который будет далее использоваться для вывода. 

Для этого использовал следующий [материал](https://github.com/jameslzhu/riscv-card/blob/master/riscv-card.pdf)

![rv32i.png](pictures%2Frv32i.png)

![rv32m.png](pictures%2Frv32m.png)

![rv32a.png](pictures%2Frv32a.png)

### `patterns`

Описание этой переменной будет дано в разделе Инструкции. 

## main.py

### РАЗНОЕ

### `class Values`

Создается только один экземпляр класса (переменная `v`) - сделано для более удобного хранения часто используемых переменных, которые вычисляются по ходу программы.

### `def decoder_le`

decode little endian - декодирует несколько битов в соответствии правилу little endian

### `def make_header_values`

[https://ru.wikipedia.org/wiki/Executable_and_Linkable_Format](https://ru.wikipedia.org/wiki/Executable_and_Linkable_Format)

Получение значений переменных `e_*`, эти значения будут хранится в словаре `h_values`, по соответствующим ключам `e_*`

### `def get_name_by_start`

Эта функция считывает байты по одному, пока не встретит нулевой.

Каждый прочитанный ненулевой - соответствует какому-то символу ASCII, и функция возвращает объединенные в строку эти симфолы.

### СЕКЦИИ:

[https://ru.wikipedia.org/wiki/Executable_and_Linkable_Format](https://ru.wikipedia.org/wiki/Executable_and_Linkable_Format)

### `def make_sh_values`

Парсинг заголовков секций, добавление секций в массив `sections`

Каждому заголовку секции - отдельный экземпляр класса.

### `class Section`

Используя `decoder_le`, получает необходимые поля из заголовка секций (`sh_*`) - они хранятся в словаре `values`, где ключами как раз используются константы `sh_*` о которых говорилось ранее.

Эти значения получаются при декодировке байтов elf файла.

Также хранит имя этой секции - `name` - которое заполняется в функции `make_sh_names`.

### `def make_sh_names`

Для каждой секции получает ее имя с помощью уже описанной функции `get_name_by_start`, start находится в блягодаря значению `e_shstrndx`, как раз созданного для этой цели.

### СИМВОЛЫ

[https://docs.oracle.com/cd/E23824_01/html/819-0690/chapter6-79797.html](https://docs.oracle.com/cd/E23824_01/html/819-0690/chapter6-79797.html)

### `class Symbol`

Хранит необходимые поля из заголовка секций (`st_*`) - они хранятся в словаре с названием `values`, где ключами также используются константы `sh_*` о которых говорилось ранее.

Эти значения также получаются при декодировке байтов elf файла.

Также имеются поля `bind`, `type`, `vis`, `shndx` - которые вычисляются из уже имеющихся, в соответсвии с информацией на уже упоминаемом сайте.

Также хранит имя этой секции - `name` - которое заполняется в функции `make_st_values`.

Имеет метод `__str__` - идет преобразование в строку для **.symtab**.

### `def make_st_values`

Поочередное создание символов, вычисление их имён (с помощью функции `get_name_by_start`), и добавление символов в список `symbols`. Также создание меток - если тип символа - функция или переменная, к которым могу позднее обратится. Метки хранятся в словаре `markers`.

### ИНСТРУКЦИИ

### `def fence_args`

Фуункция вычисляет необходимые аргументы (`pred` и `succ`) для инструкции fence 

Принимает строку из 8 битов - возвращает необходимые комбинации iorw для `pred` и `succ` соответственно.

### `class Instruction`

[https://msyksphinz-self.github.io/riscv-isadoc/html/rvi.html#lui](https://msyksphinz-self.github.io/riscv-isadoc/html/rvi.html#lui)
Основную информацию я брал с этого сайта, так же иногда примегал к следующему материалу: https://drive.google.com/file/d/1s0lZxUZaa7eV_O0_WsZzaurFLLww7ou5/view

`patterns`

Это переменная из файла constants.py, было обещано ее описание.

Мне было лень писать 10000 if’ов, чтобы понять, что за инструкция по ее битовому представлению. А на вышеупомянутом [сайте](https://msyksphinz-self.github.io/riscv-isadoc/html/rvi.html#lui) для каждого символа есть табличка, с “шаблоном” для каждой инструкции. Написаны номера битов, и что в них должно находится.
Более того, по кнопочке `[View page source](https://msyksphinz-self.github.io/riscv-isadoc/html/_sources/rvi.rst.txt)` можно найти текстовое представление страницы.

Ну и я подумал - а почему бы мне не распарсить информацию из этого сайта, и не вставить ее просто в код (так и появилась переменная `patterns`).

Код для парсинга будет сейчас приложен.

(я решил не добавлять его в репозиторий, потому что для его использования еще надо будет создать текстовый файл с текстовыми данными с сайта (через питон пока не умею такое делать автоматически) - а это засорение репозитория, поэтому просто приложу здесь - а содержимое текстового файла - в точности ctrl+c - ctrl+v)

```python
with open("commands.txt", 'r') as f:
    txt = [ln.strip() for ln in f.readlines()]

start = 0
end = 2
txt.append('------')

def get_ith_col(s, k):
    n = 0
    for i in range(len(s)):
        if s[i] == '|':
            n += 1
        if n == k:
            return i

out = []

while end < len(txt):
    begin = start
    if begin == 1501:
        pass
    while not txt[end] or txt[end] != ":Format:":
        end += 1
    end += 1

    args = tuple(("".join(txt[end].split()[2:])).split(','))

    while not txt[end] or any([(c != '-') for c in txt[end]]):
        end += 1

    end -= 1

    while '+' not in txt[start]:
        start += 1
    nums = txt[start + 1]
    data = txt[start + 3]
    res = []
    parts = [p.strip() for p in data.split('|')]
    for i in range(1, len(parts) - 1):
        if not parts[i]:
            continue

        if all([(c in '01 ') for c in parts[i]]):
            pos2 = get_ith_col(data, i + 1)
            pos1 = get_ith_col(data, i)
            ns = nums[pos1 + 1: pos2].strip().split('-')
            assert len(ns) == 2

            res.append((int(ns[1]), int(ns[0]), parts[i]))

    out.append([res, txt[begin], args])

    start = end
    end = start + 3

print(out)

```

На выходе получается список шаблонов, отедельно для каждой инструкции - который я просто скопировал и вставил как значение переменной `patterns`.

Один шаблон выглядит так:

- список tuple’ов, которые задают начальный и конечный индексы, строку, которая должны быть на подстроке с этими концами. Этот tuple использует функция
    
    `def _is_instruction_fit_pattern` которая как раз проверяет, что у предполагаемой инструкции на нужных местах - нужные строи.
    
- строковое представление функции.
- Используется для вывода (не всегда):
tuple из нескольких строк, которые соответсвуют аргументам, которые должны выводиться. В классе `Instructions` я назвал необходимые поля в точности как и на сайте, что с помощью встроенно функции getattr() получить знчение поля по её строковому представлению.

Таким образом, эта переменная мне поможет не только определить что за строка, но и поможет в выводе инструкций

`def _get_instruction_name_and_args`

Пробегается по всем шаблонам и ищет подходящий. Если его нет - делает инструкцию invalid.

`def _decode`

декодировка чисел, хранящихся в дополнении до двух

`def __slice__`

так как в little endian биты нумеруются справа налево - иногда удобнее обращать с к ним по этим же самым индексам - и эта фаункция помогает с этим справиться

`def __init__`

- получение бинарного представления с помощью `decoder_le`
- Используя `def _get_instruction_name_and_args` получаем имя и аргументы
- получение типа функции с помощью словаря `instruction_types`.
- В соответствии с таблицей из [документации](https://github.com/jameslzhu/riscv-card/blob/master/riscv-card.pdf) вычисляем значения rd, rs1, rs2, shamt (для функций slli, srli, srai)
    ![instrs.png](pictures%2Finstrs.png)
    
- Далее, в соответствии с таблице вычисляется imm и декодируется с помощью `_decode`.

`def __str__`

Перевод инструкции в строку для вывода.

- Сперва проверка, что инструкция инвалидная
- Проверка, нужно ли выводить строку с меткой
- разбираются разные особенные случаи
- Когда остались только функции с 2 или 3 аргументами - используем `pattern` (как раз 3 элемент каждого шаблона - названия необходимых аргументов для вывода).
- (использовать `pattern` для вывода додумался только в конце - поэтому использовал его не так часто, хотя в теории можно бы еще и некоторые особые случаи с ним отработать)

### `def make_instructions`

Создает инструкции, добавляет их в список `instructions`.

Также вычисляет предполагаемый адрес перехода (`idx`), и если нынешняя инструкция - j или b типа - то проверяет, есть ли метка с помеченным адресом, и если нет - добавляет метку `L%i`.

### ВЫВОД и main

### `def print_`

В классе Values есть поле output - массив, в котором будут храниться строки, которые надо будет вывести.

И эта функци добавляет очередную строки в конец этого массива.

### `def print_instructions`

Вывод секции **.text**. Поочередный вывод всех инструкий.

Стоит указать, что строки с *метками* выводятся сразу вместе с последующей инструкцией - сделано так, потому что у этих двух строк одинаковый адрес. 

### `def print_symtab`

Вывод секции **.symtab**. Сначала вывод заколовка, далее поочередный вывод всех символов.

### `get_section_index_by_name`

Пробегается по всем секция и возвращает идекс необходимой секции в массиве `sections`.

### `def main`

- Содержит проверку аргументов, обработку ошибок работы с файлами, извлечение байтов из elf файла.
- вызов функций `make_header_values`, `make_sh_values`, `make_sh_names`.
- Нахождение секций **.text**, **.symtab**, **.strtab** с помощью функции `get_section_index_by_name`.
- вызов функций `make_st_values`, `make_instructions`, `print_instructions`, `print_symtab`.
- запись результата в файл.

## Про реализации RV32I,M,A, Zifence, Zihintpause

IMA: это просто команды, я взял их с [сайта](https://msyksphinz-self.github.io/riscv-isadoc/html/rvi.html#lui) и распарсил. 

Zifence: [https://five-embeddev.com/riscv-isa-manual/latest/zifencei.html#chap:zifencei](https://five-embeddev.com/riscv-isa-manual/latest/zifencei.html#chap:zifencei)

это команда fence.i - она тоже есть на этом сайте - для ее вывода отдельный if:

```python
if self.type == "i4" or self.name == "fence.i":  # zifence
    return result + '\n'
```

Zihintpause: [https://five-embeddev.com/riscv-isa-manual/latest/zihintpause.html#chap:zihintpause](https://five-embeddev.com/riscv-isa-manual/latest/zihintpause.html#chap:zihintpause)

Это частный случай команды fence - тоже дополнительный if:

```python
if fa[0] == "w" and fa[1] == "":  # zihintpuse
    return result + "%7s\n" % "pause"
```