import sys

def multiple_choice(prompt, options):
    sys.stdout.write(prompt + '\n\n')
    sys.stdout.write("Choose one of the following:\n")
    for letter, desc in options:
        sys.stdout.write("  {}) {}\n".format(letter, desc))

    x = None
    while x not in ('s', 'm', 'q'):
        sys.stdout.write("[smq]: ")
        x = input().strip()
