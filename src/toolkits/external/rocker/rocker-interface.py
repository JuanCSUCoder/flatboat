import inspect
import typing
import rocker

# Default Extensions Imports
import rocker.extensions
import rocker.git_extension
import rocker.nvidia_extension
import rocker.os_detector
import rocker.rmw_extension
import rocker.ssh_extension
import rocker.volume_extension

## BEGIN Open Robotics Topological Extension Sorter - APACHE 2.0 ##

def sort_extensions(extensions, cli_args=""):
  def topological_sort(source: typing.Dict[str, typing.Set[str]]):
    """Perform a topological sort on names and dependencies and returns the sorted list of names."""
    names = set(source.keys())
    # prune optional dependencies if they are not present (at this point the required check has already occurred)
    pending = [(name, dependencies.intersection(names)) for name, dependencies in source.items()]
    emitted = []
    while pending:
      next_pending = []
      next_emitted = []
      for entry in pending:
        name, deps = entry
        deps.difference_update(emitted)  # remove dependencies already emitted
        if deps:  # still has dependencies? recheck during next pass
          next_pending.append(entry)
        else:  # no more dependencies? time to emit
          yield name
          next_emitted.append(name)  # remember what was emitted for difference_update()
        #end if
      #end for
      if not next_emitted:
        raise Exception("Cyclic dependancy detected: %r" % (next_pending,))
      #end if
      pending = next_pending
      emitted = next_emitted
    #end while
  #end def

  extension_graph = {name: cls.invoke_after(cli_args) for name, cls in sorted(extensions.items())}
  active_extension_list = [extensions[name] for name in topological_sort(extension_graph)]
  return active_extension_list
#end def

## END Open Robotics Topological Extension Sorter - APACHE 2.0 ##

# 1. Get Default Extensions Modules
extension_modules = [rocker.extensions, rocker.git_extension, rocker.nvidia_extension, rocker.rmw_extension, rocker.ssh_extension, rocker.volume_extension]


# 2. Get Extensions Classes
print("##### DETECTING EXTENSIONS #####")
extensions_dict = {}
for extension_mod in extension_modules:
  for name, cls in inspect.getmembers(extension_mod):
    if inspect.isclass(cls) and [b.__name__ for b in cls.__bases__][0] == 'RockerExtension':
      print("Extension Class: ", name, " Inherits: ", [b.__name__ for b in cls.__bases__])
      extensions_dict[name] = cls()
    #end if
  #end for
#end for

# TODO: 3. Filter Inactive or Blacklisted Extensions

def generate_dockerfile(extensions, args_dict, base_image):
    extensions = sort_extensions(extensions_dict, cli_args=args_dict)

    dockerfile_str = ''
    # Preamble snippets
    for el in extensions:
        dockerfile_str += '# Preamble from extension [%s]\n' % el.get_name()
        dockerfile_str += el.get_preamble(args_dict) + '\n'
    dockerfile_str += '\nFROM %s\n' % base_image
    # ROOT snippets
    dockerfile_str += 'USER root\n'
    for el in extensions:
        dockerfile_str += '# Snippet from extension [%s]\n' % el.get_name()
        dockerfile_str += el.get_snippet(args_dict) + '\n'
    # Set USER if user extension activated
    if 'user' in args_dict and args_dict['user']:
        if 'user_override_name' in args_dict and args_dict['user_override_name']:
            username = args_dict['user_override_name']
        else:
            username = "flatboat"
        dockerfile_str += f'USER {username}\n'
    # USER snippets
    for el in extensions:
        dockerfile_str += '# User Snippet from extension [%s]\n' % el.get_name()
        dockerfile_str += el.get_user_snippet(args_dict) + '\n'
    return dockerfile_str

def generate_parameters():
  pass
