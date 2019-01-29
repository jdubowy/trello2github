import sys

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
