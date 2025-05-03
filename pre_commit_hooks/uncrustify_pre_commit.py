import sys
import os
import subprocess
import argparse
import difflib


# get the lines that are different in each file
# each line begins with '+' for each line that is in f2 but not in f1
# each line begins with '-' for each line that is in f1 but not f2
def get_diff(f1, f2, filename, newline='\n'):
  return newline.join(difflib.unified_diff(f1.split(newline), f2.split(newline), filename + '-original', filename + '-formatted', lineterm=newline, n=0))


def main():
  # arguments that can be passed in by pre-commit
  parser = argparse.ArgumentParser()

  # specify the config file used by uncrustify
  parser.add_argument('--config', help='config file for uncrustify', required=False)

  # if strict mode is selected than the files will not be fixed automatically and the commit will fail
  parser.add_argument('--strict', action='store_true', help='force commit to fail if format is wrong instead of correcting the files automatically')

  # the files that are changed in the commit 
  parser.add_argument('filenames', nargs='*', help='Filenames to fix')

  args = parser.parse_args()

  config = 'test.cfg'
  if(args.config):
    config = args.config
    os.environ['PATH'] += os.pathsep + os.path.join(os.path.dirname(os.path.abspath(args.config)), 'bin')

  style_violations = False
  for filename in args.filenames:

    with open(filename, 'rb') as f: raw_content = f.read()

    # Test to see if uncrustify cmd is available
    from shutil import which
    if which('uncrustify') is None:
      print('The "uncrustify" command is not available on path. Please install uncrustify and add it to the default path.')
      print('For Windows, binaries can be downloaded directly from the uncrustify repo here:')
      print('  https://sourceforge.net/projects/uncrustify/files/')
      print('For Linux, you should be able to install uncrustify using your package manager.')
      print('  eg: "sudo apt install uncrustify" on a Debian system.')
      sys.exit(1)

    # pipe file contents to uncrustify
    p = subprocess.Popen(['uncrustify', '-c', config], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    corrected_content, error_output = p.communicate(input=raw_content)
    corrected_content = corrected_content.decode()
    error_output = error_output.decode()

    if(p.returncode > 0):
      print('There was an error running uncrustify')
      print(error_output)
      sys.exit(1)

    # determine what lines must change
    diff = get_diff(raw_content.decode(), corrected_content, filename=filename)

    # if there are lines to change
    if(diff != ''):
      print ('=============================================')
      print ('file: \'{f}\''.format(f=filename))
      print ('---------------------------------------------')
      print (diff)
      print ('=============================================')
      style_violations = True

      # if strict mode isn't enabled
      if not args.strict:
        print ('writing fixes to \'{f}\''.format(f=filename))
        f = open(filename, 'wb')
        f.write(corrected_content.encode())
        f.close()


  if (style_violations and args.strict):
    print ('\n\ncommit failed - coding style violations were found\n')
    sys.exit(1)

  sys.exit(0)

if __name__ == '__main__':
  sys.exit(main())
