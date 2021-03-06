#!/usr/bin/env python
# Copyright (c) 2016 "Jonathan Yantis"
#
#    This program is free software: you can redistribute it and/or  modify
#    it under the terms of the GNU Affero General Public License, version 3,
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    As a special exception, the copyright holders give permission to link the
#    code of portions of this program with the OpenSSL library under certain
#    conditions as described in each individual source file and distribute
#    linked combinations including the program with the OpenSSL library. You
#    must comply with the GNU Affero General Public License in all respects
#    for all of the code used other than as permitted herein. If you modify
#    file(s) with this exception, you may extend this exception to your
#    version of the file(s), but you are not obligated to do so. If you do not
#    wish to do so, delete this exception statement from your version. If you
#    delete this exception statement from all source files in the program,
#    then also delete it in the license file.
#
"""
NetGrph API Views
"""
import logging
import nglib
import nglib.query
import nglib.report
import nglib.netdb.switch
from nglib.exceptions import ResultError
from flask import jsonify, request
from apisrv import app, auth, config, errors

# Setup
logger = logging.getLogger(__name__)
app_name = config['apisrv']['app_name']

# Device Queries
@app.route('/netgrph/api/v1.1/devs', methods=['GET'])
@auth.login_required
def get_devs():
    """ Get Device Reports
    
        Notes: Truncates by default for speed
    """
    search = '.*'
    group = '.*'
    trunc = True

    if 'search' in request.args:
        search = request.args['search']
    if 'group' in request.args:
        group = request.args['group']
    if 'full' in request.args:
        trunc = False

    try:
        return jsonify(nglib.report.get_dev_report(dev=search, group=group, trunc=trunc))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.1/devs/<device>', methods=['GET'])
@auth.login_required
def get_device(device):
    """ Get specific device reports """

    try:
        return jsonify(nglib.query.dev.get_device(device, rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.1/devs/<device>/neighbors', methods=['GET'])
@auth.login_required
def get_device_neighbors(device):
    """ Get specific device neighbors """

    try:
        return jsonify(nglib.query.dev.get_neighbors(device))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.1/devs/<device>/vlans', methods=['GET'])
@auth.login_required
def get_device_vlans(device):
    """ Get specific device vlans """

    try:
        return jsonify(nglib.query.dev.get_vlans(device))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.1/devs/<device>/nets', methods=['GET'])
@auth.login_required
def get_device_nets(device):
    """ Get specific device networks """

    try:
        return jsonify(nglib.query.dev.get_networks(device))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.1/devs/<device>/ints', methods=['GET'])
@auth.login_required
def get_device_ints(device):
    """ Get specific device interfaces """

    if not nglib.netdb:
        return jsonify(errors.json_error('NetDB Error', \
            'NetDB Must be enabled to run this query'))

    try:
        return jsonify(nglib.netdb.switch.get_switch(device))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

# Path Queries
@app.route('/netgrph/api/<ver>/path', methods=['GET'])
@auth.login_required
def get_full_path(ver):
    """ L2-L4 Path Query, use onePath for single paths """
    onepath = False
    depth = '20'

    if 'onepath' in request.args:
        if request.args['onepath'] == "True":
            onepath = True
    if 'depth' in request.args:
        depth = request.args['depth']
    try:
        return jsonify(nglib.query.path.get_full_path(request.args['src'], \
            request.args['dst'], {"onepath": onepath, "depth": depth}))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/<ver>/rpath', methods=['GET'])
@auth.login_required
def get_routed_path(ver):
    """ Routed Paths, accepts vrf """
    onepath = False
    depth = '20'
    vrf = 'default'

    if 'onepath' in request.args:
        if request.args['onepath'] == "True":
            onepath = True
    if 'depth' in request.args:
        depth = request.args['depth']
    if 'vrf' in request.args:
        vrf = request.args['vrf']
    try:
        return jsonify(nglib.query.path.get_routed_path(request.args['src'], \
            request.args['dst'], {"onepath": onepath, "depth": depth, \
            "VRF": vrf}))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/<ver>/spath', methods=['GET'])
@auth.login_required
def get_switched_path(ver):
    """ Switched Path """
    onepath = False
    depth = '20'
    if 'onepath' in request.args:
        if request.args['onepath'] == "True":
            onepath = True
    if 'depth' in request.args:
        depth = request.args['depth']
    try:
        return jsonify(nglib.query.path.get_switched_path(request.args['src'], \
            request.args['dst'], {"onepath": onepath, "depth": depth}))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

# L3 Network Queries
@app.route('/netgrph/api/v1.1/nets', methods=['GET'])
@auth.login_required
def get_nets():
    """
    /nets API method

    Options:
        none   - return a list of all networks
        ip     - find the cidr for an IP
        cidr   - filter networks by CIDR
        filter - filter networks by NetGrph filter (vrf:[role])
    """


    cidr = None
    nFilter = 'all'

    if 'ip' in request.args:
        try:
            return jsonify(nglib.query.net.get_net(request.args['ip'], rtype="NGTREE"))
        except ResultError as e:
            return jsonify(errors.json_error(e.expression, e.message))
    elif 'cidr' in request.args:
        cidr = request.args['cidr']
        cidr = cidr.replace('-', '/')
        try:
            return jsonify(nglib.query.net.get_networks_on_cidr(cidr, rtype="NGTREE"))
        except ResultError as e:
            return jsonify(errors.json_error(e.expression, e.message))
        except ValueError as e:
            print(dir(e))
            return jsonify(errors.json_error('ValueError', str(e), code=400))
    else:
        if 'filter' in request.args:
            nFilter = request.args['filter']
        try:
            return jsonify(nglib.query.net.get_networks_on_filter(nFilter=nFilter, rtype="NGTREE"))
        except ResultError as e:
            return jsonify(errors.json_error(e.expression, e.message))

# L2 VLAN Queries
@app.route('/netgrph/api/<ver>/vlans', methods=['GET'])
@auth.login_required
def get_vlans(ver):
    allSwitches = True
    vrange = '1-4096'
    group = '.*'
    if 'allSwitches' in request.args and request.args['allSwitches'] == 'False':
        allSwitches = False
    if 'vrange' in request.args:
        vrange = request.args['vrange']
    if 'group' in request.args:
        group = request.args['group']

    try:
        return jsonify(nglib.report.get_vlan_report(vrange=vrange, group=group, \
                    rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))


@app.route('/netgrph/api/<ver>/vlans/<vlan>', methods=['GET'])
@auth.login_required
def get_vlan(vlan, ver):
    allSwitches = True

    if 'allSwitches' in request.args and request.args['allSwitches'] == 'False':
        allSwitches = False
    try:
        return jsonify(nglib.query.vlan.get_vlan(vlan, allSwitches=allSwitches, \
                    rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))


## v1.0 Methods ##
@app.route('/netgrph/api/v1.0/net', methods=['GET'])
@auth.login_required
def get_net():

    try:
        return jsonify(nglib.query.net.get_networks_on_cidr(request.args['cidr'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/ip', methods=['GET'])
@auth.login_required
def get_ip():

    try:
        return jsonify(nglib.query.net.get_net(request.args['ip'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/nlist', methods=['GET'])
@auth.login_required
def get_nlist():

    try:
        return jsonify(nglib.query.net.get_networks_on_filter(request.args['group'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/nfilter', methods=['GET'])
@auth.login_required
def get_nfilter():
    """ Networks on a filter """
    try:
        return jsonify(nglib.query.net.get_networks_on_filter(nFilter=request.args['filter'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/vid', methods=['GET'])
@auth.login_required
def get_vid():
    allSwitches = True
    if 'allSwitches' in request.args and request.args['allSwitches'] == 'False':
        allSwitches = False
    try:
        return jsonify(nglib.query.vlan.search_vlan_id(request.args['id'], \
                    rtype="NGTREE", allSwitches=allSwitches))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))


@app.route('/netgrph/api/v1.0/vtree', methods=['GET'])
@auth.login_required
def get_vtree():
    try:
        return jsonify(nglib.query.vlan.get_vtree(request.args['name'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))

@app.route('/netgrph/api/v1.0/dev', methods=['GET'])
@auth.login_required
def get_dev():
    try:
        return jsonify(nglib.query.dev.get_device(request.args['dev'], rtype="NGTREE"))
    except ResultError as e:
        return jsonify(errors.json_error(e.expression, e.message))


# Info method, Return Request Data back to client as JSON
@app.route('/' + app_name + '/api/<ver>/info', methods=['POST', 'GET'])
@auth.login_required
def app_getinfo(ver):
    """ Returns Flask API Info """
    response = dict()
    response['api_version'] = ver
    response['message'] = "Flask API Data"
    response['status'] = "200"
    response['method'] = request.method
    response['path'] = request.path
    response['remote_addr'] = request.remote_addr
    response['user_agent'] = request.headers.get('User-Agent')

    # GET attributes
    for key in request.args:
        response['GET ' + key] = request.args.get(key, '')
    # POST Attributes
    for key in request.form.keys():
        response['POST ' + key] = request.form[key]

    return jsonify(response)

@app.route('/')
def app_index():
    """Index identifying the server"""
    response = {"message": app_name + \
                " server: Authentication required for use",
                "status": "200"}
    return jsonify(response)
