# Obfuscates game engine to prevent use of automated decompile and decryption
# tools by modifying source code.
#
# Meant to be used on an unmodified official commit.
#
# Last tested on Godot 4.7.2
#
# FILES TOUCHED:
#
# core/io/file_access_encrypted.h
# core/io/file_access_pack.h
# modules/gdscript/gdscript_parser.cpp
# modules/gdscript/gdscript_tokenizer.cpp
# modules/gdscript/gdscript_tokenizer.h
# modules/gdscript/gdscript_tokenizer_buffer.h


import random


WRITE_OUT = True

# Additional obfuscation to make reverse engineering harder (affects debugging)
STRONG = True


# Returns leading whitespace.
def lwhitespace(s: str) -> str:
    return s[:len(s)-len(s.lstrip())]


# Returns index of string starting with 'start' ignoring leading whitespace,
# or else -1 if not found.
def index_starts_with(ls: list[str], start: str) -> int:
    for i, s in enumerate(ls):
        if s.lstrip().startswith(start):
            return i

    return -1

# Returns a list of code lines within braces ignoring comments alongside the
# index where the code block ends.
def block_lines(ls: list[str], idx: int) -> tuple[int, list[str]]:
    lines = []
    end_idx = -1
    for i in range(idx, len(ls)):
        line = ls[i].strip()
        if line.startswith("}"):
            end_idx = i
            break
        elif not line.startswith("/"):
            idx = line.rfind(',')
            idx = idx if idx > 0 else len(line)
            lines.append(lwhitespace(ls[i]) + line[:idx])
    return (end_idx, lines)


def shuffle_tokens():
    text = ""

    with open("./modules/gdscript/gdscript_tokenizer.h", 'r') as f:
        text = f.read()

    lines = text.split("\n")

    enum_start = index_starts_with(lines, "enum Type") + 1

    if enum_start < 0:
        print("Failed to find token enum Type")
        return

    enum_end, names = block_lines(lines, enum_start)

    if enum_end < 0:
        print("Invalid file: end of enum not found.")
        return

    shuffle_names = [t for t in zip(range(len(names)-2), names[1:-1])]
    random.shuffle(shuffle_names)

    new_enum_text = ",\n".join(names[:1] + [t[1] for t in shuffle_names] + names[-1:]) + '\n'

    new_text = "\n".join(lines[:enum_start]) + '\n' + new_enum_text + "\n".join(lines[enum_end:])

    name_indices = [t[0] for t in shuffle_names]

    if WRITE_OUT:
        with open("./modules/gdscript/gdscript_tokenizer.h", 'w') as f:
            f.write(new_text)

    # Apply shuffle of enum to static token_names array.
    with open("./modules/gdscript/gdscript_tokenizer.cpp", 'r') as f:
        text = f.read()

    lines = text.split("\n")

    names_start = index_starts_with(lines, "static const char *token_names") + 1

    if names_start < 0:
        print("Failed to find static token names array.")
        return

    names_end, names = block_lines(lines, names_start)

    if names_end < 0:
        print("Invalid file: end of names array not found.")
        return

    names_trunc = names[1:]
    new_names = [names_trunc[i] for i in name_indices] if not STRONG else ['\t\"\"' for _ in name_indices]
    new_name_text = ",\n".join(names[:1] + new_names) + ',\n'
    new_text = "\n".join(lines[:names_start]) + '\n' + new_name_text + "\n".join(lines[names_end:])

    if WRITE_OUT:
        with open("./modules/gdscript/gdscript_tokenizer.cpp", 'w') as f:
            f.write(new_text)

    # Sync with ParseRule rules table in gdscript_parser.cpp
    with open("./modules/gdscript/gdscript_parser.cpp", 'r') as f:
        text = f.read()

    lines = text.split("\n")

    rules_start = index_starts_with(lines, "static ParseRule rules[]") + 1

    if rules_start < 0:
        print("Failed to find static parse rules array.")
        return

    rules_end, rules = block_lines(lines, rules_start)

    if rules_end < 0:
        print("Invalid file: end of parse rules array not found.")
        return

    rules_trunc = rules[1:]
    new_rules = [rules_trunc[i] for i in name_indices]
    new_rule_text = ",\n".join(rules[:1] + new_rules) + ',\n'
    new_text = "\n".join(lines[:rules_start]) + '\n' + new_rule_text + "\n".join(lines[rules_end:])

    if WRITE_OUT:
        with open("./modules/gdscript/gdscript_parser.cpp", 'w') as f:
            f.write(new_text)


def bump_tokenizer_version():
    text = ""

    with open("./modules/gdscript/gdscript_tokenizer_buffer.h", 'r') as f:
        text = f.read()

    lines = text.split("\n")

    version_idx = index_starts_with(lines, "static constexpr uint32_t TOKENIZER_VERSION")

    if (version_idx < 0):
        print("tokenizer version not found")
        return

    version_txt = lines[version_idx]
    equals_pos = version_txt.rfind('=')
    version = int(version_txt[equals_pos + 1:-1])
    new_version = version + random.randint(10, 110)

    new_version_txt = version_txt[:equals_pos] + f"= {new_version};"

    lines[version_idx] = new_version_txt

    new_text = "\n".join(lines)

    if WRITE_OUT:
        with open("./modules/gdscript/gdscript_tokenizer_buffer.h", 'w') as f:
            f.write(new_text)


def scramble_pack_magic():
    text = ""

    with open("./core/io/file_access_pack.h", 'r') as f:
        text = f.read()

    lines = text.split("\n")

    start = "#define PACK_HEADER_MAGIC"
    idx = index_starts_with(lines, start)

    if (idx < 0):
        print("Pack header magic not found")
        return

    lines[idx] = f"{start} {random.randint(0, 0xFFFFFFFF)}"

    new_text = "\n".join(lines)

    if WRITE_OUT:
        with open("./core/io/file_access_pack.h", 'w') as f:
            f.write(new_text)


def scramble_encrypted_header_magic():
    text = ""

    with open("./core/io/file_access_encrypted.h", 'r') as f:
        text = f.read()

    lines = text.split("\n")

    start = "#define ENCRYPTED_HEADER_MAGIC"
    idx = index_starts_with(lines, start)

    if (idx < 0):
        print("Encrypted header magic not found")
        return

    lines[idx] = f"{start} {random.randint(0, 0xFFFFFFFF)}"

    new_text = "\n".join(lines)

    if WRITE_OUT:
        with open("./core/io/file_access_encrypted.h", 'w') as f:
            f.write(new_text)

def main():
    shuffle_tokens()
    bump_tokenizer_version()
    scramble_pack_magic()
    scramble_encrypted_header_magic()

main()
