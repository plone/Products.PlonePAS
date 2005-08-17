## Script (Python) "prefs_user_group_search.py"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=searchstring, restrict, return_form=None, ignore=[]
##title=Valid Search Resriction
##

# CHANGES:
#  use listing like in 2.0.5
#  don't use title_or_name in group search

#MembershipTool.searchForMembers
groups_tool = context.portal_groups
members_tool = context.portal_membership
retlist = []

if not searchstring:
    if restrict != "groups":
        retlist = retlist + members_tool.listMembers()
    if restrict != "users":
        retlist = retlist + groups_tool.listGroups()
else:
    if restrict != "groups":
        retlist = retlist + members_tool.searchForMembers(REQUEST=None, name=searchstring)
    if restrict != "users":
        retlist = retlist + groups_tool.searchForGroups(REQUEST=None, name=searchstring)

if ignore:
  retlist = [r for r in retlist if r not in ignore]

# reorder retlist?
if return_form:
    context.REQUEST.RESPONSE.redirect( context.absolute_url() + '/' + return_form )
return retlist
