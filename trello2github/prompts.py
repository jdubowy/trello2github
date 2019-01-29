import os
import sys
import tempfile

def multiple_choice(prompt, options):
    options = list(options)
    options.append(('q', 'quit (exit)'))
    sys.stdout.write('\n' + prompt + '\n\n')
    sys.stdout.write("Choose one of the following:\n")
    for letter, desc in options:
        sys.stdout.write("  {}) {}\n".format(letter, desc))

    x = None
    option_entries = [str(o[0]) for o in options]
    while x not in option_entries:
        sys.stdout.write("[{}]: ".format(','.join(option_entries)))
        x = input().strip()

    if x == 'q':
        sys.stdout.write("\nGood Bye\n")
        sys.exit(0)

    return x

def edit_in_text_editor(field_name, value):
    with tempfile.NamedTemporaryFile() as fp:
        fp.write('---- {} ----\n\n'.format(field_name).encode())
        fp.write(value.encode() + b'\n')
        fp.flush()

        os.system('emacs {}'.format(fp.name))

        fp.seek(0)
        lines = []
        for l in fp.readlines():
            l = l.decode().strip()
            # Accept empty lines after first non-empty line
            if not l.startswith("---- ") and (lines or l):
                lines.append(l)

        return "\n".join(lines)

if __name__ == "__main__":
    val = edit_in_text_editor("foo", "bar")
    print("New val is {}:\n".format(val))
