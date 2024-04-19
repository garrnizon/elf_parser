import sys
from constants import *


class Values:

    h_values = {}
    sections = []
    symbols = []
    instructions = []
    markers = {}
    not_named_markers_index = 0
    output = []

    def get(self, name):
        return self.h_values[name]


v = Values()


def decoder_le(b):
    res = 0

    for i in range(len(b) - 1, -1, -1):
        res *= 2 ** 8
        res += b[i]

    return res


def make_header_values(rb):
    ind = 0
    for i in range(len(h_fields)):
        end = ind + h_fields_sizes[i]
        v.h_values[h_fields[i]] = decoder_le(rb[ind: end])
        ind = end


def get_name_by_start(rb, start):
    stop = start
    while rb[stop] != 0:
        stop += 1
    return "".join([chr(i) for i in rb[start: stop]])


class Section:
    def __init__(self, rb):
        assert len(rb) == 40, f"{len(rb)}"
        chunks = [decoder_le(rb[i: i + sh_sizes]) for i in range(0, len(rb), sh_sizes)]
        self.values = dict(zip(sh_fields, chunks))
        self.name = ""


def make_sh_values(rb):
    for sh_index in range(v.get(e_shoff), v.get(e_shnum) * v.get(e_shentsize) + v.get(e_shoff), v.get(e_shentsize)):
        section = Section(rb[sh_index: sh_index + v.get(e_shentsize)])
        v.sections.append(section)


def make_sh_names(rb):
    shstrtab = v.sections[v.get(e_shstrndx)]
    for section in v.sections:
        section.name = get_name_by_start(rb, section.values[sh_name] + shstrtab.values[sh_offset])


class Symbol:
    def __init__(self, rb):
        assert len(rb) == sum(symtab_sizes)
        self.values = {}
        self.name = ""

        begin = 0
        for i in range(len(symtab_sizes)):
            end = begin + symtab_sizes[i]
            self.values[symtab_fields[i]] = decoder_le(rb[begin: end])
            begin = end

        self.bind = symbol_binds[self.values[st_info] // 2 ** 4]
        self.type = symbol_types[self.values[st_info] & 15]
        self.vis = symbol_vis[self.values[st_other] & 3]
        self.shndx = symbol_shndx.get(self.values[st_shndx], str(self.values[st_shndx]))

    def __str__(self, i=0):
        return "[%4i] 0x%-15X %5i %-8s %-8s %-8s %6s %s\n" % (
            i,
            self.values[st_value],
            self.values[st_size],
            self.type,
            self.bind,
            self.vis,
            self.shndx,
            self.name
        )


def make_st_values(rb, symtab_s: Section, strtab_s: Section):

    size_of_one_symbol = symtab_s.values[sh_entsize]
    offset = symtab_s.values[sh_offset]

    for start_index in range(offset, offset + symtab_s.values[sh_size], size_of_one_symbol):
        symbol = Symbol(rb[start_index: start_index + size_of_one_symbol])
        symbol.name = get_name_by_start(rb, symbol.values[st_name] + strtab_s.values[sh_offset])

        if symbol.type == "OBJECT" or symbol.type == "FUNC":
            v.markers[symbol.values[st_value]] = symbol.name
        v.symbols.append(symbol)


def fence_args(s: str):
    assert len(s) == 8

    pred = 'i' * int(s[7]) + 'o' * int(s[6]) + 'r' * int(s[5]) + 'w' * int(s[4])
    succ = 'i' * int(s[3]) + 'o' * int(s[2]) + 'r' * int(s[1]) + 'w' * int(s[0])

    return pred, succ


class Instruction:
    def _is_instruction_fit_pattern(self, instr_bits, patttern):
        for case in patttern:
            if instr_bits[-1 - case[1]: 32 - case[0]] != case[2]:
                return False
        return True

    def _get_instruction_name_and_args(self, instr_bits):
        for pattern in patterns:
            if self._is_instruction_fit_pattern(instr_bits, pattern[0]):
                return pattern[1], pattern[2]

        return "invalid instruction", ()

    def _decode(self, bin_repr):
        n = int(bin_repr, base=2)
        if bin_repr[0] == '0':
            return n
        return n - 2 ** len(bin_repr)

    def __slice__(self, r, l=None):
        if l is None:
            return self.bits[31 - r]

        return self.bits[32 - l: 32 - r]

    def __init__(self, b):
        self.bits = bin(2 ** 32 + decoder_le(b))[3:]
        self.rbits = self.bits[::-1]

        # self.opcode = self.bits % 2 ** 7
        # self.type = ''
        # if self.opcode == instruction_types['r']:
        self.name, self.args = self._get_instruction_name_and_args(self.bits)

        self.type = instruction_types[self.bits[-7:]]
        self.rd = regs[int(self.__slice__(7, 12), base=2)]
        self.rs1 = regs[int(self.__slice__(15, 20), base=2)]
        self.shamt = int(self.__slice__(20, 25), base=2)
        self.rs2 = regs[self.shamt]

        self.imm_str = '0'

        if self.type[0] == 'i':
            self.imm_str = self.__slice__(20, 32)
        elif self.type[0] == 's':
            self.imm_str = self.__slice__(25, 32) + self.__slice__(7, 12)
        elif self.type[0] == 'u':
            self.imm_str = self.__slice__(12, 32)  # + '0' * 12
        elif self.type[0] == 'j':
            self.imm_str = self.__slice__(31) + self.__slice__(12, 20) + self.__slice__(20) + self.__slice__(21, 31) + '0'
        elif self.type[0] == 'b':
            self.imm_str = self.__slice__(31) + self.__slice__(7) + self.__slice__(25, 31) + self.__slice__(8, 12) + '0'

        self.imm = self._decode(self.imm_str)

    def __str__(self, index=0):
        if self.name == "invalid instruction":
            return "   %05x:\t%08x\t%-7s\n" % (index, int(self.bits, base=2), self.name)

        self.offset = self.imm + index

        result = ''
        is_mark = index in v.markers

        if is_mark:
            result += "\n%08x \t<%s>:\n" % (index, v.markers[index])

        result += "   %05x:\t%08x\t%7s" % (index, int(self.bits, base=2), self.name)

        if self.type == "i4" or self.name == "fence.i":  # zifence
            return result + '\n'

        result += '\t'
        if self.type == 'j':
            return result + "%s, 0x%x <%s>\n" % (self.rd, self.offset, v.markers[self.offset])

        elif self.type == 'b':
            return result + "%s, %s, 0x%x, <%s>\n" % (self.rs1, self.rs2, self.offset, v.markers[self.offset])

        elif self.name == "fence":
            fa = fence_args(self.__slice__(20, 28))
            if fa[0] == "w" and fa[1] == "":  # zihintpuse
                return result + "%7s\n" % "pause"
            else:
                return result + "%s, %s\n" % fa

        elif self.type in ["i2", "i3", "s"]:
            return result + "%s, %d(%s)\n" % ((self.rs2 if self.type == "s" else self.rd), self.imm, self.rs1)

        elif self.type[0] == 'u':
            if self.imm < 0:
                return result + "%s, %s\n" % (self.rd, hex(int(self.imm_str, base=2)))
            else:
                return result + "%s, 0x%x\n" % (self.rd, self.imm)

        elif self.name.startswith("amo"):
            return result + "%s, %s, (%s)\n" % (self.rd, self.rs2, self.rs1)

        else:
            self.offset = "0x%x" % self.offset
            if len(self.args) == 2:

                return result + "%s, %s\n" % tuple([getattr(self, arg) for arg in self.args])

            else:  # len(self.args) = 3:

                return result + "%s, %s, %s\n" % tuple([getattr(self, arg) for arg in self.args])


def make_instructions(rb, text_s: Section):

    for start in range(text_s.values[sh_offset], text_s.values[sh_offset] + text_s.values[sh_size], 4):

        instr = Instruction(rb[start: start + 4])
        v.instructions.append(instr)

        idx = text_s.values[sh_addr] + start - text_s.values[sh_offset] + instr.imm

        if (instr.type[0] == 'b' or instr.type[0] == 'j') and (idx not in v.markers.keys()):
            v.markers[idx] = f"L{v.not_named_markers_index}"
            v.not_named_markers_index += 1


def print_(s):
    v.output.append(s)


def print_instructions(text_s):

    print_('.text\n')
    index = text_s.values[sh_addr]

    for i in range(len(v.instructions)):
        print_(v.instructions[i].__str__(index))
        index += 4


def print_symtab():
    print_("\n\n.symtab\n\nSymbol Value              Size Type     Bind     Vis       Index Name\n")
    for i in range(len(v.symbols)):
        symbol = v.symbols[i]
        print_(symbol.__str__(i))


def get_section_index_by_name(s_name):
    for i in range(len(v.sections)):
        if v.sections[i].name == s_name:
            return i
    sys.exit(f'"{s_name}" section not fount')


def main():
    if len(sys.argv) != 3:
        sys.exit(f"Wrong number of arguments.\nExpected 2 arguments, found {len(sys.argv) - 1}.")

    try:
        with open(sys.argv[1], "rb") as f:
            raw_bytes = f.read()
    except PermissionError:
        sys.exit(f"Permission denied: can not read from input file {sys.argv[1]}")

    make_header_values(raw_bytes)

    if v.get(e_shoff) == 0:
        sys.exit("table of section header not found")

    if v.get(e_shnum) == 0:
        sys.exit("no section header found")

    if v.get(e_shstrndx) == 0:
        sys.exit("table of section headers' names not found")

    make_sh_values(rb=raw_bytes)

    make_sh_names(rb=raw_bytes)
    # with open(sys.argv[2], 'w') as f:

    text_s = v.sections[get_section_index_by_name(".text")]
    symtab_s = v.sections[get_section_index_by_name(".symtab")]
    strtab_s = v.sections[get_section_index_by_name(".strtab")]

    make_st_values(rb=raw_bytes, symtab_s=symtab_s, strtab_s=strtab_s)

    make_instructions(raw_bytes, text_s)

    print_instructions(text_s)
    print_symtab()
    if v.output[-1][-1] == '\n':
        v.output[-1] = v.output[-1][:-1]
    try:
        with open(sys.argv[2], 'w') as f:
            f.write("".join(v.output))
    except PermissionError:
        sys.exit(f"Permission denied: can not write into output file {sys.argv[2]}")


if __name__ == '__main__':
    main()
