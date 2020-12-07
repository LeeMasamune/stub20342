def startswith(s: str, l: list) -> bool:
     for i in l:
          if s.startswith(i):
               return True
     return False

################################################################################

in_dir = r"./Code"

lines_import = []
modules = []
modules_unknown = []

import sys
sys_modules = list(sys.modules.keys())
#sys_modules.sort()
#print(sys_modules)
sys_modules_ext = ["configparser", "dateutil.relativedelta", "gc", "pathlib", "typing" ]

user_modules = [ "utils", "db", "load", "predict", "detect", "report" ]

ignore_modules = sys_modules + sys_modules_ext + user_modules

from pathlib import Path
pathlist = Path(in_dir).rglob("*.py")
for path in pathlist:
     # because path is object not string
     path_str = str(path)
     # print(path_str)

     with open(path_str, "r") as fd:
          line_ct = 0
          for line in fd:
               line_ct += 1
               line = line.strip()
               if line[0:1] == "#": continue # Comment line
               line_lower = line.lower()
               if "import" in line_lower: # import statement
                    # print(f"LN{line_ct}:", line)
                    if not (line in lines_import):
                         lines_import.append(line) # No repeats

                         # Get module name ------------------------------------#
                         if line.startswith("import ") or line.startswith("from "):
                              module_name = line.split()[1]

                              if startswith(module_name, ignore_modules):
                                   continue

                              if not (module_name in modules):
                                   modules.append(module_name)
                         else:
                              modules_unknown.append(line)

# lines_import.sort()
# for line in lines_import:
#      print(line)

print("-" * 80)
modules.sort()
for module_name in modules:
     print(module_name)
