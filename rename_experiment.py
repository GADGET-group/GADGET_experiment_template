#!/usr/bin/env python3
'''
Turn the experiment template into the repository of one experiment:

    python3 rename_experiment.py e26001          # do it
    python3 rename_experiment.py e26001 -n       # only print what it would do

renames EXPERIMENT_analysis/ -> e26001_analysis/ and EXPERIMENT_runs.py -> e26001_runs.py (every file or folder
whose name contains the placeholder), and replaces the placeholder word EXPERIMENT in every text file of the
repository (pyproject.toml, README files, the runs module, .gitignore, configs). It skips .git/, __pycache__/,
binary files and itself, refuses when a target name already exists, and prints what it did. Standard library only.
'''
import argparse
import os
import re
import sys

TOKEN = 'EXPERIMENT'
SKIP_DIRS = {'.git', '__pycache__'}


def text_of(path):
    '''file contents as str, or None for a binary (NUL bytes or not UTF-8) file'''
    with open(path, 'rb') as f:
        data = f.read()
    if b'\0' in data:
        return None
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return None


def walk(root, self_path):
    '''(directories, files) under root, absolute paths, skipping SKIP_DIRS, *.egg-info and this script'''
    dirs, files = [], []
    for here, subdirs, names in os.walk(root):
        subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS and not d.endswith('.egg-info'))
        dirs.extend(os.path.join(here, d) for d in subdirs)
        files.extend(os.path.join(here, n) for n in sorted(names)
                     if os.path.realpath(os.path.join(here, n)) != self_path)
    return dirs, files


def main():
    ap = argparse.ArgumentParser(description='Rename the experiment template for one experiment.')
    ap.add_argument('name', help='experiment name, for example e26001')
    ap.add_argument('-n', '--dry-run', action='store_true', help='print what would be done, change nothing')
    args = ap.parse_args()
    name = args.name
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
        sys.exit(f'{name!r} is not a valid experiment name: {name}_analysis must be a Python package name '
                 '(letters, digits and underscores, starting with a letter)')
    if TOKEN in name:
        sys.exit(f'the experiment name must not contain {TOKEN}')

    root = os.path.dirname(os.path.realpath(__file__))
    self_path = os.path.realpath(__file__)
    package = os.path.join(root, f'{TOKEN}_analysis')
    if not os.path.isdir(package):
        sys.exit(f'{package} not found: the template has already been renamed (or this is not the template)')

    dirs, files = walk(root, self_path)

    # renames: every file or folder whose own name contains the token, deepest first so that a folder is renamed
    # after the files in it
    renames = []
    for path in dirs + files:
        base = os.path.basename(path)
        if TOKEN in base:
            renames.append((path, os.path.join(os.path.dirname(path), base.replace(TOKEN, name))))
    renames.sort(key=lambda r: r[0].count(os.sep), reverse=True)
    clashes = [new for _, new in renames if os.path.lexists(new)]
    if clashes:
        sys.exit('refusing, these already exist:\n  ' + '\n  '.join(os.path.relpath(c, root) for c in clashes))

    # contents
    edits = []
    for path in files:
        text = text_of(path)
        if text is not None and TOKEN in text:
            edits.append((path, text.count(TOKEN), text.replace(TOKEN, name)))

    verb = 'would' if args.dry_run else ''
    for path, count, new_text in edits:
        print(f'{verb + " " if verb else ""}replace {count} x {TOKEN} -> {name} in {os.path.relpath(path, root)}')
        if not args.dry_run:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(new_text)
    for old, new in renames:
        print(f'{verb + " " if verb else ""}rename {os.path.relpath(old, root)} -> {os.path.relpath(new, root)}')
        if not args.dry_run:
            os.rename(old, new)
    if args.dry_run:
        print('dry run: nothing changed')
    else:
        print(f'done: {len(edits)} files edited, {len(renames)} paths renamed. Next: README.md, step 3. '
              'This script can be deleted now.')


if __name__ == '__main__':
    main()
