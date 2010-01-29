# -*- coding: UTF-8 -*-
from django.db import models

class Node(models.Model):
    DRIVERS = (
        (u"xen", u"Xen"),
        (u"qemu", u"QEMU / KVM"),
        (u"lxc", u"Linux Containers (LXC)"),
        (u"test", u"Test \"mock\""),
        (u"openvz", u"OpenVZ"),
        (u"uml", u"User Mode Linux"),
        (u"vbox", u"VirtualBox"),
        (u"one", u"Open Nebula"),
        (u"esx", u"VMware ESX"),
        (u"gsx", u"VMware GSX")
    )
    TRANSPORTS = (
        (u"tls", u"TLS 1.0 (SSL 3.1)"),
        (u"unix", u"Unix domain socket"),
        (u"ssh", u"SSH tunneled"),
        (u"ext", u"External program"),
        (u"tcp", u"Unencrypted TCP/IP socket")
    )

    name = models.CharField(max_length = 255, verbose_name = "Node Name")

    # Node connection
    driver = models.CharField(max_length = 6, choices = DRIVERS,
        verbose_name = "Hypervisor Driver")
    address = models.CharField(max_length = 255, null = True, blank = True,
        verbose_name = "Hostname / IP Address")
    port = models.IntegerField(null = True, blank = True, verbose_name = "Port")
    transport = models.CharField(max_length = 4, choices = TRANSPORTS, null = True, blank = True,
        verbose_name = "Used Transport")
    
    username = models.CharField(max_length = 60, null = True, blank = True, verbose_name = "Username")
    path = models.CharField(max_length = 1024, null = True, blank = True, verbose_name = "Path")
    extra_parameters = models.CharField(max_length = 1024, null = True, blank = True, 
        verbose_name = "Extra Parameters")

    def __unicode__(self):
        return self.name
    #enddef

    def getURI(self):
        """
        Generate Libvirt URI format from data
        """
        # Driver
        uri = u"%s" % (self.driver)

        # Transport
        if self.transport: uri += u"+%s" % (self.transport)

        uri += u"://"

        # Username
        if self.username: uri += u"%s@" % (self.username)

        # Hostname / IP address
        if self.address: uri += u"%s" % (self.address)

        # Port
        if self.port: uri += u":%s" % (self.port)

        uri += u"/"

        # Path
        if self.path: uri += u"%s" % (self.path)

        # Extra parameters
        if self.extra_parameters: uri += u"?%s" % (self.extra_parameters)

        return uri
        
    #enddef
    
#endclass