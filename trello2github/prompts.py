import sys

def multiple_choice(prompt, options):
    sys.stdout.write('\n' + prompt + '\n\n')
    sys.stdout.write("Choose one of the following:\n")
    for letter, desc in options:
        sys.stdout.write("  {}) {}\n".format(letter, desc))

    x = None
    option_entries = [o[0] for o in options]
    while x not in option_entries:
        sys.stdout.write("[smq]: ")
        x = input().strip()

    return x
