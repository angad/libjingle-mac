#!/usr/bin/python2.4
# Copyright 2009, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Publish tool for SCons."""


# List of published resources.  This is a dict indexed by group name.  Each
# item in this dict is a dict indexed by resource type.  Items in that dict
# are lists of files for that resource.
__published = {}

#------------------------------------------------------------------------------


class PublishItem(object):
  """Item to be published."""

  def __init__(self, source, subdir):
    """Initialize object.

    Args:
      source: Source node.
      subdir: If not None, subdirectory to copy node into in
          ReplicatePublished().
    """
    object.__init__(self)
    self.source = source
    self.subdir = subdir

#------------------------------------------------------------------------------


def _InitializePublish(env):
  """Re-initializes published resources.

  Args:
    env: Parent environment
  """
  env=env     # Silence gpylint

  # Clear the dict of published resources
  __published.clear()


def ReplicatePublished(env, target, group_name, resource_type):
  """Replicate published resources for the group to the target directory.

  Args:
    env: Environment in which this function was called.
    target: Target directory for resources.
    group_name: Name of resource group, or a list of names of resource groups.
    resource_type: Type of resources (string), or a list of resource types.

    Uses the subdir parameter passed to Publish() when replicating source nodes
    to the target.

  Returns:
    The list of target nodes from the calls to Replicate().

  Since this is based on Replicate(), it will also use the REPLICATE_REPLACE
  variable, if it's set in the calling environment.
  """
  target_path = env.Dir(target).abspath
  source_list = env.GetPublishedWithSubdirs(group_name, resource_type)
  dest_nodes = []
  for source in source_list:
    # Add the subdir if there is one in the source tuple.
    if source[1]:
      dest_nodes += env.Replicate(target_path + '/' + source[1], source[0])
    else:
      dest_nodes += env.Replicate(target_path, source[0])
  return dest_nodes


def GetPublishedWithSubdirs(env, group_name, resource_type):
  """Returns a list of the published resources of the specified type.

  Args:
    env: Environment in which this function was called.
    group_name: Name of resource group, or a list of names of resource groups.
    resource_type: Type of resources (string), or a list of resource types.

  Returns:
    A flattened list of the source nodes from calls to Publish() for the
        specified group and resource type.  Each source node is represented
        by a pair consisting of (source_node, subdir). Returns an empty list
        if there are no matching resources.
  """
  source_list = []
  for group in env.SubstList2(group_name):
    # Get items for publish group and resource type
    for resource in env.SubstList2(resource_type):
      items = __published.get(group, {}).get(resource, [])
      for i in items:
        source_list.append((i.source, i.subdir))

  return source_list


def GetPublished(env, group_name, resource_type):
  """Returns a list of the published resources of the specified type.

  Args:
    env: Environment in which this function was called.
    group_name: Name of resource group, or a list of names of resource groups.
    resource_type: Type of resources (string), or a list of resource types.

  Returns:
    A flattened list of the source nodes from calls to Publish() for the
        specified group and resource type.  Returns an empty list if there are
        no matching resources.
  """
  source_list = env.GetPublishedWithSubdirs(group_name, resource_type)
  return [source[0] for source in source_list]


def Publish(env, group_name, resource_type, source, subdir=None):
  """Publishes resources for use by other scripts.

  Args:
    env: Environment in which this function was called.
    group_name: Name of resource group.
    resource_type: Type of resources (string).
    source: Source file(s) to copy.  May be a string, Node, or a list of
        mixed strings or Nodes.  Strings will be passed through env.Glob() to
        evaluate wildcards.  If a source evaluates to a directory, the entire
        directory will be recursively copied.
    subdir: Subdirectory to which the resources should be copied, relative to
        the primary directory for that resource type, if not None.
  """
  if subdir is None:
    subdir = ''         # Make string so we can append to it

  # Evaluate SCons variables in group name
  # TODO: Should Publish() be able to take a list of group names and publish
  # the resource to all of them?
  group_name = env.subst(group_name)

  # Get list of sources
  items = []
  for source_entry in env.Flatten(source):
    if isinstance(source_entry, str):
      # Search for matches for each source entry
      # TODO: Should generate an error if there were no matches?  But need to
      # skip this warning if this is a recursive call to env.Publish() from
      # below.
      source_nodes = env.Glob(source_entry)
    else:
      # Source entry is already a file or directory node; no need to glob it
      source_nodes = [source_entry]
    for s in source_nodes:
      if str(s.__class__) == 'SCons.Node.FS.Dir':
        # Recursively publish all files in subdirectory.  Since glob('*')
        # doesn't match dot files, also glob('.*').
        env.Publish(group_name, resource_type,
                    [s.abspath + '/*', s.abspath + '/.*'],
                    subdir=subdir + '/' + s.name)
      else:
        items.append(PublishItem(s, subdir))

  # Publish items, if any
  if items:
    # Get publish group
    if group_name not in __published:
      __published[group_name] = {}
    group = __published[group_name]
    if resource_type not in group:
      group[resource_type] = []

    # Publish items into group
    group[resource_type] += items


def generate(env):
  # NOTE: SCons requires the use of this name, which fails gpylint.
  """SCons entry point for this tool."""

  # Defer initializing publish, but do before building SConscripts
  env.Defer(_InitializePublish)
  env.Defer('BuildEnvironmentSConscripts', after=_InitializePublish)

  env.AddMethod(GetPublishedWithSubdirs)
  env.AddMethod(GetPublished)
  env.AddMethod(Publish)
  env.AddMethod(ReplicatePublished)
