from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto.ofproto_v1_3_parser import OFPMatch
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.packet import ether_types
from ryu.lib.packet import in_proto as inet
from ryu.lib import dpid as dpid_lib
from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp
from ryu.lib.packet import tcp
from ryu.lib.packet import udp

"""
SCC365 | Base L2 Learning Switch (Week 12)

You should follow the task sheet provided for you on moodle.
This acts simply as a hub for now, but, if expanded, will function 
as a L2 learning switch.
"""

class LearningSwitch(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION] # Use OF v1_3 for this module!

    def __init__(self, *args, **kwargs):
        ''' Create instance of the controller '''
        super(LearningSwitch, self).__init__(*args, **kwargs)
        self.mac_dic={}                       # the dictionary to store mac info

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        ''' Handle Configuration Changes '''
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        print("EVENT: Switch added || dpid: 0x%09x"%(datapath.id))
        self.add_flow_default(datapath, 0, match, actions)    # default flow entry, no idle time/hard time

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        ''' Handle Packet In OpenFlow Events '''
        self.logger.info("EVENT: PACKET IN")

        ## Collect EVENT data
        msg = ev.msg                                        # The message containing all the data needed from the openflow event
        datapath = ev.msg.datapath                          # The switch (datapath) that the event came from
        ofproto = datapath.ofproto                          # OF Protocol lib to be used with the OF version on the switch
        parser = datapath.ofproto_parser                    # OF Protocol Parser that matches the OpenFlow version on the switch
        dpid = datapath.id                                  # ID of the switch (datapath) that the event came from
        self.mac_dic.setdefault(dpid,{})                    # using dpid to initialize

        ## Collect packet data and output packet info
        pkt=packet.Packet(msg.data)                         # The packet relating to the event (including all of its headers)
        eth=pkt.get_protocols(ethernet.ethernet)[0]         # get the eth header
        src=eth.src                                         # source mac address
        dst=eth.dst                                         # dest mac address
        in_port = msg.match['in_port']                      # The port that the packet was received on the switch
        self.logger.info("From datapath %s, from source %s,to dest %s, in port is %s",dpid,src,dst,in_port)

        ## match src and the packet in port
        ## if dest in the dictionary of dpid(switch id), then find the port by dest
        ## else flood the packet
        self.mac_dic[dpid][src]=in_port                     
        if dst in self.mac_dic[dpid]:
            out_port=self.mac_dic[dpid][dst]
        else:
            out_port=ofproto.OFPP_FLOOD

        ## set the action, type is output:port
        ## consider protocol from low to high layer
        ## get the match according to protocol
        ## output info
        actions=[parser.OFPActionOutput(out_port)]
        if out_port!=ofproto.OFPP_FLOOD:    
            # first match ip in the ethertype field
            if eth.ethertype==ether_types.ETH_TYPE_IP:
                ip=pkt.get_protocol(ipv4.ipv4)      
                # protocol is ICMP, get match directly
                if ip.proto==in_proto.IPPROTO_ICMP:
                    match=parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ipv4_src=ip.src,ipv4_dst=ip.dst,ip_proto=ip.proto)
                    self.logger.info("PACKET OUT: source ip is %s, dest ip is %s, To switch %s port %s",
                                      ip.src,ip.dst,dpid,out_port)
                # protocol is TCP, first get info of packet, then match
                elif ip.proto==in_proto.IPPROTO_TCP:
                    tcpinfo=pkt.get_protocol(tcp.tcp)
                    match=parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ipv4_src=ip.src,ipv4_dst=ip.dst,ip_proto=ip.proto,
                                          tcp_src=tcpinfo.src_port,tcp_dst=tcpinfo.dst_port)
                    self.logger.info("PACKET OUT: source ip and port is %s,%s, dest ip and port is %s,%s,to switch %s port %s",
                                      ip.src,tcpinfo.src_port,ip.dst,tcpinfo.dst_port,dpid,out_port)
                # protocol is UDP, first get info of packet, then match
                elif ip.proto==in_proto.IPPROTO_UDP:
                    udpinfo=pkt.get_protocol(udp.udp)
                    match=parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,ipv4_src=ip.src,ipv4_dst=ip.dst,ip_proto=ip.proto,
                                          udp_src=udpinfo.src_port,udp_dst=udpinfo.dst_port)
                    self.logger.info("PACKET OUT: source ip and port is %s,%s, dest ip and port is %s,%s,to switch %s port %s",
                                      ip.src,udpinfo.src_port,ip.dst,udpinfo.dst_port,dpid,out_port)
                    
                self.add_flow(datapath,100,1,match,actions)   # set idle_time=100s
        else:
            self.logger.info("PACKET OUT: Flooding")

        # The action of sending a packet out converted to the correct OpenFlow format
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
        return

    def add_flow(self, datapath, idle_time,priority, match, actions):
        ''' Write to the Datapath's flow-table '''
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        ## create a new mod and send it to datapath
        ## add idle_timeout, delete the entry if it isn't used for long time
        mod = parser.OFPFlowMod(datapath=datapath, idle_timeout=idle_time, priority=priority,match=match, instructions=inst)
        self.logger.info("FLOW MOD: Written")
        datapath.send_msg(mod)

    def add_flow_default(self, datapath, priority, match, actions):
        ''' Write to the Datapath's flow-table '''
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        ## create a new mod and send it to datapath
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,match=match, instructions=inst)
        self.logger.info("FLOW MOD: Written")
        datapath.send_msg(mod)