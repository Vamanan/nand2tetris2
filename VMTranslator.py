import argparse
import os

# operations
ADD = "add"
SUB = "sub"
NEG = "neg"
EQ = "eq"
GT = "gt"
LT = "lt"
AND = "and"
OR = "or"
NOT = "not"
ARITHMETIC_OPERATIONS = set(["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"])
PUSH_POP_OPERATIONS = set(["push", "pop"])
LABEL_OPERATIONS = set(["label"])
IF_OPERATIONS = set(["if-goto"])
FUNCTION_OPERATIONS = set(["function"])
RETURN_OPERATIONS = set(["return"])
CALL_OPERATIONS = set(["call"])

# command type
ARITHMETIC_COMMAND_TYPE = "C_ARITHMETIC"
PUSH_COMMAND_TYPE = "C_PUSH"
POP_COMMAND_TYPE = "C_POP"
LABEL_COMMAND_TYPE = "C_LABEL"
GOTO_COMMAND_TYPE = "C_GOTO"
IF_COMMAND_TYPE = "C_IF"
FUNCTION_COMMAND_TYPE = "C_FUNCTION"
RETURN_COMMAND_TYPE = "C_RETURN"
CALL_COMMAND_TYPE = "C_CALL"

# memory segments
CONSTANT = "constant"
LOCAL = "local"
ARGUMENT = "argument"
THIS = "this"
THAT = "that"
TEMP = "temp"
POINTER = "pointer"
STATIC = "static"

TEMP_BASE_ADDRESS = 5

SEGMENT_MAPPING = {LOCAL: "LCL", ARGUMENT: "ARG", THIS: "THIS", THAT: "THAT"}


def get_output_file_path(input_file_path):
    dirname = os.path.dirname(input_file_path)
    filename = os.path.basename(input_file_path)
    filename, _ = os.path.splitext(filename)
    output_filename = filename + '.asm'
    output_file_path = os.path.join(dirname, output_filename)
    return output_file_path


def get_filename_without_extension(input_file_path):
    filename = os.path.basename(input_file_path)
    filename, _ = os.path.splitext(filename)
    return filename


class Parser(object):
    def __init__(self, input_file_path):
        self.vm_file = open(input_file_path, 'r')
        self.current_command = None

    def _is_line_comment(self, line):
        return line.startswith("//")

    def _is_line_new_line(self, line):
        return len(line.strip()) == 0

    def has_more_commands(self):
        # returns true if there are more lines to be read in self.vm_file
        # get current position

        while True:
            current_position = self.vm_file.tell()
            line = self.vm_file.readline()
            if line and not self._is_line_comment(line) and not self._is_line_new_line(line):
                # line is a command
                break
            elif not line:
                # end of file has been reached
                return False

        # return to beginning of line
        self.vm_file.seek(current_position)
        return True

    def advance(self):
        # this method should be called only if has_more_commands returns True
        # sets current_command
        self.current_command = self.vm_file.readline().strip()

    def command_type(self):
        operation = self.current_command.split()[0]
        if operation in ARITHMETIC_OPERATIONS:
            return ARITHMETIC_COMMAND_TYPE
        elif operation in PUSH_POP_OPERATIONS:
            if operation == "push":
                return PUSH_COMMAND_TYPE
            else:
                return POP_COMMAND_TYPE
        elif operation in LABEL_OPERATIONS:
            return LABEL_COMMAND_TYPE
        elif operation in IF_OPERATIONS:
            return IF_COMMAND_TYPE
        elif operation in FUNCTION_OPERATIONS:
            return FUNCTION_COMMAND_TYPE
        elif operation in RETURN_OPERATIONS:
            return RETURN_COMMAND_TYPE
        elif operation in CALL_OPERATIONS:
            return CALL_COMMAND_TYPE

    def arg1(self):
        operation = self.current_command.split()[0]
        if operation in ARITHMETIC_OPERATIONS:
            return operation
        else:
            operation, arg1, arg2 = self.current_command.split()[:3]
            return arg1

    def arg2(self):
        operation = self.current_command.split()[0]
        if operation in ARITHMETIC_OPERATIONS:
            return None
        elif operation in PUSH_POP_OPERATIONS:
            operation, arg1, arg2 = self.current_command.split()[:3]
            return arg2


class CodeWriter(object):
    def __init__(self, output_file_path):
        self.assembly_file = open(output_file_path, 'w')
        self._if_else_block_num = 0

    def _get_push_command(self, arg, constant=False):
        commands = list()
        # bring variable into D
        commands.append("@{}".format(arg))
        if not constant:
            commands.append("D=M")
        else:
            commands.append("D=A")
        # write D to top of stack
        commands.append("@SP")
        commands.append("A=M")
        commands.append("M=D")
        # increment stack pointer
        commands.append("@SP")
        commands.append("M=M+1")
        return "\n".join(commands)

    def _get_pop_command(self, variable_name):
        commands = list()
        # decrement stack pointer
        commands.append("@SP")
        commands.append("M=M-1")
        # store top of stack in D
        commands.append("A=M")
        commands.append("D=M")
        # store D in variable
        commands.append("@{}".format(variable_name))
        commands.append("M=D")
        return '\n'.join(commands)

    def _get_add_command(self, variable1, variable2):
        commands = list()
        # store variable2 in D
        commands.append("@{}".format(variable2))
        commands.append("D=M")
        # bring variable 1 into memory
        commands.append("@{}".format(variable1))
        # store M+D in M
        commands.append("M=M+D")
        return '\n'.join(commands)

    def _get_sub_command(self, variable1, variable2):
        commands = list()
        # store variable2 in D
        commands.append("@{}".format(variable2))
        commands.append("D=M")
        # bring variable 1 into memory
        commands.append("@{}".format(variable1))
        # store M-D in M
        commands.append("M=M-D")
        return '\n'.join(commands)

    def _get_and_command(self, variable1, variable2):
        commands = list()
        # store variable2 in D
        commands.append("@{}".format(variable2))
        commands.append("D=M")
        # bring variable 1 into memory
        commands.append("@{}".format(variable1))
        # store M&D in M
        commands.append("M=D&M")
        return '\n'.join(commands)

    def _get_or_command(self, variable1, variable2):
        commands = list()
        # store variable2 in D
        commands.append("@{}".format(variable2))
        commands.append("D=M")
        # bring variable 1 into memory
        commands.append("@{}".format(variable1))
        # store M|D in M
        commands.append("M=D|M")
        return '\n'.join(commands)

    def _get_eq_command(self, variable1, variable2):
        # store result of variable1 eq variable2 in variable1
        commands = list()
        # store variable2 in D
        commands.append("@{}".format(variable2))
        commands.append("D=M")
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set D to D-M
        commands.append("D=M-D")

        # if variable1 - variable2 != 0, jump to else
        commands.append("@else{}".format(self._if_else_block_num))
        commands.append("D;JNE")
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set M to true
        commands.append("M=-1")
        # jump to outside if
        commands.append("@outsideif{}".format(self._if_else_block_num))
        commands.append("0;JMP")
        # set label to else
        commands.append("(else{})".format(self._if_else_block_num))
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set M to false
        commands.append("M=0")
        # jump to outside if
        commands.append("@outsideif{}".format(self._if_else_block_num))
        commands.append("0;JMP")
        # set label to outside if
        commands.append("(outsideif{})".format(self._if_else_block_num))
        self._if_else_block_num += 1
        return '\n'.join(commands)

    def _get_gt_command(self, variable1, variable2):
        # store result of variable1 gt variable2 in variable1
        commands = list()
        # store variable2 in D
        commands.append("@{}".format(variable2))
        commands.append("D=M")
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set D to M-D
        commands.append("D=M-D")

        # if variable1 - variable2  <= 0, jump to else
        commands.append("@else{}".format(self._if_else_block_num))
        commands.append("D;JLE")
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set M to true
        commands.append("M=-1")
        # jump to outside if
        commands.append("@outsideif{}".format(self._if_else_block_num))
        commands.append("0;JMP")
        # set label to else
        commands.append("(else{})".format(self._if_else_block_num))
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set M to false
        commands.append("M=0")
        # jump to outside if
        commands.append("@outsideif{}".format(self._if_else_block_num))
        commands.append("0;JMP")
        # set label to outside if
        commands.append("(outsideif{})".format(self._if_else_block_num))
        self._if_else_block_num += 1
        return '\n'.join(commands)

    def _get_lt_command(self, variable1, variable2):
        # store result of variable1 lt variable2 in variable1
        commands = list()
        # store variable2 in D
        commands.append("@{}".format(variable2))
        commands.append("D=M")
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set D to variable1 - variable2
        commands.append("D=M-D")
        # if variable1 - variable2 >= 0, jump to else
        commands.append("@else{}".format(self._if_else_block_num))
        commands.append("D;JGE")
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set M to true
        commands.append("M=-1")
        # jump to outside if
        commands.append("@outsideif{}".format(self._if_else_block_num))
        commands.append("0;JMP")
        # set label to else
        commands.append("(else{})".format(self._if_else_block_num))
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # set M to false
        commands.append("M=0")
        # jump to outside if
        commands.append("@outsideif{}".format(self._if_else_block_num))
        commands.append("0;JMP")
        # set label to outside if
        commands.append("(outsideif{})".format(self._if_else_block_num))
        self._if_else_block_num += 1
        return '\n'.join(commands)

    def _get_not_command(self, variable1):
        # store result of not variable1 in variable1
        commands = list()
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # perform not M and store in M
        commands.append("M=!M")
        return '\n'.join(commands)

    def _get_neg_command(self, variable1):
        # store result of neg variable1 in variable1
        commands = list()
        # bring variable1 into memory
        commands.append("@{}".format(variable1))
        # find 2's complement of M
        # perform not M and store in M
        commands.append("M=!M")
        # add 1 to M
        commands.append("M=M+1")
        return '\n'.join(commands)

    def _write_binary_commands(self, operator):
        # store variable2 in R13
        pop_command = self._get_pop_command("R13")
        self.assembly_file.write(pop_command + "\n")
        # store variable1 in R14
        pop_command = self._get_pop_command("R14")
        self.assembly_file.write(pop_command + "\n")
        # perform operation based on operator
        if operator == ADD:
            # add R13 and R14 and store in R13
            add_command = self._get_add_command("R14", "R13")
            self.assembly_file.write(add_command + "\n")
        elif operator == SUB:
            sub_command = self._get_sub_command("R14", "R13")
            self.assembly_file.write(sub_command + "\n")
        elif operator == AND:
            and_command = self._get_and_command("R14", "R13")
            self.assembly_file.write(and_command + "\n")
        elif operator == OR:
            or_command = self._get_or_command("R14", "R13")
            self.assembly_file.write(or_command + "\n")
        # push R13 onto stack
        push_command = self._get_push_command("R14")
        self.assembly_file.write(push_command + "\n")

    def _write_eq_commands(self):
        # first pop
        pop_command = self._get_pop_command("R13")
        self.assembly_file.write(pop_command + "\n")
        # second pop
        pop_command = self._get_pop_command("R14")
        self.assembly_file.write(pop_command + "\n")
        # write eq commands
        eq_command = self._get_eq_command("R14", "R13")
        self.assembly_file.write(eq_command + "\n")
        # push R14 onto stack
        push_command = self._get_push_command("R14")
        self.assembly_file.write(push_command + "\n")

    def _write_gt_commands(self):
        # first pop
        pop_command = self._get_pop_command("R13")
        self.assembly_file.write(pop_command + "\n")
        # second pop
        pop_command = self._get_pop_command("R14")
        self.assembly_file.write(pop_command + "\n")
        # write gt commands
        gt_command = self._get_gt_command("R14", "R13")
        self.assembly_file.write(gt_command + "\n")
        # push R14 onto stack
        push_command = self._get_push_command("R14")
        self.assembly_file.write(push_command + "\n")

    def _write_lt_commands(self):
        # first pop
        pop_command = self._get_pop_command("R13")
        self.assembly_file.write(pop_command + "\n")
        # second pop
        pop_command = self._get_pop_command("R14")
        self.assembly_file.write(pop_command + "\n")
        # write lt commands
        lt_command = self._get_lt_command("R14", "R13")
        self.assembly_file.write(lt_command + "\n")
        # push R14 onto stack
        push_command = self._get_push_command("R14")
        self.assembly_file.write(push_command + "\n")

    def _write_not_commands(self):
        # first pop
        pop_command = self._get_pop_command("R13")
        self.assembly_file.write(pop_command + "\n")
        # write not commands
        not_command = self._get_not_command("R13")
        self.assembly_file.write(not_command + "\n")
        # push R13 onto stack
        push_command = self._get_push_command("R13")
        self.assembly_file.write(push_command + "\n")

    def _write_neg_commands(self):
        # first pop
        pop_command = self._get_pop_command("R13")
        self.assembly_file.write(pop_command + "\n")
        # write neg commands
        neg_command = self._get_neg_command("R13")
        self.assembly_file.write(neg_command + "\n")
        # push R13 onto stack
        push_command = self._get_push_command("R13")
        self.assembly_file.write(push_command + "\n")

    def _get_temp_push_command(self, offset):
        commands = list()
        # bring right value into memory
        address = TEMP_BASE_ADDRESS + int(offset)
        commands.append("@{}".format(address))
        # store M in D
        commands.append("D=M")
        # write D to top of stack
        commands.append("@SP")
        commands.append("A=M")
        commands.append("M=D")
        # increment stack pointer
        commands.append("@SP")
        commands.append("M=M+1")
        return '\n'.join(commands)

    def _get_segment_push_command(self, segment, offset):
        commands = list()
        # store base address in D
        commands.append("@{}".format(segment))
        commands.append("D=M")
        # set A to offset
        commands.append("@{}".format(offset))
        # set A to D + A
        commands.append("A=D+A")
        # store value in D
        commands.append("D=M")
        # set A to top of stack
        commands.append("@{}".format("SP"))
        commands.append("A=M")
        # store D in top of stack
        commands.append("M=D")
        # increment stack pointer
        commands.append("@{}".format("SP"))
        commands.append("M=M+1")
        return '\n'.join(commands)

    def _get_pointer_push_command(self, arg):
        commands = list()
        if arg == "0":
            this_or_that = SEGMENT_MAPPING[THIS]
        else:
            this_or_that = SEGMENT_MAPPING[THAT]
        # store base address of this/that pointer in D
        commands.append("@{}".format(this_or_that))
        commands.append("D=M")
        # set A to top of stack
        commands.append("@{}".format("SP"))
        commands.append("A=M")
        # store D in top of stack
        commands.append("M=D")
        # increment stack pointer
        commands.append("@{}".format("SP"))
        commands.append("M=M+1")
        return '\n'.join(commands)

    def _get_static_push_command(self ,arg, filename):
        commands = list()
        variable_name = "{}.{}".format(filename, arg)
        # set A to variable name
        commands.append("@{}".format(variable_name))
        # store value in D
        commands.append("D=M")
        # set A to top of stack
        commands.append("@{}".format("SP"))
        commands.append("A=M")
        # store D in top of stack
        commands.append("M=D")
        # increment stack pointer
        commands.append("@{}".format("SP"))
        commands.append("M=M+1")
        return '\n'.join(commands)


    def _write_push_commands(self, arg1, arg2, filename):
        if arg1 == CONSTANT:
            arg = arg2
            push_command = self._get_push_command(arg, constant=True)
        elif arg1 in SEGMENT_MAPPING:
            segment = SEGMENT_MAPPING[arg1]
            offset = arg2
            push_command = self._get_segment_push_command(segment, offset)
        elif arg1 == TEMP:
            offset = arg2
            push_command = self._get_temp_push_command(offset)
        elif arg1 == POINTER:
            arg = arg2
            push_command = self._get_pointer_push_command(arg)
        elif arg1 == STATIC:
            arg = arg2
            push_command = self._get_static_push_command(arg, filename)

        self.assembly_file.write(push_command + "\n")

    def _get_temp_pop_command(self, offset):
        commands = list()
        # decrement stack pointer
        commands.append("@SP")
        commands.append("M=M-1")
        # store top of stack in D
        commands.append("A=M")
        commands.append("D=M")
        # store D in right address where base address is 5 and offset is given
        address = TEMP_BASE_ADDRESS + int(offset)
        commands.append("@{}".format(address))
        commands.append("M=D")
        return '\n'.join(commands)

    def _get_segment_pop_command(self, segment, offset):
        commands = list()
        # store base address in D
        commands.append("@{}".format(segment))
        commands.append("D=M")
        # store offset in A
        commands.append("@{}".format(offset))
        # set D to D+A
        commands.append("D=D+A")
        # store D in R13
        commands.append("@{}".format("R13"))
        commands.append("M=D")

        # decrement stack pointer
        commands.append("@SP")
        commands.append("M=M-1")

        # store top of stack in D
        commands.append("@SP")
        commands.append("A=M")
        commands.append("D=M")

        # set A to dest address
        commands.append("@{}".format("R13"))
        commands.append("A=M")
        # write D to dest address
        commands.append("M=D")
        return '\n'.join(commands)

    def _get_pointer_pop_command(self, arg):
        commands = list()
        if arg == "0":
            this_or_that = SEGMENT_MAPPING[THIS]
        else:
            this_or_that = SEGMENT_MAPPING[THAT]
        # decrement stack pointer
        commands.append("@SP")
        commands.append("M=M-1")
        # store top of stack in D
        commands.append("A=M")
        commands.append("D=M")
        # set A to THIS/THAT
        commands.append("@{}".format(this_or_that))
        # set THIS/THAT base address to D
        commands.append("M=D")
        return '\n'.join(commands)

    def _get_static_pop_command(self, arg, filename):
        commands = list()
        variable_name = "{}.{}".format(filename, arg)
        # decrement stack pointer
        commands.append("@SP")
        commands.append("M=M-1")
        # store top of stack in D
        commands.append("A=M")
        commands.append("D=M")
        # set A to variable
        commands.append("@{}".format(variable_name))
        # set M to D
        commands.append("M=D")
        return '\n'.join(commands)

    def _write_pop_commands(self, arg1, arg2, filename):
        # pop top of stack and store onto the right place in memory using arg1, arg2
        if arg1 in SEGMENT_MAPPING:
            offset = arg2
            segment = SEGMENT_MAPPING[arg1]
            pop_command = self._get_segment_pop_command(segment, offset)
        elif arg1 == TEMP:
            offset = arg2
            pop_command = self._get_temp_pop_command(offset)
        elif arg1 == POINTER:
            arg = arg2
            pop_command = self._get_pointer_pop_command(arg)
        elif arg1 == STATIC:
            arg = arg2
            pop_command = self._get_static_pop_command(arg, filename)

        self.assembly_file.write(pop_command + "\n")

    def write_arithmetic(self, command):
        # this function converts an arithmetic command in vm code to assembly code
        assert(command in ARITHMETIC_OPERATIONS)
        set(["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"])
        if command == ADD or command == SUB or command == AND or command == OR:
            self._write_binary_commands(command)
        elif command == NEG:
            self._write_neg_commands()
        elif command == EQ:
            self._write_eq_commands()
        elif command == GT:
            self._write_gt_commands()
        elif command == LT:
            self._write_lt_commands()
        elif command == NOT:
            self._write_not_commands()

    def write_push_pop(self, command, arg1, arg2, filename):
        # self.assembly_file.write(command + " " + segment + " " + index + "\n")
        if command == PUSH_COMMAND_TYPE:
            self._write_push_commands(arg1, arg2, filename)
        elif command == POP_COMMAND_TYPE:
            self._write_pop_commands(arg1, arg2, filename)

    def write_comment(self, comment):
        self.assembly_file.write("// " + comment + "\n")

    def close(self):
        self.assembly_file.close()


def main(args):
    input_file_path = args.file_path
    # create_file(input_file_path)
    parser = Parser(input_file_path)
    output_file_path = get_output_file_path(input_file_path)
    filename = get_filename_without_extension(input_file_path)
    code_writer = CodeWriter(output_file_path)
    while parser.has_more_commands():
        parser.advance()
        code_writer.write_comment(parser.current_command)
        command_type = parser.command_type()
        if command_type != RETURN_COMMAND_TYPE:
            arg1 = parser.arg1()
        if command_type in set([PUSH_COMMAND_TYPE, POP_COMMAND_TYPE, FUNCTION_COMMAND_TYPE, CALL_COMMAND_TYPE]):
            arg2 = parser.arg2()
            code_writer.write_push_pop(command_type, arg1, arg2, filename)
        else:
            code_writer.write_arithmetic(arg1)
    code_writer.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Translate VM code into Hack assembly code')
    parser.add_argument('file_path', help='path to VM code file')
    args = parser.parse_args()
    main(args)
