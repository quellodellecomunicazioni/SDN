# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import dpid as dpid_lib
from ryu.lib import stplib
from ryu.lib.packet import packet, ether_types
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp, mpls
from ryu.app import simple_switch_13
from ryu.topology import switches
from ryu.topology import event as topo_event
from ryu.topology.api import get_switch, get_link, get_host
import networkx as nx
import matplotlib.pyplot as plt
import random


class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'stplib': stplib.Stp}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.stp = kwargs['stplib']
        self.net = nx.DiGraph()
        self.lsps = {}
        self.label_list = []
        self.path_list = []

        # Sample of stplib config.
        #  please refer to stplib.Stp.set_config() for details.
        config = {dpid_lib.str_to_dpid('0000000000000001'):
                  {'bridge': {'priority': 0x8000}},
                  dpid_lib.str_to_dpid('0000000000000002'):
                  {'bridge': {'priority': 0x9000}},
                  dpid_lib.str_to_dpid('0000000000000003'):
                  {'bridge': {'priority': 0xa000}}}
        self.stp.set_config(config)

    def delete_flow(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        for dst in self.mac_to_port[datapath.id].keys():
            match = parser.OFPMatch(eth_dst=dst)
            mod = parser.OFPFlowMod(
                datapath, command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY,
                priority=1, match=match)
            datapath.send_msg(mod)

    @set_ev_cls(stplib.EventPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        arp_pkt = pkt.get_protocol(arp.arp)
        mpls_pkt = pkt.get_protocol(mpls.mpls)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        out_port = ofproto.OFPP_FLOOD

        if arp_pkt:
            if src not in self.net:
                self.net.add_node(src)
                self.net.add_edge(src,dpid)
                self.net.add_edge(dpid,src,port=in_port)
                nx.draw(self.net, with_labels=True)
                plt.savefig("grafo.png")
                plt.clf()
                print "Ho aggiunto ", src
                print "ora i nodi sono ", self.net.nodes()
                print "ora i collegamenti sono ", self.net.edges()
        elif mpls_pkt:
            print "pacchetto MPLS"
            out_port = ofproto.OFPP_FLOOD
        else:
            if dst in (self.net) and (src in self.net):
                try: 
                    path = nx.shortest_path(self.net, src, dst)
                    if path not in self.path_list:
                        self.path_list.append(path)
                        label = self.assign_label()
                        self.lsps[str(label)] = nx.shortest_path(self.net, 
                                                                 src, dst)
                        for key,value in self.lsps.iteritems():
                            print key,value
                        print "----------------------"
                        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_MPLS, mpls_label=label)
                        next = path[path.index(dpid) + 1]
                        out_port = self.net[dpid][next]['port']
                        actions = [parser.OFPActionPushMpls(),
                                   parser.OFPActionSetField(mpls_label=label),
                                   parser.OFPActionOutput(out_port)]
                        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                        mod = parser.OFPFlowMod(datapath=datapath, priority=2, match=match, instructions=inst)
                        datapath.send_msg(mod)
                except nx.NetworkXNoPath: 
                    print "no path"
                    out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    def assign_label(self):
        if not self.label_list:
            new_label = random.randint(1, 1000)
        else:
            new_label = random.randint(1, 1000)
            while new_label in self.label_list:
                new_label = random.randint(1, 1000)
        self.label_list.append(new_label)
        return new_label

    @set_ev_cls(stplib.EventTopologyChange, MAIN_DISPATCHER)
    def _topology_change_handler(self, ev):
        dp = ev.dp
        dpid_str = dpid_lib.dpid_to_str(dp.id)
        msg = 'Receive topology change event. Flush MAC table.'
        self.logger.debug("[dpid=%s] %s", dpid_str, msg)

        if dp.id in self.mac_to_port:
            self.delete_flow(dp)
            del self.mac_to_port[dp.id]

    @set_ev_cls(stplib.EventPortStateChange, MAIN_DISPATCHER)
    def _port_state_change_handler(self, ev):
        dpid_str = dpid_lib.dpid_to_str(ev.dp.id)
        of_state = {stplib.PORT_STATE_DISABLE: 'DISABLE',
                    stplib.PORT_STATE_BLOCK: 'BLOCK',
                    stplib.PORT_STATE_LISTEN: 'LISTEN',
                    stplib.PORT_STATE_LEARN: 'LEARN',
                    stplib.PORT_STATE_FORWARD: 'FORWARD'}
        self.logger.debug("[dpid=%s][port=%d] state=%s",
                          dpid_str, ev.port_no, of_state[ev.port_state])

    @set_ev_cls(topo_event.EventSwitchEnter)
    def add_switch(self, ev):
        new_switch = ev.switch.dp.id
        if new_switch not in self.net:
            self.net.add_node(new_switch)
            nx.draw(self.net, with_labels=True)
            plt.savefig("grafo.png")
            plt.clf()
            print "Ho aggiunto il nodo ", new_switch
            print "Ora i nodi sono ", self.net.nodes()

    @set_ev_cls(topo_event.EventSwitchLeave)
    def remove_switch(self, ev):
        old_switch = ev.switch.dp.id
        if old_switch in self.net:
            self.net.remove_node(old_switch)
            nx.draw(self.net, with_labels=True)
            plt.savefig("grafo.png")
            plt.clf()
            print "Ho rimosso il nodo ", old_switch
            print "Ora i nodi sono ", self.net.nodes()

    @set_ev_cls(topo_event.EventLinkDelete)
    def remove_link(self, ev):
        old_link = ev.link
        link = (old_link.src.dpid, old_link.dst.dpid)
        mirror = (old_link.dst.dpid, old_link.src.dpid)
        if link in self.net.edges():
            self.net.remove_edge(*link)
            self.net.remove_edge(*mirror)
            nx.draw(self.net, with_labels=True)
            plt.savefig("grafo.png")
            plt.clf()
            print "Ho rimosso il collegamento ", link
            print "e anche ", mirror
            print "Ora i collegamenti sono: ", self.net.edges()

    @set_ev_cls(topo_event.EventLinkAdd)
    def add_link(self, ev):
        new_link = ev.link
        link = (new_link.src.dpid, new_link.dst.dpid)
        if link not in self.net:
            self.net.add_edge(new_link.src.dpid, new_link.dst.dpid,
                              port=new_link.src.port_no)
            nx.draw(self.net, with_labels=True)
            plt.savefig("grafo.png")
            plt.clf()
            print "Ho aggiunto il collegamento ", link
            print "Ora i collegamenti sono: ", self.net.edges()
