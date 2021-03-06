# -*- coding: UTF-8 -*-

import sha, time ,datetime

from django.core.urlresolvers       import reverse
from django.db                      import transaction
from django.http                    import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts               import render_to_response, get_object_or_404
from django.template                import RequestContext
from django.utils                   import simplejson
from django.utils.translation       import ugettext as _

from webPyVirt.decorators       import secure
from webPyVirt.libs             import virtualization, toxml

from webPyVirt.domains.models       import Domain, Disk, Interface, InputDevice
from webPyVirt.domains.permissions  import isAllowedTo

from webPyVirt.nodes.permissions    import isAllowedTo as nodeIsAllowedTo
from webPyVirt.nodes.models         import Node
from webPyVirt.nodes.misc           import getNodes

@transaction.commit_on_success
def add(request):
    if request.method != "POST" or "secret" not in request.POST or "action" not in request.POST:
        return HttpResponseRedirect("%s" % (reverse("403")))
    #endif

    secret = request.POST['secret']
    action = request.POST['action']

    permis = request.session.get("domains.domain.add", {})
    if secret not in permis:
        return HttpResponseRedirect("%s" % (reverse("403")))
    #endif

    domainData = permis[secret][1]
    domain = domainData['domain']
    node = domain.node

    if not nodeIsAllowedTo(request, node, "add_domain"):
        return HttpResponseRedirect("%s" % (reverse("403")))
    #endif

    data = {
        "status":           200,
        "statusMessage":    _("OK")
    }

    if action == "nodeCheck":
        try:
            virNode = virtualization.virNode(node)
            result = virNode.getInfo()
        except virtualization.ErrorException, e:
            data['nodeStatus'] = False
            data['error'] = unicode(e)
        else:
            data['nodeStatus'] = True
            data['info'] = result
            try:
                freeMemory = virNode.getFreeMemory()
            except virtualization.ErrorException, e:
                data['info']['freeMemory'] = -1
            else:
                data['info']['freeMemory'] = freeMemory
            #endtry
        #endtry
        data['name'] = node.name
        data['uri'] = node.getURI()
    elif action == "loadMetadata":
        data['name'] = domain.name
        data['uuid'] = domain.uuid
        data['description'] = domain.description
    elif action == "saveMetadata":
        domain.name = request.POST['name']
        domain.uuid = request.POST['uuid']
        domain.description = request.POST['description']
    elif action == "loadMemory":
        if domain.memory:
            data['memory'] = domain.memory / 1024
        else:
            data['memory'] = domain.memory
        #endif
        data['vcpu'] = domain.vcpu
    elif action == "saveMemory":
        domain.memory = int(request.POST['memory']) * 1024
        domain.vcpu = int(request.POST['vcpu'])
    elif action == "loadVolumes":
        pool = domainData['pool']
        try:
            virNode = virtualization.virNode(node)
            poolInfo = virNode.getStoragePoolInfo(pool)
            result = virNode.listStorageVolumes(pool)
            volumes = [ {
                    "value":        volume,
                    "label":        "%s (%.2f GB)" % \
                        (volume, (float(virNode.getStorageVolumeInfo(pool, volume)['capacity']) / (1024 * 1024 * 1024)))
                } for volume in result ]
        except virtualization.ErrorException, e:
            data['error'] = unicode(e)
        else:
            data['poolInfo'] = poolInfo
            data['volumes'] = volumes
        #endtry

        if "volume" in domainData:
            data['volume'] = domainData['volume']
        #endif
    elif action == "saveVolumes":
        if "volume" in request.POST:
            domainData['volume'] = request.POST['volume']
        #endif
        if "volumeAction" in request.POST:
            volumeAction = int(request.POST['volumeAction'])
        else:
            volumeAction = None
        #endif
        if volumeAction == 0:
            volSize = float(request.POST['size'])
            format = request.POST['format']
            newVolume = toxml.newStorageVolumeXML(domainData['volume'], volSize, format)
            try:
                virNode = virtualization.virNode(node)
                result = virNode.createStorageVolume(domainData['pool'], newVolume)
            except virtualization.ErrorException, e:
                data['created'] = False
                data['error'] = unicode(e)
            else:
                data['created'] = True
            #endtry
        #endif
    elif action == "loadStoragePools":
        try:
            virNode = virtualization.virNode(node)
            result = virNode.listStoragePools()
            pools = [ {
                "value":    poolName,
                "label":    "%s (free %.2f GB)" % \
                    (poolName, (float(virNode.getStoragePoolInfo(poolName)['available']) / (1024 * 1024 * 1024)))
                } for poolName in result ]
        except virtualization.ErrorException, e:
            data['nodeStatus'] = False
            data['error'] = unicode(e)
        else:
            data['storagePools'] = pools
        #endtry

        if "pool" in domainData:
            data['pool'] = domainData['pool']
        #endif
    elif action == "saveStoragePools":
        domainData['pool'] = request.POST['pool']
        if "type" in request.POST:
            domainData['poolType'] = request.POST['type']
        #endif
    elif action == "saveNewStoragePool":
        poolName = domainData['pool']
        poolType = domainData['poolType']
        targetPath = request.POST['targetPath']
        if request.POST['format'] == "":
            format = None
        else:
            format = request.POST['format']
        #endif
        if request.POST['hostname'] == "":
            hostname = None
        else:
            hostname = request.POST['hostname']
        #endif
        if request.POST['sourcePath'] == "":
            sourcePath = None
        else:
            sourcePath = request.POST['sourcePath']
        #endif
        newPool = toxml.newStoragePoolXML(poolName, poolType, targetPath, format, hostname, sourcePath)
        try:
            virNode = virtualization.virNode(node)
            result = virNode.createStoragePool(newPool)
        except virtualization.ErrorException, e:
            data['poolCreated'] = False
            data['error'] = unicode(e)
        else:
            data['poolCreated'] = True
            data['poolInfo'] = result
        #endtry
    elif action == "loadNetwork":
        if "network" in domainData:
            network = domainData['network']
            data['mac'] = network['mac']
            data['name'] = network['name']
            data['targetDev'] = network['targetDev']
        #endif
        try:
            virNode = virtualization.virNode(node)
            result = virNode.listNetworks()
        except virtualization.ErrorException, e:
            data['error'] = unicode(e)
        else:
            data['networks'] = result
        #endtry
    elif action == "saveNetwork":
        network = {
            "name":         request.POST['network']
        }
        if "mac" in request.POST and len(request.POST['mac']):
            network['mac'] = request.POST['mac']
        else:
            network['mac'] = None
        #endif
        if "targetDev" in request.POST and len(request.POST['targetDev']):
            network['targetDev'] = request.POST['targetDev']
        else:
            network['targetDev'] = None
        #endif

        domainData['network'] = network
    elif action == "loadReview":
        data['name'] = domain.name
        data['uuid'] = domain.uuid
        data['memory'] = domain.memory
        data['vcpu'] = domain.vcpu
        try:
            virNode = virtualization.virNode(node)
            result = virNode.getStorageVolumeInfo(domainData['pool'], domainData['volume'])
        except virtualization.ErrorException, e:
            data['error'] = unicode(e)
        else:
            data['volume'] = result
        #endtry
        data['network'] = domainData['network']
    elif action == "create":
        try:
            virNode = virtualization.virNode(node)
            volInfo = virNode.getStorageVolumeInfo(domainData['pool'], domainData['volume'])
        except virtualization.ErrorException, e:
            data['error'] = unicode(e)
        else:
            try:
                if domain.hypervisor_type == "xen":
                    domain.os_type = "xen"
#                elif domain.hypervisor_type == "qemu":
#                    domain.os_type = "qemu"
                else:
                    domain.os_type = "hvm"
                #endif

                disk = Disk()
                disk.domain = domain

                # Disk Type
                if volInfo['type'] == virtualization.STORAGE_VOL_FILE:
                    disk.type = "file"
                elif volInfo['type'] == virtualization.STORAGE_VOL_BLOCK:
                    disk.type = "block"
                #endif

                # Disk Device
                disk.device = "disk"
                disk.source = volInfo['path']
                disk.target_dev = "hda"

                # Network
                interface = Interface()
                interface.domain = domain
                interface.type = "network"
                interface.mac_address = domainData['network']['mac']
                interface.source_network = domainData['network']['name']
                interface.target_dev = domainData['network']['targetDev']

                # Input device
                inputDev = InputDevice()
                inputDev.domain = domain
                inputDev.type = "mouse"
                inputDev.bus = "ps2"

                newDomain = toxml.newDomainXML(domain, disk, interface, inputDev)
                data['xml'] = newDomain
                domainCon = virNode.createDomain(newDomain)
                domModel = domainCon.getModel()
                domDevices = domainCon.getDevices()

                # Save to database
                domModel.owner = request.user
                domModel.node = node
                domModel.save()
                for devType, devs in domDevices.items():
                    for device in devs:
                        device.domain = domModel
                        device.save()
                    #endfor
                #endfor

            except virtualization.ErrorException, e:
                data['error'] = unicode(e)
            else:
                data['created'] = True
                data['id'] = domModel.id
            #endtry
        #endtry
    else:
        data['status'] = 404
        data['statusMessage'] = _("Action not found!")
    #endif

    domainData['domain'] = domain
    permis[secret] = (time.time(), domainData)
    request.session['domains.domain.add'] = permis

    return HttpResponse(simplejson.dumps(data))
#enddef

@transaction.commit_on_success
def migrate(request):
    if request.method != "POST" or "secret" not in request.POST or "action" not in request.POST:
        return HttpResponseRedirect("%s" % (reverse("403")))
    #endif

    secret = request.POST['secret']
    action = request.POST['action']

    permis = request.session.get("domains.domain.migrate", {})
    if secret not in permis:
        return HttpResponseRedirect("%s" % (reverse("403")))
    #endif

    domainData = permis[secret][1]
    domain = domainData['domain']

    if not isAllowedTo(request, domain, "migrate_domain"):
        return HttpResponseRedirect("%s" % (reverse("403")))
    #endif

    data = {
        "status":           200,
        "statusMessage":    _("OK")
    }

    if action == "nodeList":
        # Ziskaj zoznam uzlov, na ktore mas pravo "add_domain"
        nodes = getNodes(request, "add_domain")
        # Filtruj iba uzle, ktore maju rovnaky hypervizor
        nodes = nodes.filter(driver=domain.node.driver).exclude(name=domain.node.name)
        # Vsetky otestuje na status
        availNodes = []
        for node in nodes:
            try:
                virNode = virtualization.virNode(node)
                result = virNode.getInfo()
            except:
                continue
            finally:
                availNodes.append(node)
            #endtry
        #endfor

        data['nodes'] = [ {
            "label": node.name,
            "value": node.id
        } for node in availNodes ]
    elif action == "migrate":
        # Premigruje sa domena a v DB sa zmeni odkaz na node
        nodeId = int(request.POST['node'])
        node = get_object_or_404(Node, id=nodeId)
        try:
            virDomain = virtualization.virDomain(domain)
            virDomain.migrate(node)
        except virtualization.ErrorException, e:
            data['error'] = unicode(e)
        else:
            domain.node = node
            data['migrated'] = True
            data['id'] = domain.id
        #endtry
    else:
        data['status'] = 404
        data['statusMessage'] = _("Action not found!")
    #endif


    domainData['domain'] = domain
    permis[secret] = (time.time(), domainData)
    request.session['domains.domain.migrate'] = permis

    return HttpResponse(simplejson.dumps(data))
#enddef
