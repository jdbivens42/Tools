#!/bin/bash
community=public

 echo "Doing snmpwalk for $1"
    #Enumerate Windows Users
    echo "Windows Users:"
    snmpwalk -c $community -v1 "$1" 1.3.6.1.4.1.77.1.2.25

    #Enumerate Running Programs
    echo "Running Programs:"
    snmpwalk -c $community -v1 "$1" 1.3.6.1.2.1.25.4.2.1.2
 
    echo "Installed Software"
    #Enumerate Installed Software
    snmpwalk -c $community -v1 "$1" 1.3.6.1.2.1.25.6.3.1.2

    echo "Storage Units"
    #Enumerate Storage Units
    snmpwalk -c $community -v1 "$1" 1.3.6.1.2.1.25.2.3.1.4
    
    echo "Doing snmp-check for $1"
    snmp-check -c public -v1 "$1"
