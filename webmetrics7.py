__author__ = "Valentino Uberti <vuberti@redhat.com>"

import os
import sys
import time

import socket
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer


def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    output=iter(p.stdout.readline, b'')
    return [x.decode('utf8').strip() for x in output]

def run_cmd():
    command="memstats -r dcpmm-stats -q".split()
    #command="cat outputv7".split()
    return run_command(command)

class Socket:
    name=""
    memory_controller={}
    def __init__(self,name):
        self.name=name
        self.memory_controller={}

    def get_name(self):
        return self.name

    def add_memory_controller(self,value):
        self.memory_controller[value]=MemoryController(value)


    def get_memory_controllers(self):
        return self.memory_controller

    def get_memory_controller(self,value):
        return self.memory_controller[value]

class MemoryController:
    name=""
    channels={}
    def __init__(self,name):
        self.name=name
        self.channels={}

    def get_name(self):
        return self.name

    def add_channel(self,value):
       self.channels[value]=Channel(value)

    def get_channels(self):
        return self.channels
    
    def get_channel(self,value):
        return self.channels[value]
    
class Channel:
    name=""
    metrics={}
    def __init__(self,name):
        self.name=name
        self.metrics={}


    def get_name(self):
        return self.name

    def add_metric(self,metric_name,metric_value):
       self.metrics[metric_name]=(Metric(metric_name,metric_value))

    def get_metrics(self):
        return self.metrics

    def get_metric(self,value):
        return self.metrics[value]

class Metric:
    name=""
    value=[]
    def __init__(self,name,value):
        self.name=name
        self.value=[]
        self.value.append(int(value))

    def add_value(self,value):
        self.value.append(int(value))

    def get_name(self):
        return self.name

    def get_value(self):
        elements=len(self.value)
        total=sum(self.value)
        #print(self.value)
        return int(total/elements)

#socket[x].channel[x].imc[0].metric.values

class EsxiHost():
    sockets={}
    hostname=""
    timestamp=0

    def __init__(self):
        self.hostname=socket.gethostname()
        self.timestamp=int(time.time())
        self.sockets={}

    
    def get_sockets(self):
        return self.sockets

    def get_hostname(self):
        return self.hostname

    def get_socket(self,value):
        return self.sockets[value]


    def add_metric(self,socket,memory_controller,channel,metric,value):

      
        if socket not in self.sockets:
            #print("ADDED SOCKET")
            self.sockets[socket]=Socket(socket)

        if memory_controller not in self.sockets[socket].get_memory_controllers():
            #print("ADDED MEMORY")
            self.sockets[socket].add_memory_controller(memory_controller)
            
        if channel not in  self.sockets[socket].get_memory_controllers()[memory_controller].get_channels():
            #print("ADDED CHANNEL")
            self.sockets[socket].get_memory_controllers()[memory_controller].add_channel(channel)

        if metric not in  self.sockets[socket].get_memory_controllers()[memory_controller].get_channels()[channel].get_metrics():
            self.sockets[socket].get_memory_controllers()[memory_controller].get_channels()[channel].add_metric(metric,value)
            #print(socket,memory_controller,channel,metric,value)
            #print("CREATED : ",value)
        else:
            #print(self.sockets[socket].get_memory_controllers()[memory_controller].get_channels()[channel].get_metrics())
            self.sockets[socket].get_memory_controllers()[memory_controller].get_channels()[channel].get_metrics()[metric].add_value(value)
            #print(socket,memory_controller,channel,metric,value)
            #print("INSERT : ",value)
    def __repr__(self):
        return repr(self.sockets)


class PrometheusMetrics():
    metrics=[]
    metrics_name={}
    openmetrics=[]

    def __init__(self):
        self.metrics=[]
        self.metrics_name={}
        self.openmetrics=[]


    def add_metric(self,hostname,socket,memory_controller,channel,metric,value):
        s="{}{{hostname=\"{}\",socket=\"{}\",memory_controller=\"{}\",channel=\"{}\"}} {}".format(metric,hostname,str(socket),str(memory_controller),str(channel),str(value))
        #print(s)
        self.metrics.append(s)
        self.metrics_name[metric]="# HELP {} Counter".format(metric)

    def get_metrics(self):
        return self.metrics

    def get_openmetrics_metrics(self):
        m=""
        for metric in self.metrics_name:
            m+=self.metrics_name[metric]
            self.openmetrics.append(m)
            for ml in self.metrics:
                
                if metric in ml:
                    if not ml in self.openmetrics:
                      self.openmetrics.append(ml)

                    
            m=""
        
        return self.openmetrics
        

    def get_metrics_name(self):
        return self.metrics_name



################################################################################
#


class MyServer(BaseHTTPRequestHandler):

        
        

    def do_GET(self):

        if self.path !="/metrics":
            self.send_response(500)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()


        esxi_host=EsxiHost()
        prometheus_metrics=PrometheusMetrics()
        for line in run_cmd():
            if "IMC-" in line:
               socket,memory_controller,channel,metric,value=line.split(",")
               esxi_host.add_metric(socket,memory_controller,channel,metric,value)

        
        for s in esxi_host.get_sockets():
            for mc in esxi_host.get_socket(s).get_memory_controllers():
                #print("\t",mc)
                for c in esxi_host.get_socket(s).get_memory_controller(mc).get_channels():
                    #print("\t\t",c)
                    for m in esxi_host.get_socket(s).get_memory_controller(mc).get_channel(c).get_metrics():
                        v = esxi_host.get_socket(s).get_memory_controller(mc).get_channel(c).get_metric(m).get_value()
                        #print("\t\t\t",m,v)
                        prometheus_metrics.add_metric(esxi_host.get_hostname(),s,mc,c,m,v)

        for m in prometheus_metrics.get_openmetrics_metrics():
            self.wfile.write(bytes(m+" \n", "utf-8"))
            

                      
     
        
def main():
   
    hostName = "0.0.0.0"
    serverPort = 9272
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")

   

    

if __name__=="__main__":
    main()




