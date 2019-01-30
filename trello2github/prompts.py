import os
import sys
import tempfile

def single_line(prompt, options=None):
    x = None
    while not x or (options and x not in options):
        sys.stdout.write(prompt + ': ')
        x = input().strip()
    return x

def single_line_with_confirmation(prompt):
    while True:
        line = single_line(prompt)
        yn = single_line('Continue with "{}"? [yn]'.format(line),
            options=('y', 'Y', 'n', 'N'))
        if yn.lower() == 'y':
            return line

def multiple_choice(prompt, options):
    options = list(options)
    options.append(('q', 'quit (exit)'))
    prompt = prompt.rstrip('.')
    sys.stdout.write(prompt +".  Choose one of the following:\n")
    for letter, desc in options:
        sys.stdout.write("  {}) {}\n".format(letter, desc))

    option_entries = [str(o[0]) for o in options]
    x = single_line("[{}]".format(','.join(option_entries)), options=option_entries)

    if x == 'q':
        sys.stdout.write("\nGood Bye\n")
        sys.exit(0)

    return x

def edit_in_text_editor(field_name, value):
    with tempfile.NamedTemporaryFile() as fp:
        fp.write('---- {} ----\n\n'.format(field_name).encode())
        fp.write(value.encode() + b'\n')
        fp.flush()

        editor = os.environ.get('EDITOR') or 'vim'
        os.system('{} {}'.format(editor, fp.name))

        fp.seek(0)
        lines = []
        for l in fp.readlines():
            l = l.decode().strip()
            # Accept empty lines after first non-empty line
            if not l.startswith("---- ") and (lines or l):
                lines.append(l)

        return "\n".join(lines)

# if __name__ == "__main__":
#     v = single_line_with_confirmation("Enter your name")
#     print("Your name is {}".format(v))

#     v = multiple_choice("Pick your favorite", [('f','foo'),('b','bar')])
#     print("you chose {}".format(v))