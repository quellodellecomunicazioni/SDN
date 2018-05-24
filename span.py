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
from ryu.app import simple_switch_13
from ryu.topology import switches
from ryu.topology import event as topo_event
from ryu.topology.api import get_switch, get_link, get_host
import networkx as nx
import matplotlib.pyplot as plt
import support as sp

G = nx.Graph()

class SimpleSwitch13(simple_switch_13.SimpleSwitch13):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'stplib': stplib.Stp}

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.stp = kwargs['stplib']
		
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

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        #self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
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
		G.add_node(new_switch)
		switches = G.nodes()
		
		# prendo la lista completa dei links della rete
		links_list = get_link(self, None)
		links=[(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]

		# prendo la lista degli host
		host_list = get_host(self, None)

		# disegno il grafo
		#nx.draw(G)
		#plt.show()

		print "switches: ", switches
		print "hosts: ", host_list
		print "Links: ", links
		print "links del grafo: ", G.edges()

    @set_ev_cls(topo_event.EventSwitchLeave)
    def remove_switch(self, ev):
		old_switch = ev.switch.dp.id
		G.remove_node(old_switch)
		switches = G.nodes()
		
		# prendo la lista completa dei links della rete
		links_list = get_link(self, None)
		links=[(link.src.dpid,link.dst.dpid,{'port':link.src.port_no}) for link in links_list]

		# prendo la lista completa degli host della rete
		host_list = get_host(self, None)
		hosts = [host.mac for host in host_list]

		# disegno il grafo
		#nx.draw(G)
		#plt.show()

		print "switches: ", switches
		print "links: ", links
		print "hosts: ", hosts
		print "links grafo: ", G.edges()

    @set_ev_cls(topo_event.EventLinkAdd)
    def add_link(self, ev):
		new_link = ev.link
		test = (new_link.src.dpid, new_link.dst.dpid)
		mirror = (new_link.dst.dpid, new_link.src.dpid)
		if test not in G.edges():
			G.add_edge(*test)
			print "Ho aggiunto il collegamento: ", test
			print "I nuovi collegamenti sono: ", G.edges()

    @set_ev_cls(topo_event.EventLinkDelete)
    def remove_link(self, ev):
		old_link = ev.link
		test = (old_link.src.dpid, old_link.dst.dpid)
		mirror = (old_link.dst.dpid, old_link.src.dpid)
		if test in G.edges():
			G.remove_edge(*test)
			print "Ho rimosso il collegamento: ", test
			print "I nuovi collegamenti sono: ", G.edges()

    #@set_ev_cls(topo_event.EventHostAdd)
    #def nuovo_host(self, ev):
	#	new_host = ev.host.mac
	#	G.add_node(new_host)
	#	print G.nodes()
