# -*- coding: UTF-8 -*-

from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from webPyVirt.domains.permissions  import *
from webPyVirt.nodes.permissions    import *

def MENU(request):
    changeAcls = canChangeAcls(request)
    viewDomains = canViewDomains(request)
    removeDomains = canRemoveDomains(request)
    editDomains = canEditDomains(request)
    addDomains = canAddDomains(request)
    migrateDomains = canMigrateDomains(request)

    return [
        {   # Section domain
            "hide":         False,
            "label":        _("Domains"),
            "items":        [
                {   # Add domain
                    "hide":     not addDomains,
                    "label":    _("Add domain"),
                    "url":      "domain_add__select_node"
                },
                {   # Domain detail
                    "hide":     not viewDomains,
                    "label":    _("Domain detail"),
                    "url":      "domain_detail__select_domain"
                },
                {   # Edit domain
                    "hide":     not editDomains,
                    "label":    _("Edit domain"),
                    "url":      "domain_edit__select_domain"
                },
                {   # Edit domain
                    "hide":     not migrateDomains,
                    "label":    _("Migrate domain"),
                    "url":      "domain_migrate__select_domain"
                },
                {   # Remove domain
                    "hide":     not removeDomains,
                    "label":    _("Remove domain"),
                    "url":      "domain_remove__select_domain"
                },
            ]
        },
        {   # Section permissions
            "hide":         False,
            "label":        _("Permissions"),
            "items":        [
                {   # User ACL
                    "hide":     not changeAcls,
                    "label":    _("User ACL"),
                    "selected": r"acl/user/",
                    "url":      "acl_user__select_domain"
                },
                {   # Group ACL
                    "hide":     not changeAcls,
                    "label":    _("Group ACL"),
                    "selected": r"acl/group/",
                    "url":      "acl_group__select_domain"
                },

            ]
        }
    ]
#enddef
