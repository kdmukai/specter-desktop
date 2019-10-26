import json
import os
import random
import subprocess
import sys

from flask import Flask, Blueprint, render_template, request, redirect, jsonify, current_app
from helpers import normalize_xpubs
from hwilib import commands as hwilib_commands
from hwilib import base58

rand = random.randint(0, 1e32) # to force style refresh


hwi_views = Blueprint('hwi', __name__, template_folder='templates')


"""
    Support for calling the 'hwi' CLI. See note below in _enumerate()
"""
HWI_DIR = None
def _locate_hwi():
    # Is hwi globally available?
    returned_output = subprocess.check_output(["which", "hwi"])
    if not returned_output:
        # Are we in a virtualenv?
        virtualenv_bin_dir = sys.executable[:sys.executable.rfind(os.sep)]
        returned_output = subprocess.check_output(["hwi", "--version"], cwd=virtualenv_bin_dir)
        if "hwi" not in returned_output.decode("utf-8").lower():
            print("Could not find 'hwi' executable for HWI hardware wallet support")
            exit(0)
        else:
            HWI_DIR = virtualenv_bin_dir

_locate_hwi()



def get_spector_instance():
    # specter instance is injected into app in server.py's __main__()
    return current_app.specter


def get_hwi_client(type, path):
    is_test = 'test' in get_spector_instance().chain
    client = hwilib_commands.get_client(type, path)
    client.is_testnet = is_test
    return client


def _enumerate():
    try:
        # Have to call out to the installed 'hwi' CLI rather than directly calling
        #   hwilib.command.enumerate. The direct enumerate call crashes Flask when
        #   no devices are connected. Could not reproduce this in the python shell
        #   nor did the try/except rescue the thread.
        #
        # Restore this line try directly calling enumerate:
        #   wallets = hwilib_commands.enumerate()
        #
        # The subprocess call does not run in the current virtualenv so we need to
        #   locate the 'hwi' executable.
        returned_output = subprocess.check_output(["hwi", "enumerate"], cwd=HWI_DIR)
        return json.loads(returned_output.decode("utf-8"))

    except Exception as e:
        print(e)
        return None


@hwi_views.route('/extract_xpubs/', methods=['POST'])
def hwi_extract_xpubs():
    specter = get_spector_instance()

    device_name = request.form['device_name']
    if device_name in specter.devices.names():
        return jsonify(success=False, error="Device with this name already exists")
    
    type = request.form.get("type")
    path = request.form.get("path")

    try:
        client = get_hwi_client(type, path)
        client.is_testnet = False
        xpubs = ""

        # Extract nested Segwit
        master_xpub = client.get_pubkey_at_path('m/49h/0h/0h')['xpub']
        master_fpr = hwilib_commands.get_xpub_fingerprint_hex(master_xpub)
        xpubs += "[%s/49'/0'/0']%s\n" % (master_fpr, master_xpub)

        # native Segwit
        master_xpub = client.get_pubkey_at_path('m/84h/0h/0h')['xpub']
        master_fpr = hwilib_commands.get_xpub_fingerprint_hex(master_xpub)
        xpubs += "[%s/84'/0'/0']%s\n" % (master_fpr, master_xpub)

        # Multisig nested Segwit
        master_xpub = client.get_pubkey_at_path('m/48h/0h/0h/1h')['xpub']
        master_fpr = hwilib_commands.get_xpub_fingerprint_hex(master_xpub)
        xpubs += "[%s/48'/0'/0'/1']%s\n" % (master_fpr, master_xpub)

        # Multisig native Segwit
        master_xpub = client.get_pubkey_at_path('m/48h/0h/0h/2h')['xpub']
        master_fpr = hwilib_commands.get_xpub_fingerprint_hex(master_xpub)
        xpubs += "[%s/48'/0'/0'/2']%s\n" % (master_fpr, master_xpub)

        # And testnet
        client.is_testnet = True
        master_xpub = client.get_pubkey_at_path('m/49h/1h/0h')['xpub']
        master_xpub = base58.xpub_main_2_test(master_xpub)
        master_fpr = hwilib_commands.get_xpub_fingerprint_hex(master_xpub)
        xpubs += "[%s/49'/1'/0']%s\n" % (master_fpr, master_xpub)

        master_xpub = client.get_pubkey_at_path('m/84h/1h/0h')['xpub']
        master_xpub = base58.xpub_main_2_test(master_xpub)
        master_fpr = hwilib_commands.get_xpub_fingerprint_hex(master_xpub)
        xpubs += "[%s/84'/1'/0']%s\n" % (master_fpr, master_xpub)

        master_xpub = client.get_pubkey_at_path('m/48h/1h/0h/1h')['xpub']
        master_xpub = base58.xpub_main_2_test(master_xpub)
        master_fpr = hwilib_commands.get_xpub_fingerprint_hex(master_xpub)
        xpubs += "[%s/48'/1'/0'/1']%s\n" % (master_fpr, master_xpub)

        master_xpub = client.get_pubkey_at_path('m/48h/1h/0h/2h')['xpub']
        master_xpub = base58.xpub_main_2_test(master_xpub)
        master_fpr = hwilib_commands.get_xpub_fingerprint_hex(master_xpub)
        xpubs += "[%s/48'/1'/0'/2']%s\n" % (master_fpr, master_xpub)
    except Exception as e:
        print(e)
        return jsonify(success=False, error=e)

    normalized, parsed, failed = normalize_xpubs(xpubs)
    if len(failed) > 0:
        return jsonify(success=False, error="Failed to parse these xpubs:\n" + "\n".join(failed))

    print(normalized)
    device = specter.devices.add(name=device_name, device_type=type, keys=normalized)
    return jsonify(success=True, device_alias=device["alias"])


@hwi_views.route('/new_device/', methods=['GET'])
def hwi_new_device_xpubs():
    err = None
    specter = get_spector_instance()
    specter.check()

    return render_template(
        "hwi_new_device_xpubs.html",
        error=err,
        specter=specter,
        rand=rand
    )


@hwi_views.route('/enumerate/', methods=['GET'])
def hwi_enumerate():
    try:
        wallets = _enumerate()
        if wallets:
            print(wallets)
    except Exception as e:
        print(e)
        wallets = None
    return jsonify(wallets)


@hwi_views.route('/detect/', methods=['POST'])
def detect():
    type = request.form.get("type")
    try:
        wallets = _enumerate()

        if wallets:
            print(wallets)
            for wallet in wallets:
                if wallet.get("type") == type:
                    if type == "ledger" and wallet.get("error"):
                        print(wallet.get("error"))
                        return jsonify(success=False)
                    else:
                        return jsonify(success=True, wallet=wallet)
            print("type %s not found" % type)
    except Exception as e:
        print(e)

    return jsonify(success=False)


@hwi_views.route('/prompt_pin/', methods=['POST'])
def hwi_prompt_pin():
    print(request.form)
    type = request.form.get("type")
    path = request.form.get("path")

    try:
        if type == "keepkey" or type == "trezor":
            # The KeepKey will randomize its pin entry matrix on the device
            #   but the corresponding digits in the receiving UI always map
            #   to:
            #       7 8 9
            #       4 5 6
            #       1 2 3
            client = get_hwi_client(type, path)
            status = hwilib_commands.prompt_pin(client)
            return jsonify(success=True, status=status)
        else:
            return jsonify(success=False, error="Invalid HWI device type %s" % type)
    except Exception as e:
        print(e)
        return jsonify(success=False, error=e)


@hwi_views.route('/send_pin/', methods=['POST'])
def hwi_send_pin():
    type = request.form.get("type")
    path = request.form.get("path")
    pin = request.form.get("pin")

    try:
        client = get_hwi_client(type, path)
        status = hwilib_commands.send_pin(client, pin)
        return jsonify(status)
    except Exception as e:
        print(e)
        return jsonify(success=False, error=e)


@hwi_views.route('/sign_tx/', methods=['POST'])
def hwi_sign_tx():
    type = request.form.get("type")
    path = request.form.get("path")
    psbt = request.form.get("psbt")

    try:
        client = get_hwi_client(type, path)
        status = hwilib_commands.signtx(client, psbt)
        print(status)
        return jsonify(status)
    except Exception as e:
        print(e)
        return jsonify(success=False, error=e)
