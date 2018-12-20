# Two Pass Assembler
# for stupid AoC assembly language

# error functions

function SYNTAX_ERROR(msg) {
  if (msg) {msg = " (" msg ")"; }
  print "Invalid syntax" msg ":" >> "/dev/stderr";
  print FILENAME ":" FNR "  " ORIG >> "/dev/stderr";
  FATAL=1; # used to skip second pass
  exit(FATAL);
}

function EVALUATION_ERROR(msg) {
  if (msg) {msg = " (" msg ")"; }
  print "Evaluation error" msg ":" >> "/dev/stderr";
  print instruction[i,"file"] ":" instruction[i,"linenum"] "  " instruction[i,"line"] >> "/dev/stderr";
  FATAL=1; # used to skip second pass
  exit(FATAL);
}

#   Evaluate an expression.
#   The expression is in the *global* variable `expr`.
#   An expression is either:
#       A register (optionally followed by ')' or ','),
#           in which case the register gets returned;
#       A value (optionally followed by ')' or ','),
#           in which case the value gets returned;
#       A symbol (optionally followed by ')' or ','),
#           in which case the value of the symbol gets returned;
#       Or an operator expression beginning with '(' and the operator,
#           in which case the operator gets recorded,
#           the first argument gets recorded,
#           if the expression ends, the unary operator gets processed,
#           otherwise, the second argument gets recorded,
#           and the binary operator gets processed.

function eval_expr(op, ex1, ex2, mm) {
    if (match(expr, /^(([-+r]?[[:digit:]]+)|([$][[:alnum:]]*))([,)].*)?/, mm)) {
        expr = mm[4];
        if (mm[2] != "") {
            return mm[2];
        } else if (mm[3] in symbols) {
            return symbols[mm[3]];
        } else {
            EVALUATION_ERROR("Undefined symbol " substr(mm[1],2));
        }
    } else if (match(expr, /^[(]([-+*/])/, mm)) {
        op = mm[1];
        expr = substr(expr, 3);
        ex1 = eval_expr();
        if (expr ~ /^[)]/) {
            expr = substr(expr, 2);
            if (op == "+") {
                return ex1;
            } else if ((op == "-") && (ex1 ~ /^[-+[:digit:]]/)) {
                return -ex1;
            } else {
                EVALUATION_ERROR();
            }
        } else {
            expr = substr(expr, 2);
            ex2 = eval_expr();
            expr = substr(expr, 2);
            if (ex1 ~ /^[-+[:digit:]]/ && ex2 ~ /^[-+[:digit:]]/) {
                if (op == "+") {
                    return ex1 + ex2;
                } else if (op == "-") {
                    return ex1 - ex2;
                } else if (op == "*") {
                    return ex1 * ex2;
                } else if (op == "/") {
                    return int(ex1 / ex2);
                }
            } else {
                EVALUATION_ERROR();
            }
        }
    } else {
        EVALUATION_ERROR();
    }
}

#   Parse an operator.  Helper function for parsing a
#   parenthesized expression.

function parse_oper(mm) {
    if (match($0, /^([-+*\/]) */, mm)) {
        $0 = substr($0, mm[0, "length"] + 1);
        return mm[1];
    }
    SYNTAX_ERROR("Invalid operator " $1);
}

#   Parse an argument.
#   Each argument can be a register, a value, a symbol,
#   or a parenthesized expression.

function parse_arg(    build, ex1, ex2, op1, mm) {
    if (match($0, /^(r[[:digit:]]+) */, mm)) {
        $0 = substr($0, mm[0, "length"] + 1);
        return mm[1];
    }
    if (match($0, /^(-?[[:digit:]]+) */, mm)) {
        $0 = substr($0, mm[0, "length"] + 1);
        return mm[1];
    }
    if (match($0, /^([[:alpha:]][[:alnum:]_]*) */, mm)) {
        $0 = substr($0, mm[0, "length"] + 1);
        return "$" mm[1];
    }
    if (match($0, /^[.] */, mm)) {
        $0 = substr($0, mm[0, "length"] + 1);
        return "$";
    }
    if (match($0, /^[(] */, mm)) {
        $0 = substr($0, mm[0, "length"] + 1);
        if (match($0, /^([-+]) */, mm)) {
            $0 = substr($0, mm[0, "length"] + 1);
            ex1 = parse_arg();
            ex1 = "(" mm[1] ex1 ")"
        } else {
            ex1 = parse_arg();
        }
        if (match($0, /^[)] */, mm)) {
            $0 = substr($0, mm[0, "length"] + 1);
            return "(+" ex1 ")"
        } else {
            op1 = parse_oper();
            ex2 = parse_arg();
            if (!match($0, /^[)] */, mm)) {
                SYNTAX_ERROR();
            }
            $0 = substr($0, mm[0, "length"] + 1);
            return "(" op1 ex1 "," ex2 ")";
        }
    }
    SYNTAX_ERROR("Unparsable argument " $1);
}

# Initialization:

BEGIN {

#   Clear the symbol table

  delete symbols;

#   Clear the instruction array

  delete instruction;

#   Clear the output array

  delete output;
  n_output = 0;

#   Reset the address counter

  addr = 0;

#   Record known opcodes and directives

  valid_opcodes = " #org #eq #ip add mul ban bor set gt eq ";

}

# First Pass:

#   Record the original line

{
  ORIG = $0;
}

#   Reset the per-line variables

{
    symbol = "";
    delete opcode;
}

#   Strip comments

{
  sub(/ *;.*/, "");
}

#   Identify and extract symbol from beginning of line

/^([[:alpha:]][[:alnum:]_]*):/ {
  symbol = substr($1, 1, length($1)-1);
  sub(/^([[:alpha:]][[:alnum:]_]*): */, "");
  symbols["$" symbol] = addr;
}

#   Skip blank lines

/^$/ { next; }

#   Parse the rest of the line into an instruction/directive
#   and a set of arguments.

{
    delete opcode;

    if (!match($0, /^ *(#?[[:alpha:]]+) */, m)) {
        SYNTAX_ERROR("Invalid opcode " $1);
    }
    opcode[0] = m[1]
    if (!index(valid_opcodes, " " opcode[0] " ")) {
        SYNTAX_ERROR("Invalid opcode " opcode[0]);
    }
    $0 = substr($0, length(m[0]) + 1)

    opcode[1] = parse_arg();

    if (length($0) > 0) {

        if (match($0, /^, */, m)) {
            $0 = substr($0, m[0, "length"] + 1)
            opcode[2] = parse_arg();
        }

        if (!match($0, /^-> */, m)) {
            SYNTAX_ERROR("Missing result register");
        }
        $0 = substr($0, m[0, "length"] + 1)
        opcode[3] = parse_arg();
        if (!(opcode[3] ~ /^r/)) {
            if (opcode[3] ~ /^[$]/) {
                if (!(symbols[opcode[3]] ~ /^r/)) {
                    SYNTAX_ERROR("Result must be a register, not " symbols[opcode[3]]);
                }
            } else {
                SYNTAX_ERROR("Result must be a register, not " opcode[3]);
            }
        }
    }
}

#   Process immediate directives

(opcode[0] == "#eq") && (opcode[1] != "") && (opcode[2] == "") && (opcode[3] == "") {
  if (symbol == "") { SYNTAX_ERROR("#eq requires a label"); }
  symbols["$" symbol] = opcode[1];
  next;
}

(opcode[0] == "#org") && (opcode[1] != "") && (opcode[2] == "") && (opcode[3] == "") {
  if (symbol != "") { SYNTAX_ERROR("#org cannot have a label"); }
  expr = opcode[1];
  addr = eval_expr();
  if (!(addr ~ /^[-+[:digit:]]/)) {
      SYNTAX_ERROR("Origin must be a value")
  }
  next;
}

#   Process delayed directives

(opcode[0] == "#ip") && (opcode[1] != "") && (opcode[2] == "") && (opcode[3] == "") {
  output[n_output,0] = "#ip";
  output[n_output,1] = opcode[1];
  n_output += 1;
  next;
}

#   Record the instruction

{
    if (opcode[0] == "set") {
        if (opcode[2] != "") {
            SYNTAX_ERROR("`set` only accepts one argument");
        }
    } else {
        if (opcode[2] == "") {
            SYNTAX_ERROR("`" opcode[0] "` requires two arguments");
        }
    }
    if (opcode[2] == "") {opcode[2] = opcode[1]}; # special case for `set`
    if (opcode[3] == "") { SYNTAX_ERROR("No result register"); }
    for (i=0; i<4; i+=1) {
        instruction[addr,i] = opcode[i];
    }
    instruction[addr,"line"] = ORIG;
    instruction[addr,"file"] = FILENAME;
    instruction[addr,"lineno"] = FNR;
    addr += 1;
}

# Second Pass:
#   Process each instruction to produce the output opcodes,
#   replacing symbols with values before processing.
#

END {
    if (!FATAL) {
        for (i=0; i<n_output; i+=1) {
            # evaluate the argument
            expr = output[i,1]
            output[i,1] = eval_expr();
            if (output[i,0] == "#ip") {
                if (output[i,1] ~ /^r/) {
                    output[i,1] = substr(output[i,1],2);
                } else {
                    EVALUATION_ERROR("#ip argument must be a register")
                }
            }
            print output[i,0], output[i,1];
        }
        for (i=0; i<addr; i+=1) {
            # create symbol `$` to hold the current address
            symbols["$"] = i;
            if (instruction[i,0] == "") {
                print "setr 0 0 0"
            } else {
                # evaluate each argument
                for (j=1; j<4; j+=1) {
                    expr = instruction[i,j];
                    instruction[i,j] = eval_expr();
                }
                if (length(instruction[i,0]) == 2) {
                    # eq and gt get type of instruction[i,1] appended first
                    if (instruction[i,1] ~ /^r/) {
                        instruction[i,1] = substr(instruction[i,1],2)
                        instruction[i,0] = instruction[i,0] "r"
                    } else {
                        instruction[i,0] = instruction[i,0] "i"
                    }
                } else {
                    if (instruction[i,1] ~ /^r/) {
                        instruction[i,1] = substr(instruction[i,1],2)
                    } else if (instruction[i,0] != "set") {
                        EVALUATION_ERROR("First argument must be a register")
                    }
                }
                if (instruction[i,2] ~ /^r/) {
                    instruction[i,2] = substr(instruction[i,2],2)
                    instruction[i,0] = instruction[i,0] "r"
                } else {
                    instruction[i,0] = instruction[i,0] "i"
                }
                instruction[i,3] = substr(instruction[i,3],2);
                print instruction[i,0], instruction[i,1], instruction[i,2], instruction[i,3]
            }
        }
    }
}
