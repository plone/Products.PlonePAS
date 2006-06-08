## Controlled Python Script "validate_emailaddr"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=email=''
##title=Validates an email
##

member=context.portal_membership.getAuthenticatedMember()
if not member.canWriteProperty('email'):
    return state

reg_tool=context.portal_registration

def invalid(field):
    state.setError('email',
        context.translate('You entered an invalid email address.'))

if email and reg_tool.isValidEmail(email):
    pass
else:
    invalid('email')

if state.getErrors():
    status_msg = context.translate('Please correct the indicated errors.')
    return state.set(
        status='failure',
        portal_status_message=status_msg)
else:
    return state

