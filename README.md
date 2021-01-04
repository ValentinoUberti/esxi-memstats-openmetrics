# Memstats openmetrics for ESXI v7

- How to run

Copy webmetrics7.py to the Esxi vm

Create the firewall service:

Filename: /etc/vmware/firewall/metrics.xml

```
<ConfigRoot>

<!-- Metrics inbound 9272/tcp -->
 <service id='0045'>                                               
    <id>metrics</id>                                                         
    <rule id='0000'>                   
      <direction>inbound</direction> 
      <protocol>tcp</protocol>         
      <porttype>dst</porttype>       
      <port>                                                        
        <begin>9272</begin>                                              
        <end>9272</end>              
      </port>                         
    </rule>                            
    <enabled>true</enabled>         
    <required>true</required>                                      
  </service>     

</ConfigRoot>

```

Refresh the firewall rules:

```
esxcli network firewall refresh

```

Run the metrics exporter:

```
python webmetrics7.py
```